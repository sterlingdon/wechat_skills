import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client()
model = "gemini-3.1-flash-image-preview"

def test_ratio(ratio, prompt="A peaceful forest"):
    print(f"Testing {ratio}...")
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(aspect_ratio=ratio)
            )
        )
        print(f"✅ {ratio} Success!")
        return True
    except Exception as e:
        print(f"❌ {ratio} Failed: {e}")
        return False

ratios = ["21:9", "16:9", "3:2", "1:1"]
for r in ratios:
    test_ratio(r)

print("\nTesting with the failing prompt (first inline)...")
test_ratio("16:9", "一个昏暗的出租屋内，光线仅来自于亮着的电脑屏幕。")
