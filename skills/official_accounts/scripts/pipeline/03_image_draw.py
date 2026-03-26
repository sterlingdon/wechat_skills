import os
import sys
import base64
import time
from dotenv import load_dotenv

load_dotenv()

MAX_RETRIES = 3
RETRY_BASE_DELAY = 5


def draw_image_gemini_nano_banana(
    prompt: str, output_path: str, aspect_ratio: str = "1:1"
) -> str:
    print(
        f"🎨 [模块 3] Gemini Nano Banana 开始绘制：{prompt[:20]}... (比例: {aspect_ratio})"
    )

    API_KEY = os.environ.get("GEMINI_API_KEY")
    if not API_KEY:
        print("⚠️ [模块 3] GEMINI_API_KEY 缺失，将生成一张纯色占位图用于测试流水线。")
        _create_dummy_image(output_path)
        return output_path

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print(
            "Error: google-genai not installed. Run: pip install google-genai",
            file=sys.stderr,
        )
        _create_dummy_image(output_path)
        return output_path

    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            client = genai.Client(api_key=API_KEY)

            image_config = types.ImageConfig(aspect_ratio=aspect_ratio)
            config = types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"], image_config=image_config
            )

            model = "gemini-3.1-flash-image-preview"

            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )

            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    image_data = part.inline_data.data
                    with open(output_path, "wb") as f:
                        f.write(image_data)
                    print(f"✅ [模块 3] Gemini 绘制成功，已保存至 {output_path}")
                    return output_path

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
    print("将生成占位图。")
    _create_dummy_image(output_path)
    return output_path


def _create_dummy_image(path: str):
    dummy_base64 = b"R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
    with open(path, "wb") as f:
        f.write(base64.b64decode(dummy_base64))


class ImageDrawEngine:
    def __init__(self, backend: str = "gemini_nano_banana"):
        self.backend = backend

    def draw(self, prompt: str, output_path: str, aspect_ratio: str = "1:1") -> str:
        if self.backend == "gemini_nano_banana":
            return draw_image_gemini_nano_banana(prompt, output_path, aspect_ratio)
        else:
            raise ValueError(f"不支持的绘图后端: {self.backend}")
