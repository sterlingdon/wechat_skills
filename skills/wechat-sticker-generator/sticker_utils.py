import os
import sys
import json
import shutil
import base64
from datetime import datetime
from PIL import Image

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SKILL_DIR, "output")
CONFIG_FILE = os.path.expanduser("~/.sticker_generator_config.json")

# ============================================================
# 多 Provider 配置系统
# ============================================================

DEFAULT_CONFIG = {
    "default_provider": "gemini",
    "providers": {
        "gemini": {
            "api_key_env": "GEMINI_API_KEY",  # 从环境变量读取的 key 名
            "alt_env_keys": ["GOOGLE_API_KEY"],  # 备选环境变量名
            "model": "gemini-3.1-flash-image-preview",
            "description": "Google Gemini - 推荐，效果好速度快"
        },
        "qwen": {
            "api_key_env": "DASHSCOPE_API_KEY",
            "alt_env_keys": ["QWEN_API_KEY"],
            "model": "qwen-vl-max",
            "description": "阿里千问 - 国内访问稳定"
        }
        # 可以继续添加其他 provider...
    }
}

def load_config():
    """加载配置文件，不存在则返回默认配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 合并默认配置（确保新增的 provider 也能用）
                for key in DEFAULT_CONFIG:
                    if key not in config:
                        config[key] = DEFAULT_CONFIG[key]
                for provider, settings in DEFAULT_CONFIG["providers"].items():
                    if provider not in config["providers"]:
                        config["providers"][provider] = settings
                return config
        except:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """保存配置到文件"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"[✓] 配置已保存到: {CONFIG_FILE}")

def get_api_key(provider_name=None):
    """
    获取指定 provider 的 API Key

    优先级：
    1. 配置文件中的 api_key 字段
    2. 主环境变量（api_key_env）
    3. 备选环境变量（alt_env_keys）
    """
    config = load_config()
    provider = provider_name or config.get("default_provider", "gemini")
    provider_config = config["providers"].get(provider)

    if not provider_config:
        print(f"[!] 未知的 provider: {provider}", file=sys.stderr)
        print(f"[*] 可用的 providers: {list(config['providers'].keys())}", file=sys.stderr)
        return None, provider

    # 1. 检查配置文件中的 api_key
    if provider_config.get("api_key"):
        return provider_config["api_key"], provider

    # 2. 检查主环境变量
    main_env = provider_config.get("api_key_env", f"{provider.upper()}_API_KEY")
    api_key = os.environ.get(main_env)
    if api_key:
        return api_key, provider

    # 3. 检查备选环境变量
    for alt_env in provider_config.get("alt_env_keys", []):
        api_key = os.environ.get(alt_env)
        if api_key:
            return api_key, provider

    # 没有 key，给出提示
    print("\n" + "="*60, file=sys.stderr)
    print(f"❌ 缺少 {provider.upper()} API Key", file=sys.stderr)
    print("="*60, file=sys.stderr)

    if provider == "gemini":
        print("\n获取 Gemini API Key:", file=sys.stderr)
        print("  1. 访问: https://aistudio.google.com/app/apikey", file=sys.stderr)
        print("  2. 登录 Google 账号并创建 API Key", file=sys.stderr)
    elif provider == "qwen":
        print("\n获取千问 API Key:", file=sys.stderr)
        print("  1. 访问: https://dashscope.console.aliyun.com/", file=sys.stderr)
        print("  2. 开通服务并获取 API Key", file=sys.stderr)

    print(f"\n配置方式（三选一）：", file=sys.stderr)
    print(f"  方式A - 环境变量：", file=sys.stderr)
    print(f'    export {main_env}="你的API_Key"', file=sys.stderr)
    print(f"\n  方式B - 配置文件（交互式）：", file=sys.stderr)
    print(f'    python sticker_utils.py config set {provider}', file=sys.stderr)
    print(f"\n  方式C - 切换到其他 provider：", file=sys.stderr)
    print(f'    python sticker_utils.py config default qwen', file=sys.stderr)
    print("\n" + "="*60 + "\n", file=sys.stderr)

    return None, provider

def show_config():
    """显示当前配置"""
    config = load_config()
    print("\n" + "="*60)
    print("📋 Sticker Generator 配置")
    print("="*60)
    print(f"\n默认 Provider: {config.get('default_provider', 'gemini')}")
    print(f"配置文件: {CONFIG_FILE}")
    print("\n可用的 Providers:")
    for name, settings in config["providers"].items():
        has_key = "✅" if settings.get("api_key") or os.environ.get(settings.get("api_key_env", "")) else "❌"
        print(f"  {has_key} {name}: {settings.get('description', '')}")
    print("\n" + "="*60)

def config_command(args):
    """处理 config 子命令"""
    if not args:
        show_config()
        return

    cmd = args[0]
    config = load_config()

    if cmd == "set" and len(args) >= 2:
        # 设置 API Key: config set gemini xxx
        provider = args[1]
        if provider not in config["providers"]:
            print(f"[!] 未知的 provider: {provider}")
            print(f"[*] 可用的: {list(config['providers'].keys())}")
            return

        if len(args) >= 3:
            api_key = args[2]
        else:
            # 交互式输入
            import getpass
            api_key = getpass.getpass(f"请输入 {provider} API Key: ")

        config["providers"][provider]["api_key"] = api_key
        save_config(config)

    elif cmd == "default" and len(args) >= 2:
        # 设置默认 provider: config default qwen
        provider = args[1]
        if provider not in config["providers"]:
            print(f"[!] 未知的 provider: {provider}")
            return
        config["default_provider"] = provider
        save_config(config)
        print(f"[✓] 默认 provider 已设置为: {provider}")

    elif cmd == "list":
        show_config()

    else:
        print("用法:")
        print("  config              - 显示当前配置")
        print("  config list         - 显示当前配置")
        print("  config set <provider> [key]  - 设置 API Key")
        print("  config default <provider>    - 设置默认 provider")


# 风格预设映射
STYLE_MAPPING = {
    "2D_KAWAII": "2D flat style, cute anime style, clean lines, flat vector illustration, pastel colors.",
    "2D_ANIME_COOL": "2D anime style, sharp lines, cool and dynamic, vibrant colors, shonen manga aesthetic.",
    "3D_CLAY": "3D clay rendering, soft studio lighting, cute and plump, C4D, octane render, toy-like.",
    "3D_PIXAR": "3D Pixar-style animation, Disney quality, expressive, soft lighting, smooth rendering.",
    "PIXEL_ART": "16-bit pixel art, neat pixels, retro video game style, flat colors, nostalgic.",
    "CHINESE_INK": "Chinese ink wash painting style, traditional oriental aesthetic, elegant brush strokes, minimal colors.",
    "WATERCOLOR": "Soft watercolor painting, children's book illustration, gentle strokes, dreamy.",
    "LINE_ART": "Minimalist black and white line art, simple childish doodle, clean scribbles.",
    "CARTOON_WEST": "Western cartoon style, exaggerated proportions, bold outlines, expressive, American animation.",
    "CHIBI_SD": "Super deformed chibi style, big head small body, kawaii, adorable proportions.",
    "MEME_STYLE": "Internet meme sticker style, exaggerated expressions, funny, viral, bold and wacky.",
    "CUSTOM": "",  # 用户自定义
}

# 场景主题映射
SCENE_MAPPING = {
    "DAILY_LIFE": "daily life slice-of-life scene",
    "WORKPLACE": "office workplace setting, relatable work situations",
    "ROMANCE": "romantic sweet loving atmosphere",
    "FESTIVAL": "celebration festive holiday mood",
    "EMOTIONAL": "emotional expressive dramatic mood",
    "GAMING": "gaming esports competitive vibe",
    "STUDY": "student study academic setting",
}

# 角色类型提示
CHARACTER_TYPE_HINTS = {
    "HUMAN_CHIBI": "chibi style human character, big head, cute proportions",
    "HUMAN_ANIME": "anime style human character, detailed features",
    "ANIMAL_CUTE": "cute animal character, anthropomorphic traits",
    "ANIMAL_ANTHRO": "anthropomorphic animal character, human-like posture",
    "FANTASY": "fantasy creature, magical being, mythical",
    "OBJECT_PERSONIFIED": "personified object character, living item with face",
    "IP_CHARACTER": "recognizable popular character, faithful to original design",
}

# 配色氛围映射
COLOR_MOOD_MAPPING = {
    "BRIGHT_VIBRANT": "bright vibrant saturated colors, cheerful palette",
    "SOFT_PASTEL": "soft pastel colors, gentle macaron palette, dreamy",
    "WARM_COZY": "warm cozy colors, orange and yellow tones, comfortable",
    "COOL_CALM": "cool calm colors, blue and teal tones, serene",
    "MONOCHROME": "monochrome black and white, grayscale",
    "NEON_CYBER": "neon cyber colors, glowing fluorescent, futuristic",
    "VINTAGE_RETRO": "vintage retro colors, faded nostalgic palette",
}

# 背景类型映射
BACKGROUND_TYPE_MAPPING = {
    "white": "STRICTLY SOLID HIGHEST-PURITY WHITE BACKGROUND (#FFFFFF). Ensure 100% pure flat white with NO noise, NO grain, NO ground shadows, and NO lighting artifacts. The background MUST be perfectly clean uniform hex #FFFFFF across the entire image.",
    "transparent": "STRICTLY SOLID FLAT WHITE BACKGROUND (#FFFFFF) for later chroma-keying. Do NOT generate checkerboard patterns or alpha transparency. Instead, use a completely uniform, flat, and spotless pure white background with absolutely zero noise, zero gradients, and zero drop shadows. This is critical for clean masking.",
}

# 负面提示词 - 用于避免污染 GIF 输出
NEGATIVE_PROMPT = "checkerboard background, transparent background artifacts, noise, film grain, dirty background, dust, shadows on ground, drop shadow, lighting artifacts, borders, frames, grid lines, cell dividers, white borders, black borders, colored borders, padding around character, vignette, shadow effects, glow effects, gradient background, patterned background, scenery, background objects, text watermarks, logos, signatures, low quality, blurry, distorted, deformed, extra limbs, missing limbs, cropped character, character touching grid edges, overlapping cells"


def build_static_prompt(character, style_desc, expressions, reference_image="", background_type="white"):
    background_desc = BACKGROUND_TYPE_MAPPING.get(background_type, BACKGROUND_TYPE_MAPPING["white"])
    prompt_lines = [
        "A character sticker sheet featuring exactly 9 different expressions arranged in a 3x3 layout on a single seamless canvas. Do NOT draw any grid lines.",
        f"Character: {character}",
        f"Art Style: {style_desc}",
        "",
        "=== CRITICAL LAYOUT REQUIREMENTS ===",
        "1. CANVAS: Perfect square (1:1 aspect ratio), logically divided into 3x3=9 equal areas, but visually completely seamless.",
        "2. SCENE ALIGNMENT: Each area is a separate camera view. The character should be naturally framed within its area. Do NOT rigidly force the character to the exact mathematical center if the pose (e.g., sitting vs standing) dictates otherwise. Keep a consistent baseline floor.",
        "3. SIZE: Character (including all limbs, hair, accessories) must stay within 70% of each area, leaving at least 15% safe margin on ALL FOUR sides to prevent cutting off during slicing.",
        "4. NO OVERLAP: Absolutely no character parts, hair, limbs, shadows, or text may cross into adjacent areas. Each area is completely independent.",
        "5. ABSOLUTELY NO BORDERS: No visible borders, frames, grid lines, dividers, or dividing boxes between characters. The characters must float on a single, uninterrupted, perfectly clean background.",
        "",
        f"Background: {background_desc}",
    ]
    if reference_image:
        prompt_lines.append(f"Character Reference: Use the provided reference image to maintain identical facial features, hairstyle, and outfit across all 9 frames.")

    prompt_lines.append("")
    prompt_lines.append("=== EXPRESSIONS (3 rows × 3 columns, each centered in its cell) ===")
    for i, exp in enumerate(expressions):
        if i >= 9: break
        t = exp.get('text', '')
        if not t.strip(): t = "WOW!"
        prompt_lines.append(f"Cell {i+1}: Action: {exp.get('action', '')}. Text overlay: \"{t}\" - large, bold, readable, positioned so it does not hide the face.")

    prompt_lines.append("")
    prompt_lines.append("=== NEGATIVE CONSTRAINTS (STRICTLY AVOID) ===")
    prompt_lines.append(NEGATIVE_PROMPT)

    return "\n".join(prompt_lines)


def build_animated_prompt(character, style_desc, action, text_overlay, reference_image="", background_type="white"):
    background_desc = BACKGROUND_TYPE_MAPPING.get(background_type, BACKGROUND_TYPE_MAPPING["white"])
    if not text_overlay or not str(text_overlay).strip():
        text_overlay = f"{str(action).split()[0].upper()}!"

    prompt_lines = [
        "A 9-frame animation sprite sheet arranged in 3 rows and 3 columns on a single seamless canvas. Do NOT draw any grid lines.",
        f"Character: {character}",
        f"Art Style: {style_desc}",
        f"Animation: A smooth 9-frame sequence of '{action}'.",
        "",
        "=== CRITICAL LAYOUT REQUIREMENTS ===",
        "1. CANVAS: Perfect square (1:1 aspect ratio), logically divided into exactly 3x3=9 equal areas, but visually completely seamless.",
        "2. ANIMATION SPACE: Treat each area as a consistent fixed camera framing a fixed ground plane. The character must move NATURALLY within this space.",
        "3. NATURAL VERTICAL MOVEMENT: Crucially, if the action involves jumping, flying, or raising up, the character's body MUST be drawn physically higher within that specific frame's area compared to a standing frame. Do NOT artificially lock the character's center of mass to the center of every frame, otherwise the animation will not show vertical displacement.",
        "4. SIZE LIMIT: Character (including all limbs, hair, accessories, and motion effects) must stay within 70% of each area. This means at least 15% empty background margin on ALL FOUR sides of every area.",
        "5. NO OVERLAP: No character parts, hair, limbs, shadows, text, or motion lines may cross the invisible boundary into adjacent areas.",
        "6. ABSOLUTELY NO BORDERS: No visible borders, frames, grid lines, dividers, or dividing boxes between frames. The sequence must be drawn on a single, uninterrupted, perfectly clean background.",
        "7. CONSISTENT BASELINE: Maintain a consistent imaginary floor level across all 9 areas, so physical movements look correct when the frames are played sequentially as a GIF.",
        "",
        f"Background: {background_desc}",
        "",
        f"Text: \"{text_overlay}\" - large, bold, comic-style text in each frame, positioned consistently and not covering the character's face.",
        "",
        "=== NEGATIVE CONSTRAINTS (STRICTLY AVOID) ===",
        NEGATIVE_PROMPT,
    ]

    if reference_image:
        prompt_lines.insert(5, f"Character Reference: Use the provided reference image to maintain identical facial features, hairstyle, and outfit across all 9 frames.")

    return "\n".join(prompt_lines)

def create_dir():
    """在 skill 目录下的 output/ 中创建时间戳工作空间"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp_dir = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_path = os.path.join(OUTPUT_DIR, timestamp_dir)
    os.makedirs(full_path, exist_ok=True)
    out_dir_abs = os.path.abspath(full_path)
    print(out_dir_abs)
    return out_dir_abs

def build_prompts_workspace(target_dir):
    json_path = os.path.join(target_dir, "params.json")
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found inside {target_dir}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    mode = data.get("mode", "static")
    character = data.get("character_prompt", "")
    style_preset = data.get("style_preset", "2D_KAWAII")
    custom_style = data.get("custom_style", "")
    scene_theme = data.get("scene_theme", "")
    character_type = data.get("character_type", "")
    color_mood = data.get("color_mood", "BRIGHT_VIBRANT")
    reference_image = data.get("reference_image", "")
    background_type = data.get("background_type", "white")  # 默认白色背景（微信）

    # 归档安全：复制外界基底图到本次发包环境内
    if reference_image and os.path.isfile(reference_image):
        ref_filename = os.path.basename(reference_image)
        new_ref_path = os.path.join(target_dir, "reference_" + ref_filename)
        if os.path.abspath(reference_image) != os.path.abspath(new_ref_path):
            shutil.copy2(reference_image, new_ref_path)
            reference_image = os.path.abspath(new_ref_path)

    expressions = data.get("expressions", [])

    # 构建风格描述
    if style_preset == "CUSTOM" and custom_style:
        style_desc = custom_style + ", high quality."
    else:
        style_desc = STYLE_MAPPING.get(style_preset, STYLE_MAPPING["2D_KAWAII"])

    # 添加场景主题
    if scene_theme and scene_theme in SCENE_MAPPING:
        style_desc += f", {SCENE_MAPPING[scene_theme]}"

    # 添加角色类型提示
    type_hint = ""
    if character_type and character_type in CHARACTER_TYPE_HINTS:
        type_hint = CHARACTER_TYPE_HINTS[character_type]
        character = f"{character}, {type_hint}"

    # 添加配色氛围
    if color_mood and color_mood in COLOR_MOOD_MAPPING:
        style_desc += f", {COLOR_MOOD_MAPPING[color_mood]}"

    if mode == "static":
        prompt_text = build_static_prompt(character, style_desc, expressions, reference_image, background_type)
        with open(os.path.join(target_dir, "prompt.txt"), "w", encoding="utf-8") as f:
            f.write(prompt_text)
    else:
        for i, exp in enumerate(expressions):
            sub_dir = os.path.join(target_dir, f"anim_{i+1:02d}")
            os.makedirs(sub_dir, exist_ok=True)
            action = exp.get("action", "")
            text_overlay = exp.get("text", "")
            prompt_text = build_animated_prompt(character, style_desc, action, text_overlay, reference_image, background_type)
            with open(os.path.join(sub_dir, "prompt.txt"), "w", encoding="utf-8") as f:
                f.write(prompt_text)

    print(f"Prompts successfully generated inside {target_dir}")
    return target_dir

def remote_draw_trigger(prompt_path, output_image_path, reference_image_path=None):
    """调用图片生成 API 生成图像，支持 Gemini 和 千问"""
    api_key, provider = get_api_key()
    if not api_key:
        return False

    print(f"=== Image Generation ({provider.upper()}) ===")
    print(f"[*] Reading prompt: {prompt_path}")
    print(f"[*] Output path: {output_image_path}")
    if reference_image_path:
        print(f"[*] Reference image: {reference_image_path}")

    config = load_config()
    provider_config = config["providers"].get(provider, {})
    model = provider_config.get("model", "gemini-3.1-flash-image-preview")
    api_base_url = provider_config.get("api_base_url", "")

    print(f"[*] Using model: {model}")

    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompt = f.read()

    if provider == "qwen":
        return _qwen_generate_image(prompt, output_image_path, reference_image_path, api_key, model, api_base_url)
    else:
        return _gemini_generate_image(prompt, output_image_path, reference_image_path, api_key, model)


def _gemini_generate_image(prompt, output_image_path, reference_image_path=None, api_key=None, model=None):
    """调用 Gemini API 生成图像"""
    print(f"[*] Generating image with Gemini...")

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("Error: google-genai not installed. Run: pip install google-genai", file=sys.stderr)
        return False

    try:
        client = genai.Client(api_key=api_key)

        # 构建内容：如果有参考图，同时传入图片和文字
        if reference_image_path and os.path.exists(reference_image_path):
            # 读取参考图
            with open(reference_image_path, 'rb') as f:
                image_data = f.read()

            # 检测图片类型
            import imghdr
            img_type = imghdr.what(reference_image_path)
            mime_type = f"image/{img_type}" if img_type else "image/jpeg"

            # 构建多模态输入
            enhanced_prompt = prompt + "\n\n[CRITICAL: The person in the reference image above is the character you must draw. Transform them into the requested style while preserving their key facial features (face shape, eyes, nose, mouth, hair style). Keep the character recognizable!]"
            contents = [
                types.Part.from_bytes(data=image_data, mime_type=mime_type),
                enhanced_prompt  # 文字直接作为字符串
            ]
        else:
            contents = prompt

        response = client.models.generate_content(
            model=model or "gemini-3.1-flash-image-preview",
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            )
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_data = part.inline_data.data
                with open(output_image_path, "wb") as f:
                    f.write(image_data)
                print(f"[✓] Image saved: {output_image_path}")
                return True

        print("Error: No image in response", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error generating image: {e}", file=sys.stderr)
        return False


def _qwen_generate_image(prompt, output_image_path, reference_image_path=None, api_key=None, model=None, api_base_url=None):
    """调用千问 API 生成图像

    支持以下模型：
    - wanx2.1-t2i-turbo, wanx2.1-t2i, wanx-max: 使用 ImageSynthesis API
    - qwen-image-2.0-pro: 使用任务提交式 API
    """
    print(f"[*] Generating image with Qwen (model: {model})...")

    try:
        import dashscope
        from dashscope import ImageSynthesis
    except ImportError:
        print("Error: dashscope not installed. Run: pip install dashscope", file=sys.stderr)
        return False

    # 设置 API Key
    dashscope.api_key = api_key

    # 检测模型类型
    is_wanx_model = model and (model.startswith('wanx') or model.startswith('wan-'))

    if is_wanx_model:
        # wanx 系列使用 ImageSynthesis API
        return _qwen_wanx_generate(prompt, output_image_path, model, api_base_url)
    else:
        # qwen-image 系列使用任务提交式 API
        return _qwen_image_generate(prompt, output_image_path, model, api_base_url, reference_image_path)


def _qwen_wanx_generate(prompt, output_image_path, model=None, api_base_url=None):
    """ wanx 系列模型的图像生成（使用 ImageSynthesis API）"""
    from dashscope import ImageSynthesis
    import dashscope

    if api_base_url:
        dashscope.base_url = api_base_url

    try:
        response = ImageSynthesis.call(
            model=model or "wanx2.1-t2i-turbo",
            prompt=prompt,
            n=1,
            size="1024*1024"
        )

        if response.status_code == 200 and response.output and response.output.results:
            image_url = response.output.results[0].url
            import requests
            img_response = requests.get(image_url)
            if img_response.status_code == 200:
                with open(output_image_path, "wb") as f:
                    f.write(img_response.content)
                print(f"[✓] Image saved: {output_image_path}")
                return True
        print(f"Error from Qwen API: {response.message}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error generating image: {e}", file=sys.stderr)
        return False


def _qwen_image_generate(prompt, output_image_path, model=None, api_base_url=None, reference_image_path=None, api_key=None):
    """qwen-image 系列模型的图像生成（使用 MultiModalConversation API）

    参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/qwen-image-2-0-pro
    """
    import dashscope
    from dashscope import MultiModalConversation

    # 设置 API Key 和 base_url
    if api_key:
        dashscope.api_key = api_key
    if api_base_url:
        dashscope.base_http_api_url = api_base_url
    else:
        dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'

    try:
        # 构建消息
        content = [{"text": prompt}]

        # 如果有参考图，添加到消息中
        if reference_image_path and os.path.exists(reference_image_path):
            with open(reference_image_path, 'rb') as f:
                image_data = f.read()
            # 检测图片类型
            import imghdr
            img_type = imghdr.what(reference_image_path) or 'png'
            content.insert(0, {
                "image": f'data:image/{img_type};base64,{base64.b64encode(image_data).decode("utf-8")}'
            })

        messages = [
            {
                "role": "user",
                "content": content
            }
        ]

        # 调用 API
        response = MultiModalConversation.call(
            model=model or 'qwen-image-2.0-pro',
            messages=messages,
            result_format='message',
            stream=False,
            watermark=False,
            prompt_extend=True,
            negative_prompt="透明格子背景，伪透明背景，噪点，杂质，杂色，颗粒感，地面阴影，投影，光影伪造，边框，网格线，白色边框，黑色边框，分割线，画框，低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，人脸无细节，过度光滑，画面具有 AI 感，构图混乱，文字模糊，扭曲，背景污染，渐变背景，花纹背景，阴影效果，发光效果",
            size='1024*1024'
        )

        if response.status_code == 200:
            # 从响应中提取图片 URL
            resp_dict = json.loads(str(response))
            if resp_dict.get('output') and resp_dict['output'].get('choices') and resp_dict['output']['choices'][0].get('message'):
                message = resp_dict['output']['choices'][0]['message']
                if message.get('content'):
                    for item in message['content']:
                        if item.get('image'):
                            image_url = item['image']
                            # 下载图片
                            import requests
                            img_response = requests.get(image_url)
                            if img_response.status_code == 200:
                                with open(output_image_path, "wb") as f:
                                    f.write(img_response.content)
                                print(f"[✓] Image saved: {output_image_path}")
                                return True
                            else:
                                print(f"Error downloading image: {img_response.status_code}", file=sys.stderr)
                                return False
            print("Error: No image in response", file=sys.stderr)
            return False
        else:
            print(f"Error from Qwen API: HTTP {response.status_code} - {response.message}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"Error generating image: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

def transform_photo_to_chibi(photo_path, style_preset, output_path, additional_description=""):
    """将真人照片转换为指定风格的角色定妆图

    流程（简化版，让 Gemini 处理一切）：
    1. 发送原始照片给 Gemini
    2. Gemini 识别主角 + 转换风格 + 输出单人角色图
    3. 后处理：确保输出尺寸标准（512x512）
    """
    print(f"=== Transforming Photo to Sticker Character ===")
    print(f"[*] Input photo: {photo_path}")
    print(f"[*] Style: {style_preset}")
    print(f"[*] Output: {output_path}")

    if not os.path.exists(photo_path):
        print(f"Error: Photo not found: {photo_path}", file=sys.stderr)
        return False

    api_key, provider = get_api_key()
    if not api_key:
        return False

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("Error: google-genai not installed. Run: pip install google-genai", file=sys.stderr)
        return False

    style_desc = STYLE_MAPPING.get(style_preset, STYLE_MAPPING["2D_KAWAII"])

    # 根据风格类型动态调整转换指令
    style_specific_instructions = {
        "2D_KAWAII": "Convert to cute chibi proportions: big head small body (1:2 ratio), large expressive eyes, rounded features.",
        "2D_ANIME_COOL": "Convert to cool anime style: sharp features, stylish proportions, dynamic pose potential.",
        "3D_CLAY": "Convert to 3D clay/figurine style: soft rounded forms, toy-like appearance, smooth surfaces.",
        "3D_PIXAR": "Convert to Pixar-style 3D character: expressive features, smooth animation-ready design.",
        "PIXEL_ART": "Convert to pixel art style: simplified features suitable for low-res rendering, clear silhouette.",
        "CHINESE_INK": "Convert to Chinese ink painting style: elegant brush strokes, minimal colors, artistic interpretation.",
        "WATERCOLOR": "Convert to watercolor illustration style: soft edges, gentle colors, artistic hand-painted look.",
        "LINE_ART": "Convert to simple line art: clean outlines, minimal detail, clear recognizable features.",
        "CARTOON_WEST": "Convert to Western cartoon style: exaggerated proportions, bold shapes, expressive design.",
        "CHIBI_SD": "Convert to super deformed chibi: extremely large head, tiny body, maximum cuteness.",
        "MEME_STYLE": "Convert to internet meme style: exaggerated expressions, bold lines, funny and expressive.",
    }

    style_transform = style_specific_instructions.get(style_preset, style_specific_instructions["2D_KAWAII"])

    # 读取原始照片（不做预处理，让 Gemini 处理）
    with open(photo_path, 'rb') as f:
        photo_data = f.read()

    import imghdr
    img_type = imghdr.what(photo_path)
    mime_type = f"image/{img_type}" if img_type else "image/jpeg"

    # 构建转换 prompt - 让 Gemini 识别主角并转换
    prompt = f"""TASK: Transform the MAIN PERSON in this photo into a {style_desc} character reference image.

STEP 1 - IDENTIFY THE MAIN PERSON:
Look at the photo and identify the main person/character. Focus on the most prominent person if there are multiple people.

STEP 2 - PRESERVE KEY FEATURES:
Keep the person's distinctive facial features recognizable:
- Face shape, eye shape, nose and mouth characteristics
- Hair style and color
- Any distinctive features (glasses, beard, accessories, etc.)

STEP 3 - STYLE TRANSFORMATION:
{style_transform}

STEP 4 - OUTPUT REQUIREMENTS:
- SINGLE CHARACTER ONLY (the main person you identified)
- Portrait/close-up showing head and shoulders
- Front-facing, neutral expression
- Clean solid WHITE background (#FFFFFF)
- Square aspect ratio (1:1)
- NO text, NO watermarks, NO extra elements
- High quality, suitable as a reference image

{f"Additional notes: {additional_description}" if additional_description else ""}

This will be used as a character reference for generating stickers - it must be a clean, single-character image."""

    print(f"[*] Transforming with gemini-3.1-flash-image-preview...")
    print(f"[*] Letting Gemini identify and transform the main person...")

    try:
        client = genai.Client(api_key=api_key)

        contents = [
            types.Part.from_bytes(data=photo_data, mime_type=mime_type),
            prompt
        ]

        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            )
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_data = part.inline_data.data

                # 后处理：确保标准尺寸
                processed = _process_reference_image(image_data, output_path)
                if processed:
                    print(f"[✓] Character reference saved: {output_path}")
                    return True
                else:
                    # 后处理失败，直接保存
                    with open(output_path, "wb") as f:
                        f.write(image_data)
                    print(f"[✓] Character reference saved: {output_path}")
                    return True

        print("Error: No image in response", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error transforming photo: {e}", file=sys.stderr)
        return False

def _process_reference_image(image_data, output_path, target_size=512):
    """后处理 reference image：缩放到标准尺寸（512x512）

    注意：人脸检测已在预处理阶段完成，这里只做尺寸标准化
    """
    try:
        from io import BytesIO

        img = Image.open(BytesIO(image_data))

        # 转换为 RGB
        if img.mode != 'RGB':
            img = img.convert('RGB')

        width, height = img.size
        print(f"[*] Generated image size: {width}x{height}")

        # 如果不是正方形，裁剪为正方形（取中心）
        if width != height:
            min_dim = min(width, height)
            left = (width - min_dim) // 2
            upper = (height - min_dim) // 2
            right = left + min_dim
            lower = upper + min_dim
            img = img.crop((left, upper, right, lower))
            print(f"[*] Cropped to square: {min_dim}x{min_dim}")

        # 强制缩放到目标尺寸
        if img.size != (target_size, target_size):
            img = img.resize((target_size, target_size), Image.Resampling.LANCZOS)

        # 保存为 PNG
        img.save(output_path, "PNG")
        print(f"[✓] Reference image saved: {target_size}x{target_size}")
        return True

    except Exception as e:
        print(f"[!] Reference image post-processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def draw_character_reference(character_prompt, style_preset, output_path):
    """生成角色定妆参考图（不带动作，纯外观展示）"""
    print(f"=== Generating Character Reference Image ===")
    print(f"[*] Output: {output_path}")

    api_key, provider = get_api_key()
    if not api_key:
        return False

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("Error: google-genai not installed. Run: pip install google-genai", file=sys.stderr)
        return False

    style_desc = STYLE_MAPPING.get(style_preset, STYLE_MAPPING["2D_KAWAII"])

    # 构建定妆图 prompt（强调清晰展示角色外观，不带动作）
    prompt = f"""Character Design Reference Sheet - A clear, well-lit front-view portrait of a single character for use as a design reference.

Character Description: {character_prompt}

Art Style: {style_desc}

IMPORTANT Requirements:
- Full body or upper body portrait, clearly showing the character's face, hair, outfit, and distinguishing features
- Neutral standing pose, no action or movement
- Clean solid white background (#FFFFFF)
- Well-lit, clearly visible details
- High quality, suitable as a reference for generating more images of this same character
- The character should have a simple, pleasant expression

This image will be used as a reference to maintain character consistency across multiple generated images."""

    print(f"[*] Generating with gemini-3.1-flash-image-preview...")

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            )
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_data = part.inline_data.data
                with open(output_path, "wb") as f:
                    f.write(image_data)
                print(f"[✓] Character reference saved: {output_path}")
                return True

        print("Error: No image in response", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error generating image: {e}", file=sys.stderr)
        return False

def process_single_grid(target_dir):
    grid_path = os.path.join(target_dir, "original_grid.png")
    if not os.path.exists(grid_path):
        print(f"Skipping {target_dir}: original_grid.png not found", file=sys.stderr)
        return False

    # background_type 由大模型 prompt 控制，代码不做任何背景处理

    prompt_path = os.path.join(target_dir, "prompt.txt")
    is_animated = False
    if os.path.exists(prompt_path):
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 检测是否是动画序列（新的 prompt 格式或旧的格式）
            is_animated = "9-frame animation" in content or "9-frame animation sprite sheet" in content or "A HIGHLY DYNAMIC 9-frame animation" in content

    try:
        img = Image.open(grid_path)
    except Exception as e:
        print(f"Error opening {grid_path}: {e}")
        return False

    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    width, height = img.size

    # [Bulletproof Safeguard]: Forecfully make the main canvas a perfect square if the model outputs 16:9 or 4:3
    if width != height:
        size = min(width, height)
        c_left = (width - size) // 2
        c_top = (height - size) // 2
        img = img.crop((c_left, c_top, c_left + size, c_top + size))
        width, height = size, size
        print(f"[*] Post-process: Auto-cropped non-square canvas into a {size}x{size} square before grid slicing.")

    # 保留图片的原始背景，不做任何后处理转换

    item_width = width // 3
    item_height = height // 3

    count = 1
    frames = []

    for row in range(3):
        for col in range(3):
            left = col * item_width
            upper = row * item_height
            right = left + item_width
            lower = upper + item_height

            box = (left, upper, right, lower)
            cropped_img = img.crop(box)

            # 直接缩放到 240x240，不留边框
            resized_img = cropped_img.resize((240, 240), Image.Resampling.LANCZOS)

            # 使用原图作为最终输出（已经 240x240）
            final_img = resized_img

            filename = os.path.join(target_dir, f"sticker_{count:02d}.png")
            final_img.save(filename, "PNG")
            frames.append(final_img)

            count += 1

    if is_animated and frames:
        gif_path = os.path.join(target_dir, "animated_sticker.gif")
        frames[0].save(
            gif_path,
            save_all=True,
            append_images=frames[1:],
            duration=100,
            loop=0,
            disposal=2
        )
    return True

def make_white_transparent(img, tolerance=30):
    """将接近白色的像素转为透明

    Args:
        img: PIL Image (RGBA mode)
        tolerance: 白色容差（0-255），用于处理边缘抗锯齿

    Returns:
        处理后的 RGBA Image
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    pixels = img.load()
    width, height = img.size

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            # 检测是否接近白色
            if r >= 255 - tolerance and g >= 255 - tolerance and b >= 255 - tolerance:
                # 计算与纯白的距离，用于平滑边缘
                whiteness = max(r, g, b)
                # 将白色程度转换为透明度
                new_alpha = int(a * (255 - whiteness) / 255)
                pixels[x, y] = (r, g, b, new_alpha)

    return img

def process_workspace(target_dir):
    if os.path.exists(os.path.join(target_dir, "prompt.txt")):
        process_single_grid(target_dir)
    else:
        for item in sorted(os.listdir(target_dir)):
            sub_dir = os.path.join(target_dir, item)
            if os.path.isdir(sub_dir) and item.startswith("anim_"):
                process_single_grid(sub_dir)
                
    print(f"Batch process complete for workspace: {os.path.abspath(target_dir)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python sticker_utils.py create_dir")
        print("  python sticker_utils.py transform_photo <photo_path> <style_preset> <output_path> [additional_description]")
        print("  python sticker_utils.py draw_character <character_prompt> <style_preset> <output_path>")
        print("  python sticker_utils.py build_prompts <target_directory_path>")
        print("  python sticker_utils.py draw <prompt.txt> <output_original_grid.png> [reference_image]")
        print("  python sticker_utils.py draw_with_ref <prompt.txt> <output.png> <reference_image>")
        print("  python sticker_utils.py process <target_directory_path>")
        print("")
        print("配置管理:")
        print("  python sticker_utils.py config                    # 显示当前配置")
        print("  python sticker_utils.py config set <provider>     # 设置 API Key")
        print("  python sticker_utils.py config default <provider> # 设置默认 provider")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "config":
        config_command(sys.argv[2:])
    elif cmd == "create_dir":
        create_dir()
    elif cmd == "transform_photo":
        if len(sys.argv) < 5:
            print("Usage: python sticker_utils.py transform_photo <photo_path> <style_preset> <output_path> [additional_description]")
            sys.exit(1)
        photo_path = sys.argv[2]
        style_preset = sys.argv[3]
        output_path = sys.argv[4]
        additional_desc = sys.argv[5] if len(sys.argv) > 5 else ""
        transform_photo_to_chibi(photo_path, style_preset, output_path, additional_desc)
    elif cmd == "draw_character":
        if len(sys.argv) < 5:
            print("Usage: python sticker_utils.py draw_character <character_prompt> <style_preset> <output_path>")
            sys.exit(1)
        draw_character_reference(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "build_prompts":
        build_prompts_workspace(sys.argv[2])
    elif cmd == "draw":
        if len(sys.argv) < 4:
            print("Usage: python sticker_utils.py draw <prompt.txt> <output.png> [reference_image]")
            sys.exit(1)
        ref_image = sys.argv[4] if len(sys.argv) > 4 else None
        remote_draw_trigger(sys.argv[2], sys.argv[3], ref_image)
    elif cmd == "draw_with_ref":
        if len(sys.argv) < 5:
            print("Usage: python sticker_utils.py draw_with_ref <prompt.txt> <output.png> <reference_image>")
            sys.exit(1)
        remote_draw_trigger(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "process":
        process_workspace(sys.argv[2])
