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

SCENE_MAPPING = {
    "COMPREHENSIVE": "comprehensive daily life slice-of-life scene",      # 综合
    "FESTIVAL": "celebration festive holiday mood",                       # 节日节气/节日
    "ROMANCE": "romantic sweet loving atmosphere, dating",                # 恋爱交友
    "GREETING": "greeting, expressing thanks or apologies",               # 祝福问候/打招呼致谢
    "WORKPLACE": "office workplace setting, relatable work situations",   # 职场工作
    "STUDY": "student study academic campus setting",                     # 毕业/学生
    "GAMING": "gaming esports competitive vibe",                          # 游戏电竞
    "PETS": "cute funny pet animal situations",                           # 动物萌宠
    "FOOD": "eating food dining lifestyle",                               # 饮食/美食
    "SPORTS": "sports fitness workout sweating",                          # 运动健身
}

CHARACTER_TYPE_HINTS = {
    "HUMAN_CHIBI": "chibi style human character, big head, cute proportions",
    "HUMAN_ANIME": "anime style human character, detailed features",
    "ANIMAL_CUTE": "cute animal character, anthropomorphic traits",
    "ANIMAL_ANTHRO": "anthropomorphic animal character, human-like posture",
    "FANTASY": "fantasy creature, magical being, mythical",
    "OBJECT_PERSONIFIED": "personified object character, living item with face",
    "IP_CHARACTER": "recognizable popular character, faithful to original design",
}

COLOR_MOOD_MAPPING = {
    "BRIGHT_VIBRANT": "bright vibrant saturated colors, cheerful palette",
    "SOFT_PASTEL": "soft pastel colors, gentle macaron palette, dreamy",
    "WARM_COZY": "warm cozy colors, orange and yellow tones, comfortable",
    "COOL_CALM": "cool calm colors, blue and teal tones, serene",
    "MONOCHROME": "monochrome black and white, grayscale",
    "NEON_CYBER": "neon cyber colors, glowing fluorescent, futuristic",
    "VINTAGE_RETRO": "vintage retro colors, faded nostalgic palette",
}

BACKGROUND_TYPE_MAPPING = {
    "white": "STRICTLY SOLID HIGHEST-PURITY WHITE BACKGROUND (#FFFFFF). Ensure 100% pure flat white with NO noise, NO grain, NO ground shadows, and NO lighting artifacts. The background MUST be perfectly clean uniform hex #FFFFFF across the entire image.",
    "transparent": "STRICTLY SOLID FLAT WHITE BACKGROUND (#FFFFFF) for later automated background removal in post-processing. Do NOT generate checkerboard patterns or alpha transparency. Instead, use a completely uniform, flat, and spotless pure white background with absolutely zero noise, zero gradients, and zero drop shadows.",
}

NEGATIVE_PROMPT = "checkerboard background, transparent background artifacts, noise, film grain, dirty background, dust, shadows on ground, drop shadow, lighting artifacts, borders, frames, grid lines, cell dividers, white borders, black borders, colored borders, padding around character, vignette, shadow effects, glow effects, gradient background, patterned background, scenery, background objects, text watermarks, logos, signatures, low quality, blurry, distorted, deformed, extra limbs, missing limbs, cropped character, character touching grid edges, overlapping cells"
