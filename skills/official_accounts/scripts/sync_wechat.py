import os
import re
import json
from datetime import datetime
from typing import Dict
import requests
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.environ.get("WECHAT_APP_ID")
APP_SECRET = os.environ.get("WECHAT_APP_SECRET")

skill_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
workspace_root = os.path.dirname(os.path.dirname(skill_root))
content_root = os.path.join(workspace_root, "content_hub")


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


def load_preview_html(md_path: str) -> str:
    """Load the existing preview HTML file if it exists."""
    preview_path = md_path.replace(".md", "_preview.html")
    if os.path.exists(preview_path):
        with open(preview_path, "r", encoding="utf-8") as f:
            return f.read()
    return None


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


def archive_to_published(
    source_md: str, final_html: str, record: dict, article_date: str, article_name: str
):
    """
    Archive published materials to content_hub/04-published/YYYY-MM-DD/{article-name}/
    """
    published_dir = os.path.join(
        content_root, "04-published", article_date, article_name
    )
    os.makedirs(published_dir, exist_ok=True)

    # Get article base name
    base_name = os.path.splitext(os.path.basename(source_md))[0]

    # 1. Save final HTML sent to WeChat
    html_path = os.path.join(published_dir, f"{base_name}_final.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(final_html)
    print(f"📦 归档 HTML: {html_path}")

    # 2. Save sync record
    record_path = os.path.join(published_dir, "sync_record.json")
    with open(record_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    print(f"📦 归档记录: {record_path}")

    # 3. Copy original markdown
    md_path = os.path.join(published_dir, f"{base_name}.md")
    with open(source_md, "r", encoding="utf-8") as src:
        with open(md_path, "w", encoding="utf-8") as dst:
            dst.write(src.read())
    print(f"📦 归档原文: {md_path}")

    # 4. Copy images directory if exists
    source_dir = os.path.dirname(source_md)
    source_images = os.path.join(source_dir, "images")
    if os.path.exists(source_images):
        target_images = os.path.join(published_dir, "images")
        if not os.path.exists(target_images):
            import shutil

            shutil.copytree(source_images, target_images)
            print(f"📦 归档图片: {target_images}")

    print(f"✅ 物料已归档至: {published_dir}")


if __name__ == "__main__":
    import sys
    import importlib

    sys.path.insert(0, skill_root)

    analyze_article = importlib.import_module(
        "scripts.pipeline.01_article_analyze"
    ).analyze_article
    render_markdown_to_wechat_html = importlib.import_module(
        "scripts.pipeline.04_html_render"
    ).render_markdown_to_wechat_html

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

        # Try to use existing preview HTML, otherwise regenerate
        preview_html = load_preview_html(target_md)
        if preview_html:
            # Replace local image paths with WeChat URLs in existing HTML
            for local_path, wechat_url in image_map.items():
                preview_html = preview_html.replace(local_path, wechat_url)
            final_html = preview_html
            print("✅ 使用已生成的预览 HTML")
        else:
            final_html = render_markdown_to_wechat_html(new_md, style_name)
            print("⚠️ 未找到预览 HTML，重新生成")

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

        # Extract article name from path (directory name after date)
        date_match = re.search(r"/(\d{4}-\d{2}-\d{2})/", os.path.abspath(target_md))
        if not date_match:
            raise Exception(f"未能从路径中提取文章日期: {target_md}")
        article_date = date_match.group(1)
        article_name = os.path.basename(base_dir)
        archive_to_published(target_md, final_html, record, article_date, article_name)

    except Exception as e:
        print(f"❌ Error during sync: {str(e)}")
