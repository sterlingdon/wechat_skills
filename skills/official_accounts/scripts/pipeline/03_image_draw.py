import os
import sys
import base64
import json
import time
from dotenv import load_dotenv

load_dotenv()

MAX_RETRIES = 3
RETRY_BASE_DELAY = 5
DEFAULT_GEMINI_MODEL = os.environ.get(
    "GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image-preview"
)
DEFAULT_QWEN_MODEL = os.environ.get("QWEN_IMAGE_MODEL", "qwen-image-2.0-pro")


def _is_wan_model(model: str) -> bool:
    normalized = (model or "").strip().lower()
    return normalized.startswith("wan")


def _is_wan2_model(model: str) -> bool:
    normalized = (model or "").strip().lower()
    return normalized.startswith("wan2.")


def _qwen_size_from_aspect_ratio(aspect_ratio: str) -> str:
    mapping = {
        "21:9": "1536*640",
        "16:9": "1536*864",
        "9:16": "864*1536",
        "1:1": "1024*1024",
    }
    return mapping.get(aspect_ratio, "1024*1024")


def draw_image_gemini_nano_banana(
    prompt: str, output_path: str, aspect_ratio: str = "1:1"
) -> bool:
    print(
        f"🎨 [模块 3] Gemini Nano Banana 开始绘制：{prompt[:20]}... (比例: {aspect_ratio})"
    )

    API_KEY = os.environ.get("GEMINI_API_KEY")
    if not API_KEY:
        print("⚠️ [模块 3] GEMINI_API_KEY 缺失，Gemini 通道不可用。")
        return False

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print(
            "Error: google-genai not installed. Run: pip install google-genai",
            file=sys.stderr,
        )
        return False

    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            client = genai.Client(api_key=API_KEY)

            image_config = types.ImageConfig(aspect_ratio=aspect_ratio)
            config = types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"], image_config=image_config
            )

            response = client.models.generate_content(
                model=DEFAULT_GEMINI_MODEL,
                contents=prompt,
                config=config,
            )

            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    image_data = part.inline_data.data
                    with open(output_path, "wb") as f:
                        f.write(image_data)
                    print(f"✅ [模块 3] Gemini 绘制成功，已保存至 {output_path}")
                    return True

            raise Exception("No image found in Gemini response parts.")

        except Exception as e:
            last_error = e
            error_str = str(e)

            if "503" in error_str and attempt < MAX_RETRIES - 1:
                wait_time = RETRY_BASE_DELAY * (attempt + 1)
                print(
                    f"⏳ [模块 3] API 过载 (503)，{wait_time}秒后重试 ({attempt + 1}/{MAX_RETRIES})..."
                )
                time.sleep(wait_time)
            else:
                break

    print(f"❌ [模块 3] Gemini 绘图失败 (重试{MAX_RETRIES}次后): {last_error}")
    return False


def draw_image_qwen(
    prompt: str, output_path: str, aspect_ratio: str = "1:1"
) -> bool:
    print(f"🎨 [模块 3] 千问开始兜底绘制：{prompt[:20]}... (比例: {aspect_ratio})")

    api_key = os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("QWEN_API_KEY")
    if not api_key:
        print("⚠️ [模块 3] DASHSCOPE_API_KEY 缺失，千问通道不可用。")
        return False

    try:
        import dashscope
    except ImportError:
        print("Error: dashscope not installed. Run: pip install dashscope", file=sys.stderr)
        return False

    dashscope.api_key = api_key
    model = DEFAULT_QWEN_MODEL
    size = _qwen_size_from_aspect_ratio(aspect_ratio)
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            if _is_wan_model(model):
                import requests

                if _is_wan2_model(model):
                    from dashscope.aigc.image_generation import ImageGeneration
                    from dashscope.api_entities.dashscope_response import Message

                    message = Message(role="user", content=[{"text": prompt}])
                    response = ImageGeneration.call(
                        model=model,
                        api_key=api_key,
                        messages=[message],
                        negative_prompt="",
                        prompt_extend=True,
                        watermark=False,
                        n=1,
                        size=size,
                    )
                else:
                    from dashscope import ImageSynthesis

                    response = ImageSynthesis.call(
                        model=model,
                        prompt=prompt,
                        n=1,
                        size=size,
                    )

                if response.status_code != 200:
                    raise Exception(
                        f"Qwen wanx failed: HTTP {response.status_code} - {getattr(response, 'message', 'unknown error')}"
                    )

                resp_dict = json.loads(str(response))
                content = (
                    resp_dict.get("output", {})
                    .get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", [])
                )

                for item in content:
                    image_url = item.get("image")
                    if image_url:
                        img_response = requests.get(image_url, timeout=60)
                        img_response.raise_for_status()
                        with open(output_path, "wb") as f:
                            f.write(img_response.content)
                        print(f"✅ [模块 3] 千问绘制成功，已保存至 {output_path}")
                        return True

                raise Exception("No image found in Wan response.")

            from dashscope import MultiModalConversation
            import requests

            response = MultiModalConversation.call(
                model=model,
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                stream=False,
                watermark=False,
                prompt_extend=True,
                size=size,
            )

            if response.status_code != 200:
                raise Exception(
                    f"Qwen multimodal failed: HTTP {response.status_code} - {getattr(response, 'message', 'unknown error')}"
                )

            resp_dict = json.loads(str(response))
            content = (
                resp_dict.get("output", {})
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content", [])
            )

            for item in content:
                image_url = item.get("image")
                if image_url:
                    img_response = requests.get(image_url, timeout=60)
                    img_response.raise_for_status()
                    with open(output_path, "wb") as f:
                        f.write(img_response.content)
                    print(f"✅ [模块 3] 千问绘制成功，已保存至 {output_path}")
                    return True

            raise Exception("No image found in Qwen response.")

        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                wait_time = RETRY_BASE_DELAY * (attempt + 1)
                print(
                    f"⏳ [模块 3] 千问出图失败，{wait_time}秒后重试 ({attempt + 1}/{MAX_RETRIES})..."
                )
                time.sleep(wait_time)

    print(f"❌ [模块 3] 千问绘图失败 (重试{MAX_RETRIES}次后): {last_error}")
    return False


def _create_dummy_image(path: str):
    dummy_base64 = b"R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
    with open(path, "wb") as f:
        f.write(base64.b64decode(dummy_base64))


class ImageDrawEngine:
    def __init__(self, backend: str = "gemini_nano_banana"):
        self.backend = backend

    def draw(self, prompt: str, output_path: str, aspect_ratio: str = "1:1") -> str:
        backends = {
            "gemini_nano_banana": [
                ("gemini", draw_image_gemini_nano_banana),
                ("qwen", draw_image_qwen),
            ],
            "qwen": [("qwen", draw_image_qwen)],
            "gemini_only": [("gemini", draw_image_gemini_nano_banana)],
        }

        if self.backend not in backends:
            raise ValueError(f"不支持的绘图后端: {self.backend}")

        for backend_name, handler in backends[self.backend]:
            ok = handler(prompt, output_path, aspect_ratio)
            if ok:
                return output_path
            print(f"⚠️ [模块 3] {backend_name} 通道失败，尝试下一个可用通道...")

        print("❌ [模块 3] 所有出图通道均失败，生成占位图保底。")
        _create_dummy_image(output_path)
        return output_path
