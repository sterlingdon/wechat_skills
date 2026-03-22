---
name: wechat-sticker-generator
description: 一键生成符合微信规范的动态(GIF)及静态(PNG)系列表情包套件。支持多种画风、场景、角色类型，全自动切割合成标准产物。当用户提到"表情包"、"动图"、"贴纸"、"sticker"、"表情"等关键词时触发。
---

# 📄 WeChat Sticker Generator (微信表情包套件生成器)

## 1. Skill 概述 (Overview)

本 Skill 专为 AI Agent 设计，提供自动化生成极具戏剧张力、符合微信规范的"动态 GIF 表情包"及"静态图集"。

**核心能力：**

- 🎨 **12种预设画风** — 从二次元到3D黏土，像素风到水墨国风
- 🎭 **7大场景主题** — 日常、职场、恋爱、节日、情绪、游戏、学习
- 👤 **灵活角色系统** — 支持原创角色、知名IP、真人Q版化
- 📸 **真人照片转Q版** — 上传照片→自动转换→生成表情包（保留真人特征）
- 🔒 **角色一致性锁定** — 通过参考图保证多套件角色长相统一
- ⚡ **全自动流水线** — 一键生成九宫格→切片→GIF 合成；**`origin/`** 为原图仅裁剪缩放，去背景成功时额外多 **`nobg/`**（透明）；自动打包符合微信官方表情包标准规范的上传资产，按要求整理产出 **`wechat_export/`** 目录（包含全套规范主图、缩略图、封面、图标、横幅），方便直达打包导出。

---

## 2. 配置 (Configuration)

### 2.1 支持的图片生成 API

本 Skill 支持多种图片生成 API，可灵活切换：

| Provider          | 特点               | 获取 API Key                                               |
| ----------------- | ------------------ | ---------------------------------------------------------- |
| **gemini** (默认) | 效果好速度快，推荐 | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| **qwen**          | 国内访问稳定       | [阿里云 DashScope](https://dashscope.console.aliyun.com/)  |

### 2.2 配置方式

**方式一：环境变量（推荐）**

```bash
# Gemini
export GEMINI_API_KEY="你的API_Key"

# 或 千问
export DASHSCOPE_API_KEY="你的API_Key"
```

**方式二：交互式配置**

```bash
# 显示当前配置
python3 sticker_utils.py config

# 设置 API Key
python3 sticker_utils.py config set gemini
# 然后输入 API Key

# 切换默认 Provider
python3 sticker_utils.py config default qwen
```

### 2.3 首次使用检查

在运行任何生成命令前，Agent 应先检查配置：

```bash
python3 sticker_utils.py config
```

如果显示 `❌` 表示缺少 API Key，需要引导用户配置。

### 2.4 背景去除依赖（可选但推荐）

当 `background_type` 设为 `transparent` 时，`process` 阶段会自动执行去背景。默认优先走本地模型 `rembg`（推荐 `isnet-general-use`）。

```bash
# 推荐安装
pip install rembg

# 如果报 onnxruntime 相关错误，再补一个 CPU 版本
pip install onnxruntime
```

---

## 3. 完整参数结构 (Input Schema)

```json
{
  "mode": "animated",
  "set_name": "打工人龙虾",
  "set_description": "一只每天为了KPI奋斗的Q版龙虾，完美演绎职场辛酸与欢乐！",
  "copyright_info": "OpenClaw 2026",
  "character_prompt": "角色的外观长相详细设定（只描述外观，不要写动作）",
  "reference_image": "【可选】参考图路径，用于锁定角色长相",
  "style_preset": "2D_KAWAII",
  "scene_theme": "WORKPLACE",
  "character_type": "HUMAN_CHIBI",
  "color_mood": "BRIGHT_VIBRANT",
  "background_type": "transparent",
  "enable_bg_removal": true,
  "bg_removal_method": "rembg",
  "bg_removal_model": "isnet-general-use",
  "bg_removal_script_path": "",
  "bg_preserve_overlay": true,
  "bg_preserve_white_tolerance": 40,
  "bg_preserve_missing_alpha_below": 220,
  "expressions": [
    {
      "action": "高度戏剧化的动作描述（必须有大幅度的身体运动！）",
      "text": "配文文字（建议2-4个字，醒目有力）"
    }
  ]
}
```

### 3.0 背景类型 (background_type)

| 选项          | 背景描述           | 适用场景                               |
| ------------- | ------------------ | -------------------------------------- |
| `transparent` | 透明背景           | **默认值**，微信官方表情包要求透明背景 |
| `white`       | 纯白背景 (#FFFFFF) | 需要纯色背景时的备选                   |

**注意：**

- 微信的官方表情包要求透明背景，去除背景更符合审核要求
- 透明背景会在后处理时自动去背景（默认 `rembg` 模型）
- 可通过 `bg_removal_method` 切换：`rembg`（默认）或 `script`（本地脚本）
- **`bg_preserve_overlay`（默认 true）**：rembg 容易把深色配文当背景抠掉；会在抠图后把「原图不是纯白」却被抹成透明的像素（文字、深色描边等）按原图补回，只去白底
- 可调 `bg_preserve_white_tolerance`（默认 40）：数值越大，越把浅灰也当作「白底」从而不强行补回，能有效避免脏背景或光斑被“死抠死留”的情况；数值越小则越容易保留真实的浅灰描边或淡阴影。
- 去背景失败时保留该帧原图，可检查依赖或调整 `bg_removal_model`
- 去背景开启且成功时，会在同目录下保存 **`original_grid_nobg.png`**：整张九宫格去背景之后、切成 9 张贴纸之前的 PNG，便于对照 `original_grid.png` 检查抠图效果
- **目录统一**：**`origin/`** 内为**原图输出**（仅裁剪+240 缩放，无压白底、无 rembg）；去背景成功时**额外**多 **`nobg/`**；未开去背景或失败时只有 `origin/`（会删除遗留的 `nobg/` 与旧版 `white/` 目录）
- **汇总打包导出**：同一 workspace 在 process 时，会在根目录生成 **`wechat_export/`** 文件夹，它是专用于微信后台的“大礼包”，内含符合规格的主图（`main/`）、缩略图（`thumb/`）、封面（`cover.png`）、图标（`icon.png`）及横幅（`banner.png`）。

#### 本地脚本模式（`bg_removal_method: "script"`）

建议脚本接口优先支持以下参数形式（主流程会先按这个格式调用）：

```bash
python3 your_remove_bg.py --input /tmp/in.png --output /tmp/out.png --model isnet-general-use
```

如果你的脚本是简版参数，也兼容：

```bash
python3 your_remove_bg.py /tmp/in.png /tmp/out.png
```

---

## 3. 参数选项详解 (Parameter Options)

### 3.1 风格预设 (style_preset)

| 选项            | 风格描述                         | 适用场景         |
| --------------- | -------------------------------- | ---------------- |
| `2D_KAWAII`     | 日系二次元，圆润可爱，线条干净   | 通用，最推荐     |
| `2D_ANIME_COOL` | 日系帅气风，锐利线条，炫酷感     | 少年向、热血主题 |
| `3D_CLAY`       | 3D黏土质感，柔软立体，手办感     | 儿童、萌系       |
| `3D_PIXAR`      | 皮克斯风格，欧美3D动画质感       | 欧美风、全年龄   |
| `PIXEL_ART`     | 16bit像素风，复古游戏感          | 极客、游戏主题   |
| `CHINESE_INK`   | 中国水墨风，淡雅意境             | 国风、文艺       |
| `WATERCOLOR`    | 水彩手绘风，温柔治愈             | 文艺、清新       |
| `LINE_ART`      | 极简黑白线条，手绘涂鸦感         | 极简风、表情符号 |
| `CARTOON_WEST`  | 美式卡通风，夸张变形             | 搞笑、欧美风     |
| `CHIBI_SD`      | Q版SD比例，头大身小              | 萌系、游戏角色   |
| `MEME_STYLE`    | 表情包网红风，魔性夸张           | 搞笑、网络流行   |
| `CUSTOM`        | 自定义风格（需填写custom_style） | 特殊需求         |

### 3.2 场景主题 (scene_theme) 【直接映射微信官方后台使用场景表】

| 选项            | 微信后台对应勾选          | 适用场景及配文参考                |
| --------------- | ------------------------- | --------------------------------- |
| `COMPREHENSIVE` | **综合**                  | 日常常用、各类百搭场景            |
| `FESTIVAL`      | **节日节气** / **节日**   | 新年快乐、生日快乐、中秋快乐      |
| `ROMANCE`       | **恋爱交友**              | 想你、爱你、么么哒、在吗、晚安    |
| `GREETING`      | **祝福问候** / **打招呼** | 早安、晚安、谢谢老铁、对不起      |
| `WORKPLACE`     | **职场工作**              | 收到、好的、在忙、下班、KPI、干饭 |
| `STUDY`         | **毕业 / 学生**           | 加油、不想学、过了、求过          |
| `GAMING`        | **游戏电竞**              | 胜利、GG、带飞、菜鸡、上号        |
| `PETS`          | **动物萌宠**              | 萌喵、傻犬相关专属                |
| `FOOD`          | **饮食吃饭**              | 喝奶茶、饿了、大餐                |
| `SPORTS`        | **运动健身**              | 冲刺、流汗、去健身                |

### 3.3 角色类型 (character_type)

| 选项                 | 类型描述     | character_prompt 示例                          |
| -------------------- | ------------ | ---------------------------------------------- |
| `HUMAN_CHIBI`        | Q版人类角色  | "一个戴眼镜的短发女生，穿着蓝色卫衣，圆脸大眼" |
| `HUMAN_ANIME`        | 日系动漫人物 | "银色长发少女，红瞳，哥特萝莉装"               |
| `ANIMAL_CUTE`        | 可爱动物     | "一只橘猫，胖乎乎，大眼睛，尾巴翘起"           |
| `ANIMAL_ANTHRO`      | 拟人化动物   | "穿西装的兔子先生，戴礼帽，绅士风度"           |
| `FANTASY`            | 奇幻生物     | "一只小精灵，透明翅膀，发光，飘浮在空中"       |
| `OBJECT_PERSONIFIED` | 拟人化物品   | "一个有表情的饭团，三角形，海苔脸"             |
| `IP_CHARACTER`       | 知名IP角色   | "皮卡丘，黄色电气鼠，红脸颊，闪电尾巴"         |

### 3.4 配色氛围 (color_mood)

| 选项             | 色调描述                   |
| ---------------- | -------------------------- |
| `BRIGHT_VIBRANT` | 明亮鲜艳，高饱和度（默认） |
| `SOFT_PASTEL`    | 柔和粉彩，马卡龙色系       |
| `WARM_COZY`      | 暖色调，温馨舒适           |
| `COOL_CALM`      | 冷色调，沉稳冷静           |
| `MONOCHROME`     | 黑白单色                   |
| `NEON_CYBER`     | 霓虹赛博，荧光色           |
| `VINTAGE_RETRO`  | 复古怀旧，褪色感           |

---

## 4. 动作描述指南 (Action Description Guide)

**⚠️ 关键原则：动作必须有大幅度的身体运动，决不能是"面瘫"表情！**

### 好的动作描述 ✅

```
"向后仰头大笑，笑到眼泪飞溅，肚子剧烈颤抖"
"整个人趴在地上打滚，四肢乱蹬，撒泼耍赖"
"双手捂脸从指缝偷看，身体扭成麻花状"
"一口吞下整个汉堡，腮帮子鼓成气球，打了个超大的饱嗝"
"像火箭一样冲向屏幕，整个人撞在屏幕上滑下来"
```

### 不好的动作描述 ❌

```
"微笑" → 太静止
"开心地看着" → 缺乏动作
"表示同意" → 太抽象
"做出生气的表情" → 动作幅度太小
```

### 戏剧化公式

```
动作 = 夸张的身体姿态 + 面部表情变化 + (可选)道具/特效

示例：
基础版: "开心地笑"
戏剧版: "整个人跳起来双手比V，笑到嘴巴裂到耳朵，周围炸开烟花特效"
```

---

## 5. 完整示例 (Complete Example)

### 用户请求

> "帮我做一套打工人表情包，角色是一个秃头程序员大叔，要3个动态的，搞笑一点"

### Agent 推理过程

1. **识别需求**：用户要表情包 → 触发本 Skill
2. **模式选择**：要"动态"→ `mode: "animated"`
3. **角色设定**：秃头程序员大叔 → `character_type: "HUMAN_CHIBI"`
4. **风格选择**：搞笑打工人 → `style_preset: "MEME_STYLE"` + `scene_theme: "WORKPLACE"`
5. **动作构思**：职场搞笑场景，需要夸张动作

### 最终 params.json

```json
{
  "mode": "animated",
  "set_name": "秃头小猿",
  "set_description": "每天修Bug、抗击KPI的卑微打工人日常，虽然头秃但依然坚强！",
  "copyright_info": "李强制作",
  "character_prompt": "一个中年秃头程序员大叔，圆脸，稀疏的头发，戴厚底黑框眼镜，穿着皱巴巴的格子衬衫，黑眼圈很重，一脸疲惫但眼神呆萌",
  "reference_image": "",
  "style_preset": "MEME_STYLE",
  "scene_theme": "WORKPLACE",
  "character_type": "HUMAN_CHIBI",
  "color_mood": "BRIGHT_VIBRANT",
  "background_type": "transparent",
  "expressions": [
    // 【💡 提示】微信完整表情包专辑需要 16 或 24 张，因此智能体需为主体设计 24 个不同动作！这会让静态拆作 3 个静态网格（static_01~03），动态拆作 24 个（anim_01~24）。
    // 以下由于文档篇幅限制仅展示3项：
    {
      "action": "疯狂敲键盘到手指冒烟，眼睛瞪得像铜铃，整个人变成残影，最后累趴在键盘上流口水",
      "text": "996!"
    },
    {
      "action": "看到代码报错，整个人石化碎裂成渣，眼珠子弹出来，嘴巴张大到能塞下一个拳头",
      "text": "寄!"
    },
    {
      "action": "下班时间一到，瞬间变身火箭冲出办公室，留下一道残影和漫天飞舞的文档",
      "text": "润了!"
    }
  ]
}
```

### 执行命令序列

```bash
# Step 1: 创建工作空间（可选 --provider 指定提供商，目录名会自动带上后缀）
DIR_PATH=$(python3 sticker_utils.py create_dir --provider gemini)
# 输出: /path/to/output/20260321_120000_gemini

# Step 2: 写入 params.json 到 $DIR_PATH/params.json

# Step 3: 解析生成提示词
python3 sticker_utils.py build_prompts $DIR_PATH

# Step 4: 循环批量生图（示例假设只有3项；实际完整的24个则需利用 for 循环全部跑完 anim_01 到 anim_24；静态模式下则是 static_01 到 static_03）
python3 sticker_utils.py draw $DIR_PATH/anim_01/prompt.txt $DIR_PATH/anim_01/original_grid.png --provider gemini
python3 sticker_utils.py draw $DIR_PATH/anim_02/prompt.txt $DIR_PATH/anim_02/original_grid.png --provider gemini
python3 sticker_utils.py draw $DIR_PATH/anim_03/prompt.txt $DIR_PATH/anim_03/original_grid.png --provider gemini

# Step 5: 切片合成
python3 sticker_utils.py process $DIR_PATH

# Step 6: AI 补充微信物料（Banner / Cover / 介绍文案）
# 所有信息均从 $DIR_PATH/params.json 动态读取，无需手动传入角色名或场景
python3 wechat_meta.py $DIR_PATH
```

### 预期产出

```
output/20260321_120000_gemini/
├── params.json
├── anim_01/
│   ├── original_grid.png
│   ├── original_grid_nobg.png   ← 去背景开启时：切片前的整图
│   ├── prompt.txt
│   ├── origin/                  ← 必有：原图裁剪 `sticker_01~09.png` +（动图）`animated_sticker.gif`
│   └── nobg/                    ← 仅去背景成功时：透明套，同上文件名
├── anim_02/
│   └── …
├── anim_03/
│   └── …
├── wechat_export/               ← 🎁 最终直接用于微信平台提交的合规材料包！
│   ├── main/                    ← 240x240 主图 (编号 01~24, GIF或PNG)
│   ├── thumb/                   ← 120x120 缩略图 (编号 01~24, PNG)
│   ├── cover.png                ← 240x240 表情主页面封面图
│   ├── icon.png                 ← 50x50 聊天窗口面板入口图标
│   └── banner.png               ← 750x400 顶部详情页横幅展示图
└── …
└── …
```

---

## 6. 真人照片 → Q版表情包 (Photo-to-Chibi Feature)

**🌟 特色功能：将用户的真人照片转换为Q版动画风格的表情包！**

### 使用场景

用户想要：

- 把自己/朋友的照片做成表情包
- 保持真人特征的同时变成可爱Q版
- 情侣头像、闺蜜头像表情包化

### 完整流程

#### 用户请求示例

> "用我这张照片，帮我做一套可爱的表情包，要那种Q版的，3个动图"

#### Agent 执行步骤

```bash
# ========== 第一步：创建工作空间 ==========
DIR_PATH=$(python3 sticker_utils.py create_dir --provider gemini)

# ========== 第二步：照片转Q版定妆图 ==========
# 用户提供的照片路径
USER_PHOTO="/path/to/user_photo.jpg"

# 转换为Q版定妆图（核心步骤！）
python3 sticker_utils.py transform_photo "$USER_PHOTO" "2D_KAWAII" "$DIR_PATH/base_reference.png" "戴眼镜，短头发"

# 输出: base_reference.png - 这张图就是用户的Q版形象

# ========== 第三步：写入 params.json ==========
# reference_image 填入刚才生成的 base_reference.png 路径
cat > "$DIR_PATH/params.json" << 'EOF'
{
  "mode": "animated",
  "character_prompt": "基于用户照片的Q版角色",
  "reference_image": "/path/to/output/xxx/base_reference.png",
  "style_preset": "2D_KAWAII",
  "expressions": [
    {"action": "开心地跳起来双手比心，整个人变成粉色爱心包围", "text": "爱你!"},
    {"action": "趴在桌子上哭成泪人，眼泪汇成河流", "text": "太难了"},
    {"action": "举着奶茶狂奔，眼睛变成星星状", "text": "续命!"}
  ]
}
EOF

# ========== 第四步：解析裂变 ==========
python3 sticker_utils.py build_prompts $DIR_PATH

# ========== 第五步：带参考图生成 ==========
# 注意：这里使用 draw_with_ref 命令，传入参考图！
python3 sticker_utils.py draw_with_ref $DIR_PATH/anim_01/prompt.txt $DIR_PATH/anim_01/original_grid.png $DIR_PATH/base_reference.png
python3 sticker_utils.py draw_with_ref $DIR_PATH/anim_02/prompt.txt $DIR_PATH/anim_02/original_grid.png $DIR_PATH/base_reference.png
python3 sticker_utils.py draw_with_ref $DIR_PATH/anim_03/prompt.txt $DIR_PATH/anim_03/original_grid.png $DIR_PATH/base_reference.png

# ========== 第六步：切片封包 ==========
python3 sticker_utils.py process $DIR_PATH
```

### transform_photo 命令详解

```bash
python3 sticker_utils.py transform_photo <photo_path> <style_preset> <output_path> [additional_description]
```

| 参数                     | 说明                                            |
| ------------------------ | ----------------------------------------------- |
| `photo_path`             | 用户提供的真人照片路径                          |
| `style_preset`           | **目标风格** - 支持所有 12 种风格（见下方表格） |
| `output_path`            | 输出的定妆图路径                                |
| `additional_description` | 【可选】额外描述，如"戴眼镜"、"长发"等          |

**🌟 支持所有风格转换：**

| 风格            | 适合场景   | 转换效果           |
| --------------- | ---------- | ------------------ |
| `2D_KAWAII`     | 通用可爱风 | 日系圆润 Q 版      |
| `2D_ANIME_COOL` | 帅气少年   | 锐利线条，酷感十足 |
| `3D_CLAY`       | 儿童/萌系  | 黏土手办质感       |
| `3D_PIXAR`      | 全年龄     | 皮克斯动画风格     |
| `PIXEL_ART`     | 游戏玩家   | 复古像素风         |
| `CHINESE_INK`   | 文艺国风   | 水墨画风格         |
| `WATERCOLOR`    | 清新治愈   | 水彩手绘感         |
| `LINE_ART`      | 极简风     | 黑白线条画         |
| `CARTOON_WEST`  | 搞笑欧美   | 美式夸张卡通风     |
| `CHIBI_SD`      | 超萌 Q 版  | 头超大身超小       |
| `MEME_STYLE`    | 网络流行   | 魔性表情包风       |

**🔒 自动优化：**

Gemini 会自动进行以下处理：

1. **主角识别** - 自动识别照片中的主要人物（无需预处理）
2. **风格转换** - 将真人转换为指定风格的 Q 版角色
3. **特征保留** - 保留真人关键特征（脸型、发型、眼镜等）
4. **尺寸优化** - 输出 512x512 标准尺寸
5. **白底纯净** - 纯白背景，无多余元素

### 关键点说明

**为什么必须用 `draw_with_ref` 而不是普通 `draw`？**

- 普通 `draw` 只发送文字 prompt，模型看不到参考图
- `draw_with_ref` 会把参考图作为多模态输入传给模型
- 模型会"看着"参考图来画，保证角色特征一致

**真人特征保留机制：**

脚本会自动强调保留以下特征：

- 脸型（圆脸/瓜子脸/方脸等）
- 眼睛形状和神态
- 鼻子嘴巴特征
- 发型发色
- 标志性特征（眼镜、胡须、痣等）

### 推荐风格搭配

| 原照片类型 | 推荐风格        | 效果               |
| ---------- | --------------- | ------------------ |
| 普通人像   | `2D_KAWAII`     | 日系可爱风，最通用 |
| 男生照片   | `2D_ANIME_COOL` | 帅气少年风         |
| 儿童照片   | `3D_CLAY`       | 黏土手办感，超萌   |
| 情侣照片   | `2D_KAWAII`     | 甜系 Q 版          |
| 游戏玩家   | `PIXEL_ART`     | 复古游戏风         |
| 搞笑表情   | `MEME_STYLE`    | 网红表情包风       |

---

## 7. 智能体执行流程 (Execution Workflow)

### 【第零步】角色定妆（统一生成标准基准图）

**⚠️ 核心定律：所有表情包的生成，必须依赖一张绝对中立、没有夸张动作的“定妆图” (`base_reference.png`)。决不允许直接拿未经处理的复杂照片或原图去跑多格表情包，也决不允许把夸张动作写进定妆步骤！**

Agent 必须根据用户提供的素材情况，严格选择以下三条路线之一来获取 `base_reference.png`：

**情况 A：用户完全没有提供图片（只给了文字）**
必须先让 AI “无中生有”画一张标准定妆图。
```bash
# 1. 创建工作空间
DIR_PATH=$(python3 sticker_utils.py create_dir --provider gemini)

# 2. 生成单独的角色定妆图（必须纯外观展示，绝无夸张动作）
# 参数顺序：character_prompt, style_preset, output_path
python3 sticker_utils.py draw_character "角色的外观描述..." "2D_KAWAII" "$DIR_PATH/base_reference.png"

# 3. 将生成的 base_reference.png 作为 reference_image 写入 params.json
```

**情况 B：用户提供了一张原始图片（例如：真人照片、未处理的插画、背景复杂的原图）**
**绝对不能**直接拿原图去跑表情包流水线！必须先将其“提取优化”成一张规范的标准定妆图。
**⚠️ 致命红线：转换时的 `additional_description` 必须强硬要求“保持中立、面无表情、没有任何动作、纯白背景”。绝对不能把表情包要做的夸张动作（如吐血、大哭、疯狂敲键盘）写进这个指令里！**
```bash
# 1. 创建工作空间
DIR_PATH=$(python3 sticker_utils.py create_dir --provider gemini)

# 2. 将复杂原图/照片转换为干净的标准定妆图
USER_PHOTO="/path/to/user/photo.jpg"
python3 sticker_utils.py transform_photo "$USER_PHOTO" "MEME_STYLE" "$DIR_PATH/base_reference.png" "保持角色外观特征不变。输出一张纯粹的、面无表情或正常微笑的角色参考图（定妆图）。绝对不要有任何夸张动作、不要有疲惫感。纯白背景，正面半身像。"

# 3. 之后，将生成的 base_reference.png 作为 reference_image 写入 params.json
```

**情况 C：用户提供了一张**已经处理好的、完美的**中立标准定妆图**
只有在用户明确表示“这张图已经是一张定妆图”，或者该图显然是纯白背景、正面中立的标准化形象时，才可以跳过生图步骤，直接把它当作 `reference_image` 填入 `params.json`。

---

### 【第一步】沙盒建站

```bash
DIR_PATH=$(python3 sticker_utils.py create_dir --provider gemini)
```

### 【第二步】写入配置（含 reference_image）

将组装好的 JSON 写入 `$DIR_PATH/params.json`
**确保 reference_image 字段已填入第零步生成的基底图路径！**

### 【第三步】解析裂变

```bash
python3 sticker_utils.py build_prompts $DIR_PATH
```

脚本会自动将 reference_image 写入每个子目录的 prompt.txt

### 【第四步】批量生图

```bash
# 情况A：无参考图（或参考图已在prompt中处理）
# 注意：Agent 应该使用循环来处理所有存在的 anim_* 或 static_* 目录！
python3 sticker_utils.py draw $DIR_PATH/anim_01/prompt.txt $DIR_PATH/anim_01/original_grid.png
# ... 对其他有效目录继续执行 ...

# 情况B：有参考图（真人照片转换的情况，必须用 draw_with_ref！）
# 注意：同样的，循环调用所有存在拆分后的子目录！
python3 sticker_utils.py draw_with_ref $DIR_PATH/anim_01/prompt.txt $DIR_PATH/anim_01/original_grid.png $DIR_PATH/base_reference.png
# ... 对其他有效目录继续执行 ...
```

### 【第五步】切片封包

```bash
python3 sticker_utils.py process $DIR_PATH
```

---

### 【第六步】AI 补充微信物料（Banner / Cover / 介绍文案）

⚠️ **这是主流程必要步骤，不是可选操作！** `process` 命令会生成基础的 `wechat_export/`，但 cover 和 banner 只是从第一帧截取的占位图。本步骤会调用 AI 生成真正的专属封面、横幅和完整上传文案。

```bash
# 所有信息（角色名、场景主题、吉祥物外观等）均自动从 $DIR_PATH/params.json 读取
# Agent 只需传入目录路径，无需硬写任何角色或场景信息
python3 wechat_meta.py $DIR_PATH
```

**本步骤的产出（会覆盖 process 的占位内容）：**

| 产物文件 | 规格 | 说明 |
|---|---|---|
| `wechat_export/upload_info.txt` | 文本 | AI 生成的≤80字合集介绍 + 每个表情的4字含义标签 + 风格/主题分类 |
| `wechat_export/banner.png` | 750×400 | AI 专属绘制的横幅（角色与场景主题融合，含合集名称创意排版） |
| `wechat_export/cover.png` | 240×240 | AI 专属绘制的封面（角色特写，直视镜头，高吸引力） |
| `wechat_export/icon.png` | 50×50 | 封面缩小版，用于聊天面板图标 |

**动态读取机制（重要）：** `wechat_meta.py` 的所有 AI Prompt 均通过读取 `params.json` 动态组装：
- `set_name`、`character_prompt`、`scene_theme`、`style_preset` 等字段都从 params 文件取值
- 脚本本身不含任何硬编码的角色名或场景，适用于任意表情包套件

---

### 【例外情况：无 API Key 时的浏览器人工干预路线】

如果 Agent 发现系统中**没有配置 API Key**，或者在第四步调用大模型生成图片时**报错中断**，或用户明确表示想采用网页生图，**应当利用浏览器自动化工具（browser_subagent）接管操作**：

1. **调用浏览器工具**：Agent 自动启动 `browser_subagent`，并给它下达任务：`前往 https://gemini.google.com，在聊天输入框内输入以下生成的提示词并发送。`
2. **免动手全自动输入**：Agent 将生成的 `prompt.txt` 内容传给浏览器实体，子程序会自动定位到输入框、粘贴提示词并按下回车，完全无需用户动手复制！
3. **交付等待**：网页开始生图后，Agent 提醒用户：“我已经打开了浏览器并帮您自动输入了提示词，目前页面正在生成。生成完毕后，请将最满意的九宫格图片保存，并将其文件发给我（或告诉我路径），我会接管切割流程。”
4. **接力处理**：当用户给出/上传生成的图片后，Agent 将其原样拷贝到 `$DIR_PATH/anim_01/original_grid.png`。
5. **恢复流水线**：直接跳至第五步，运行 `python3 sticker_utils.py process $DIR_PATH` 进行全自动切片和拼装。

**附加彩蛋（直接传图切片）**：
如果用户某天直接丢给你一张早已画好的九宫格网格图，让你“把它做成表情包”。你不需要走 1~4 步生图，直接新建一个沙盒文件夹并把图放进 `anim_01/original_grid.png`，然后直接跑 `process` 命令即可！

---

## 8. 输出交付 (Output Handover)

返回沙盒目录路径，并**首要提醒用户**查看直接可以上传的终极发布包：

- 🎁 **微信直接上传规范包 `wechat_export/`（核心产物）**：
  - **`wechat_export/main/`**：包含编号为 `01~24` 的 240x240 主图，满足规范约束。
  - **`wechat_export/thumb/`**：包含编号为 `01~24` 的 120x120 小方块缩略图。
  - **`wechat_export/cover.png`**、**`icon.png`**、**`banner.png`**：引擎自动化截取配置的首发配套资产图。
  - **`wechat_export/upload_info.txt`**：自动生成的表情包名称、介绍、版权信息，可以直接去微信后台复制粘贴。

- ✂️ **过程拆解留档资产（存于 `anim_XX/` 或 `static_XX/` 内）**
  - **`origin/`** 存放各画稿原始提取未抠背产物
  - **`nobg/`** 存放各底稿执行抠背透明提取后的版本
  - **`original_grid_nobg.png`** 为网格整底切除的预览大参考图
