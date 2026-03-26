import re
from typing import List, Dict

def extract_image_prompts(md_content: str, global_style: str = "高质量插画，色彩温暖") -> List[Dict[str, str]]:
    print(f"🔍 [模块 2] 开始解析配图占位符，应用统一风格：{global_style[:20]}...")
    
    pattern = re.compile(r'<!--\s*image:\s*(.*?)\s*-->')
    matches = pattern.finditer(md_content)
    
    tasks = []
    for match in matches:
        original_desc = match.group(1).strip()
        final_prompt = f"{original_desc}。{global_style}"
        tasks.append({
            "placeholder": match.group(0),
            "original_desc": original_desc,
            "final_prompt": final_prompt
        })
        
    print(f"✅ [模块 2] 找到 {len(tasks)} 处需要配图的地方。")
    return tasks

if __name__ == "__main__":
    md = "这是一段文字。<!-- image: 一个努力奔跑的青年 --> 这是另一段文字。"
    res = extract_image_prompts(md)
    print(res)
