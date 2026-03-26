import os
import re
import json
from datetime import datetime
from typing import Dict
import markdown
import requests
from premailer import transform
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.environ.get("WECHAT_APP_ID")
APP_SECRET = os.environ.get("WECHAT_APP_SECRET")

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def extract_title(md_content: str) -> str:
    match = re.search(r"^#\s+(.+)$", md_content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return "未命名文章"


def get_access_token() -> str:
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
    response = requests.get(url).json()
    if "access_token" in response:
        return response["access_token"]
    raise Exception(f"Failed to get access token: {response}")


def upload_image_to_wechat(access_token: str, image_path: str) -> str:
    url = (
        f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={access_token}"
    )
    with open(image_path, "rb") as f:
        files = {"media": f}
        response = requests.post(url, files=files).json()
        if "url" in response:
            return response["url"]
        raise Exception(f"Failed to upload image {image_path}: {response}")


def upload_thumb_material(access_token: str, image_path: str) -> str:
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    with open(image_path, "rb") as f:
        files = {"media": f}
        response = requests.post(url, files=files).json()
        if "media_id" in response:
            return response["media_id"]
        raise Exception(f"Failed to upload thumb material {image_path}: {response}")


def process_markdown_images(
    md_content: str, access_token: str, base_dir: str
) -> tuple[str, str, Dict[str, str]]:
    img_pattern = re.compile(r"!\[.*?\]\((.*?)\)")
    local_images = img_pattern.findall(md_content)

    first_thumb_media_id = None
    image_map = {}

    for img_path in set(local_images):
        if img_path.startswith("http://") or img_path.startswith("https://"):
            continue

        full_img_path = (
            os.path.join(base_dir, img_path)
            if not os.path.isabs(img_path)
            else img_path
        )

        if not os.path.exists(full_img_path):
            print(f"⚠️ Warning: Image not found locally: {full_img_path}")
            continue

        print(f"Uploading image: {full_img_path}")
        wechat_url = upload_image_to_wechat(access_token, full_img_path)

        md_content = md_content.replace(img_path, wechat_url)
        image_map[img_path] = wechat_url

        if not first_thumb_media_id:
            first_thumb_media_id = upload_thumb_material(access_token, full_img_path)

    return md_content, first_thumb_media_id, image_map


def convert_md_to_wechat_html(
    md_content: str, style_name: str = "wechat-default"
) -> str:
    css_path = os.path.join(
        project_root, "assets", "templates", "styles", f"{style_name}.css"
    )

    if not os.path.exists(css_path):
        css_path = os.path.join(
            project_root, "assets", "templates", "styles", "wechat-default.css"
        )

    html_body = markdown.markdown(md_content, extensions=["tables", "fenced_code"])

    with open(css_path, "r", encoding="utf-8") as f:
        css_content = f.read()

    full_html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>{css_content}</style>
    </head>
    <body><div class="wechat-content">{html_body}</div></body>
    </html>
    """

    inline_html = transform(full_html)
    return inline_html


def push_to_wechat_draft(
    access_token: str, title: str, digest: str, html_content: str, thumb_media_id: str
) -> str:
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"

    payload = {
        "articles": [
            {
                "title": title,
                "author": "",
                "digest": digest,
                "content": html_content,
                "content_source_url": "",
                "thumb_media_id": thumb_media_id,
                "need_open_comment": 1,
                "only_fans_can_comment": 0,
            }
        ]
    }

    response = requests.post(
        url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8")
    ).json()

    if "media_id" in response:
        print(f"✅ Success! Draft media_id: {response['media_id']}")
        return response["media_id"]
    else:
        raise Exception(f"Failed to add draft: {response}")


def save_sync_record(record: dict, base_dir: str):
    record_file = os.path.join(base_dir, "sync_record.json")
    records = []

    if os.path.exists(record_file):
        with open(record_file, "r", encoding="utf-8") as f:
            records = json.load(f)

    records.insert(0, record)

    with open(record_file, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"💾 同步记录已保存: {record_file}")


if __name__ == "__main__":
    import sys
    import importlib

    sys.path.insert(0, project_root)

    analyze_article = importlib.import_module(
        "scripts.pipeline.01_article_analyze"
    ).analyze_article

    if len(sys.argv) < 2:
        print("Usage: python scripts/sync_wechat.py <path_to_markdown_file>")
        sys.exit(1)

    target_md = sys.argv[1]
    base_dir = os.path.dirname(os.path.abspath(target_md))

    print(f"🚀 Starting to process: {target_md}")

    if not APP_ID or not APP_SECRET:
        print("❌ Error: WECHAT_APP_ID or WECHAT_APP_SECRET not found in .env")
        sys.exit(1)

    with open(target_md, "r", encoding="utf-8") as f:
        md_text = f.read()

    try:
        title = extract_title(md_text)
        print(f"📄 文章标题: {title}")

        article_style = analyze_article(md_text)
        style_name = article_style.get("style_name", "wechat-default")
        digest = article_style.get("digest", "")
        print(f"🎨 使用样式: {style_name}")
        print(f"📝 摘要: {digest}")

        token = get_access_token()

        new_md, thumb_id, image_map = process_markdown_images(md_text, token, base_dir)
        if not thumb_id:
            print(
                "⚠️ Warning: No local images found. A thumb_media_id is strictly required."
            )
            sys.exit(1)

        final_html = convert_md_to_wechat_html(new_md, style_name)

        media_id = push_to_wechat_draft(token, title, digest, final_html, thumb_id)

        record = {
            "media_id": media_id,
            "thumb_media_id": thumb_id,
            "title": title,
            "digest": digest,
            "style_name": style_name,
            "images": image_map,
            "source_file": target_md,
            "synced_at": datetime.now().isoformat(),
        }
        save_sync_record(record, base_dir)

    except Exception as e:
        print(f"❌ Error during sync: {str(e)}")
