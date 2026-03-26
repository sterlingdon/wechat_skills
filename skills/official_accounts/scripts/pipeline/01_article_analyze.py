import os
import json
from dotenv import load_dotenv

load_dotenv()

MODEL = "gemini-2.5-flash"

STYLE_RULES = {
    "solemn": "深度分析、严肃话题、纪念文章、庄重内容",
    "tech": "技术、编程、代码、AI、开发者、教程",
    "warm": "温暖、治愈、生活、情感、亲情、友情",
    "elegant": "优雅、散文、随笔、文艺、诗意",
    "wechat-default": "通用、新闻、资讯、一般内容",
}


def analyze_article(md_content: str) -> dict:
    print("🔍 [模块 1] 开始分析文章意境...")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ [模块 1] GEMINI_API_KEY 缺失，使用默认风格。")
        return _default_result()

    try:
        from google import genai
    except ImportError:
        print("⚠️ [模块 1] google-genai 未安装，使用默认风格。")
        return _default_result()

    style_desc = "\n".join([f"- {k}: {v}" for k, v in STYLE_RULES.items()])

    prompt = f"""分析下面文章的情感意境，选择最合适的排版样式，并生成摘要和配图建议。

文章：
{md_content[:2000]}

可选样式：
{style_desc}

只返回 JSON：
{{
  "theme": "核心主题一句话",
  "mood": "情感基调",
  "color_palette": "色调描述",
  "article_type": "文章类型：概念解释/流程步骤/架构设计/对比分析/数据统计/叙事感悟",
  "visual_style": "风格后缀。科技文章必须用'infographic风格，简洁现代，冷色调蓝灰配色，清晰文字标签'；情感文章用'温暖色调，柔和氛围'；商业文章用'专业商务风格，深蓝配色'",
  "cover_suggestion": "封面图建议。科技文章必须是结构化信息图，如'infographic风格，[核心概念]可视化，中央图形+周围要点标注'，禁止场景描述；情感文章用场景描述",
  "digest": "文章摘要，50字左右，用于微信图文封面展示，要能吸引读者点击",
  "style_name": "样式名称，从上面的可选样式中选一个"
}}"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
        )

        text = response.candidates[0].content.parts[0].text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        result = json.loads(text)

        style_name = result.get("style_name", "wechat-default")
        if style_name not in STYLE_RULES:
            style_name = "wechat-default"
        result["style_name"] = style_name

        print(f"✅ [模块 1] 主题: {result.get('theme')}")
        print(f"   情感: {result.get('mood')}")
        print(f"   类型: {result.get('article_type', '未知')}")
        print(f"   样式: {style_name}")
        print(f"   摘要: {result.get('digest', '')}")
        return result

    except Exception as e:
        print(f"⚠️ [模块 1] 分析失败: {e}")
        return _default_result()


def _default_result() -> dict:
    return {
        "theme": "通用主题",
        "mood": "中性",
        "color_palette": "中性色调",
        "article_type": "叙事感悟",
        "visual_style": "高质量插画",
        "cover_suggestion": "根据文章内容生成封面",
        "digest": "精彩内容，敬请阅读",
        "style_name": "wechat-default",
    }


if __name__ == "__main__":
    test = "# 深入理解 React Hooks\n\nReact Hooks 让函数组件拥有了状态管理能力。核心概念包括 useState、useEffect、useContext。\n\n<!-- image: infographic 风格，React Hooks 核心概念图，中央是 Hooks 图标，周围标注三大核心 Hook 的作用 -->"
    print(analyze_article(test))
