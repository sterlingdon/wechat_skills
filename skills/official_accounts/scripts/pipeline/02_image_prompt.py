import re
from typing import List, Dict, Optional


BASE_VISUAL_RULES = (
    "严格使用信息图 infographic 风格，科技文章统一采用简洁现代、蓝灰冷色调、白底或浅色底、"
    "清晰中文标题与标签、结构化排版、模块边界明确、留白充足。"
    "禁止写实人物写真、禁止电影感场景、禁止抽象氛围图、禁止装饰性插画、禁止杂乱背景、"
    "禁止大段难以辨认的小字、禁止多余视觉元素。"
)


TYPE_RULES = {
    "flow": "将核心内容画成流程图，突出步骤顺序、输入输出、箭头关系和关键节点。",
    "architecture": "将核心内容画成架构图或分层图，突出模块、层次和组件关系。",
    "comparison": "将核心内容画成对比图，左右分栏或卡片式比较，突出差异和优先级。",
    "data": "将核心内容画成数据图或指标卡，突出数字、趋势和结论，避免花哨装饰。",
    "concept": "将核心内容画成概念图，中心主题明确，周围是少量关键要点和标签。",
}


def _detect_language(md_content: str) -> str:
    cjk_count = len(re.findall(r"[\u4e00-\u9fff]", md_content))
    return "zh" if cjk_count >= 20 else "en"


def _find_previous_heading(md_content: str, match_start: int) -> Optional[str]:
    prefix = md_content[:match_start]
    headings = re.findall(r"^#{2,3}\s+(.+)$", prefix, flags=re.MULTILINE)
    if not headings:
        return None
    return headings[-1].strip()


def _infer_prompt_type(original_desc: str, section_title: Optional[str]) -> str:
    text = f"{section_title or ''} {original_desc}"
    if re.search(r"流程|步骤|工作流|链路|顺序|阶段", text):
        return "flow"
    if re.search(r"架构|分层|模块|系统|同步|接口|结构", text):
        return "architecture"
    if re.search(r"对比|区别|优缺点|前后|A/B|vs", text, flags=re.IGNORECASE):
        return "comparison"
    if re.search(r"数据|趋势|统计|增长|比例|指标", text):
        return "data"
    return "concept"


def _build_prompt(
    original_desc: str,
    global_style: str,
    section_title: Optional[str],
    prompt_type: str,
    language: str,
) -> str:
    label_rule = "图片中的所有文字必须使用中文" if language == "zh" else "All labels must be in English"
    context = f"本图服务的段落标题是《{section_title}》。" if section_title else ""
    type_rule = TYPE_RULES.get(prompt_type, TYPE_RULES["concept"])

    return (
        f"{context}"
        f"主题描述：{original_desc}。"
        f"{type_rule}"
        f"{BASE_VISUAL_RULES}"
        f"{label_rule}。"
        f"全局视觉风格要求：{global_style}。"
        "画面必须具体表达文章里的核心信息，而不是泛泛地画一个科技感场景。"
        "优先展示结构、关系、步骤和信息层次；避免人物表演感和无关背景。"
    )


def extract_image_prompts(
    md_content: str, global_style: str = "科技信息图风格，蓝灰冷色调，简洁现代"
) -> List[Dict[str, str]]:
    print(f"🔍 [模块 2] 开始解析配图占位符，应用统一风格：{global_style[:30]}...")

    pattern = re.compile(r"<!--\s*image:\s*(.*?)\s*-->")
    language = _detect_language(md_content)
    tasks = []

    for match in pattern.finditer(md_content):
        original_desc = match.group(1).strip()
        section_title = _find_previous_heading(md_content, match.start())
        prompt_type = _infer_prompt_type(original_desc, section_title)
        final_prompt = _build_prompt(
            original_desc=original_desc,
            global_style=global_style,
            section_title=section_title,
            prompt_type=prompt_type,
            language=language,
        )
        tasks.append(
            {
                "placeholder": match.group(0),
                "original_desc": original_desc,
                "section_title": section_title or "",
                "prompt_type": prompt_type,
                "final_prompt": final_prompt,
            }
        )

    print(f"✅ [模块 2] 找到 {len(tasks)} 处需要配图的地方。")
    return tasks

if __name__ == "__main__":
    md = "这是一段文字。<!-- image: 一个努力奔跑的青年 --> 这是另一段文字。"
    res = extract_image_prompts(md)
    print(res)
