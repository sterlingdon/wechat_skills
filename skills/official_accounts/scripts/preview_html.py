import os
import sys
import argparse
import importlib

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

render_markdown_to_wechat_html = importlib.import_module(
    "scripts.pipeline.04_html_render"
).render_markdown_to_wechat_html
analyze_article = importlib.import_module(
    "scripts.pipeline.01_article_analyze"
).analyze_article


def main():
    parser = argparse.ArgumentParser(
        description="Preview HTML before syncing to WeChat"
    )
    parser.add_argument("markdown_file", help="Path to the markdown file.")
    parser.add_argument(
        "--style", default=None, help="CSS style name (auto-detect if not specified)"
    )
    args = parser.parse_args()

    md_path = args.markdown_file
    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    if args.style:
        style_name = args.style
    else:
        print("\n" + "=" * 40)
        print("▶️ 自动分析文章意境，选择样式...")
        print("=" * 40)
        article_style = analyze_article(md_content)
        style_name = article_style.get("style_name", "wechat-default")

    html = render_markdown_to_wechat_html(md_content, style_name)

    html_path = md_path.replace(".md", "_preview.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n📄 HTML 预览已保存至: {html_path}")
    print(f"   使用样式: {style_name}")


if __name__ == "__main__":
    main()
