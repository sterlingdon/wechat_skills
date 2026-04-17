import os
import sys
import argparse
import re

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow is not installed. Run: pip install Pillow")
    sys.exit(1)

skill_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
workspace_root = os.path.dirname(os.path.dirname(skill_root))
content_root = os.path.join(workspace_root, "content_hub")
sys.path.append(skill_root)

import importlib

analyze_article = importlib.import_module(
    "scripts.pipeline.01_article_analyze"
).analyze_article
extract_image_prompts = importlib.import_module(
    "scripts.pipeline.02_image_prompt"
).extract_image_prompts
ImageDrawEngine = importlib.import_module(
    "scripts.pipeline.03_image_draw"
).ImageDrawEngine


def resize_and_crop(image_path, target_width, target_height):
    try:
        with Image.open(image_path) as img:
            img_ratio = img.width / img.height
            target_ratio = target_width / target_height

            if img_ratio > target_ratio:
                new_height = target_height
                new_width = int(new_height * img_ratio)
            else:
                new_width = target_width
                new_height = int(new_width / img_ratio)

            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            left = (new_width - target_width) / 2
            top = (new_height - target_height) / 2
            right = (new_width + target_width) / 2
            bottom = (new_height + target_height) / 2

            img = img.crop((left, top, right, bottom))
            img.save(image_path)
            print(f"✂️ 已裁剪图片至 {target_width}x{target_height}: {image_path}")
    except Exception as e:
        print(f"⚠️ 裁剪图片失败 ({image_path}): {e}")


def extract_date_from_path(file_path):
    """从路径中提取日期 YYYY-MM-DD"""
    match = re.search(r"/(\d{4}-\d{2}-\d{2})/", file_path)
    if match:
        return match.group(1)
    return None


def extract_article_name_from_path(file_path):
    """从路径中提取文章名称（取日期目录后的下一级目录名）"""
    # 路径格式: .../YYYY-MM-DD/{article-name}/{article-name}.md
    match = re.search(r"/(\d{4}-\d{2}-\d{2})/([^/]+)/", file_path)
    if match:
        return match.group(2)
    # 兼容旧格式：直接从文件名提取
    return os.path.basename(file_path).replace(".md", "")


def main():
    parser = argparse.ArgumentParser(
        description="Generate images for WeChat Official Account Markdown articles."
    )
    parser.add_argument("markdown_file", help="Path to the markdown file.")
    args = parser.parse_args()

    target_md = args.markdown_file
    date_dir = extract_date_from_path(target_md)

    if not date_dir:
        print(f"❌ 文件路径中未找到日期目录 (格式: YYYY-MM-DD): {target_md}")
        sys.exit(1)

    article_name = extract_article_name_from_path(target_md)

    # 新目录结构：03-review/YYYY-MM-DD/{article-name}/
    review_dir = os.path.join(
        content_root, "03-review", date_dir, article_name
    )
    image_dir = os.path.join(review_dir, "images")
    os.makedirs(image_dir, exist_ok=True)

    with open(target_md, "r", encoding="utf-8") as f:
        md_text = f.read()

    print("\n" + "=" * 40)
    print("▶️ 阶段 1：分析文章意境")
    print("=" * 40)

    article_style = analyze_article(md_text)
    visual_style = article_style.get("visual_style", "高质量插画")
    cover_suggestion = article_style.get("cover_suggestion", "")

    draw_engine = ImageDrawEngine(backend="gemini_nano_banana")
    new_md_text = md_text

    print("\n" + "=" * 40)
    print("▶️ 阶段 2：生成微信头条封面图")
    print("=" * 40)

    cover_prompt = f"{cover_suggestion}。{visual_style}"
    cover_filename = f"{article_name}_cover.png"
    cover_output_path = os.path.join(image_dir, cover_filename)

    try:
        draw_engine.draw(
            prompt=cover_prompt, output_path=cover_output_path, aspect_ratio="21:9"
        )
        resize_and_crop(cover_output_path, 900, 383)

        cover_prompt_path = os.path.join(image_dir, f"{article_name}_cover_prompt.txt")
        with open(cover_prompt_path, "w", encoding="utf-8") as f:
            f.write(cover_prompt)
        print(f"📝 已保存封面图 prompt 至 {cover_prompt_path}")

        new_md_text = (
            f"<!-- cover image -->\n![封面图](./images/{cover_filename})\n\n"
            + new_md_text
        )
    except Exception as e:
        print(f"❌ 封面图生成失败: {e}")

    print("\n" + "=" * 40)
    print("▶️ 阶段 3：处理正文配图占位符")
    print("=" * 40)

    image_tasks = extract_image_prompts(md_content=md_text, global_style=visual_style)

    if not image_tasks:
        print("ℹ️ 正文中未找到图片占位符。")
    else:
        for idx, task in enumerate(image_tasks):
            filename = f"{article_name}_{idx}.png"
            output_path = os.path.join(image_dir, filename)

            try:
                draw_engine.draw(
                    prompt=task["final_prompt"],
                    output_path=output_path,
                    aspect_ratio="16:9",
                )
                resize_and_crop(output_path, 1080, 608)

                # 保存正文配图的 prompt
                prompt_path = os.path.join(
                    image_dir, f"{article_name}_{idx}_prompt.txt"
                )
                with open(prompt_path, "w", encoding="utf-8") as f:
                    f.write(task["final_prompt"])
                print(f"📝 已保存正文配图 prompt 至 {prompt_path}")

                img_markdown = f"\n![{task['original_desc']}](./images/{filename})\n"
                new_md_text = new_md_text.replace(task["placeholder"], img_markdown)

            except Exception as e:
                print(f"❌ 生成正文图片异常，已跳过第 {idx} 张: {e}")

    review_path = os.path.join(review_dir, os.path.basename(target_md))
    print(f"\n💾 所有配图处理完成，正在保存至 {review_path}")

    with open(review_path, "w", encoding="utf-8") as f:
        f.write(new_md_text)


if __name__ == "__main__":
    main()
