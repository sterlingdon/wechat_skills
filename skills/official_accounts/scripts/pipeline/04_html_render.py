import os
import markdown
from premailer import transform


def render_markdown_to_wechat_html(
    md_content: str, style_name: str = "wechat-default"
) -> str:
    print(f"⚙️ [模块 4] 开始渲染 Markdown，使用排版主题：{style_name}...")

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
        <style>{css_content}</style>
    </head>
    <body>
        <div class="wechat-content" style="max-width: 100%; box-sizing: border-box;">
            {html_body}
        </div>
    </body>
    </html>
    """

    inline_html = transform(full_html)

    print("✅ [模块 4] 微信内联 HTML 渲染完成！")
    return inline_html
