import os
import re
import markdown
from premailer import transform


def _fix_list_spacing(md_content: str) -> str:
    """Fix list spacing: ensure blank line before list items.

    Python-markdown requires a blank line before a list to recognize it.
    This function adds missing blank lines before unordered (-, *, +) and
    ordered (1., 2., etc.) list items.
    """
    lines = md_content.split("\n")
    fixed_lines = []

    for i, line in enumerate(lines):
        # Check if current line is a list item
        is_list_item = re.match(r"^(\s*)([-*+]|\d+\.)\s", line)

        if is_list_item and i > 0:
            prev_line = lines[i - 1]
            # Check if previous line is not empty and not a list item
            prev_is_list = re.match(r"^(\s*)([-*+]|\d+\.)\s", prev_line)
            prev_is_empty = prev_line.strip() == ""

            if not prev_is_empty and not prev_is_list:
                # Add blank line before list
                fixed_lines.append("")

        fixed_lines.append(line)

    return "\n".join(fixed_lines)


def render_markdown_to_wechat_html(
    md_content: str, style_name: str = "wechat-default"
) -> str:
    print(f"⚙️ [模块 4] 开始渲染 Markdown，使用排版主题：{style_name}...")

    # Fix list spacing before conversion
    md_content = _fix_list_spacing(md_content)

    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    css_path = os.path.join(
        project_root, "assets", "templates", "styles", f"{style_name}.css"
    )

    if not os.path.exists(css_path):
        print(f"⚠️ [模块 4] 找不到主题 {style_name}.css，回退到默认样式")
        css_path = os.path.join(
            project_root, "assets", "templates", "styles", "wechat-default.css"
        )
        if not os.path.exists(css_path):
            raise FileNotFoundError(f"找不到任何 CSS 样式文件: {css_path}")

    html_body = markdown.markdown(md_content, extensions=["tables", "fenced_code"])

    with open(css_path, "r", encoding="utf-8") as f:
        css_content = f.read()

    full_html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
        body {{
            margin: 0;
            padding: 0;
        }}
        .wechat-content {{
            padding: 20px 16px;
            box-sizing: border-box;
        }}
        {css_content}
        </style>
    </head>
    <body>
        <div class="wechat-content" style="max-width: 100%;">
            {html_body}
        </div>
    </body>
    </html>
    """

    inline_html = transform(full_html)

    print("✅ [模块 4] 微信内联 HTML 渲染完成！")
    return inline_html
