---
name: wechat-official-account-manager
description: 全自动化的微信公众号文章运营套件。支持从灵感扩写、AI自主风格分析、封面及内页配图生成（对接 Gemini SDK），到内联 CSS 渲染及微信草稿箱自动同步。当用户提到"写推文"、"发公众号"、"排版同步"等关键词时触发。
---

# 📝 WeChat Official Account Manager (微信公众号全自动运营管家)

## 1. Skill 概述

本 Skill 专为 AI Agent 设计，将繁琐的微信公众号运营抽象为一条极其流畅的自动化流水线。

**核心能力：**

- 🧠 **AI 自主风格分析** — 自动分析文章情感意境，选择匹配的排版样式，生成封面建议和摘要
- 🎨 **Gemini 官方 SDK 绘图** — 底层深度整合 `google-genai` SDK，生成微信头条封面（900x383）及正文插图（1080x608）
- 🪄 **微信专属黑魔法排版** — 自动将 Markdown 渲染为 HTML，并通过 `premailer` 将 CSS 强制注入为内联样式
- 🔄 **图床置换与无缝入库** — 自动上传图片至微信素材库，调用草稿 API 一键推送

---

## 2. 目录结构

```
content/
  01-ideas/           # 灵感记录
  02-drafts/          # 初稿
    YYYY-MM-DD/       # 按日期组织
      article.md      # Markdown 文章
      images/         # 配图目录
  03-review/          # 待审核（预览阶段）
    YYYY-MM-DD/
      article.md
      images/
      article_preview.html
      sync_record.json
  04-published/       # 已发布
    YYYY-MM-DD/

assets/templates/styles/  # 排版样式
  solemn.css          # 庄重风格（深度分析、严肃话题）
  tech.css            # 技术风格（编程、AI）
  warm.css            # 温暖风格（生活、情感）
  wechat-default.css  # 通用风格
```

---

## 3. 配置

### 3.1 环境变量

在工作区根目录准备 `.env` 文件：

```bash
WECHAT_APP_ID="你的AppID"
WECHAT_APP_SECRET="你的AppSecret"
GEMINI_API_KEY="你的Gemini_API_Key"
```

### 3.2 依赖安装

```bash
pip install requests markdown premailer python-dotenv google-genai pillow
```

---

## 4. 执行流程

### 【第一步】内容创作

在 `content/02-drafts/YYYY-MM-DD/` 下撰写 Markdown 文章。

**配图占位符格式：**
```markdown
<!-- image: 画面详细描述 -->
```

**示例：**
```markdown
# 深入理解 React Hooks

React Hooks 改变了我们编写组件的方式...

<!-- image: infographic 风格。React Hooks 核心概念图。中央是 Hooks 图标，周围标注 useState/useEffect/useContext 三大核心 Hook。简洁现代、冷色调蓝灰配色 -->

Hooks 让函数组件拥有了状态管理能力...
```

### 【第二步】生成配图

```bash
python scripts/generate_images.py "content/02-drafts/2025-03-25/article.md"
```

**自动执行：**
1. 调用 AI 分析文章意境（主题、情感、样式选择）
2. 生成封面图 prompt 和全局风格
3. 绘制封面图（21:9 → 裁切为 900x383）
4. 解析正文占位符，绘制配图（16:9 → 裁切为 1080x608）
5. 输出到 `content/03-review/YYYY-MM-DD/`

### 【第三步】预览 HTML

```bash
python scripts/preview_html.py "content/03-review/2025-03-25/article.md"
```

**自动执行：**
1. 分析文章意境，选择排版样式
2. 渲染 Markdown 为带内联 CSS 的 HTML
3. 输出 `article_preview.html`

**手机预览：**
```bash
python server.py
# 扫码访问 http://192.168.x.x:8080/content/...
```

### 【第四步】同步到微信

```bash
python scripts/sync_wechat.py "content/03-review/2025-03-25/article.md"
```

**自动执行：**
1. 从文章提取标题
2. 获取 AI 生成的摘要
3. 上传所有图片到微信素材库
4. 替换 HTML 中的图片 URL
5. 调用微信草稿 API
6. 保存同步记录到 `sync_record.json`

---

## 5. 排版样式

系统内置 5 套样式，由 AI 根据文章意境自动选择：

| 样式 | 适用场景 |
|------|----------|
| `solemn` | 深度分析、严肃话题、纪念文章 |
| `tech` | 技术、编程、AI、教程 |
| `warm` | 温暖、治愈、生活、情感 |
| `wechat-default` | 通用、新闻、资讯 |

---

## 6. 图片风格一致性原则

**重要：生成图片 prompt 时必须保持与文章主题风格一致。**

### 风格对应关系

| 文章类型 | 图片风格要求 | 禁止元素 |
|----------|-------------|----------|
| **科技/技术** | 简洁现代、代码元素、冷色调、数据可视化 | 恋爱、温馨、复古、手绘插画 |
| **商业/财经** | 专业商务、图表数据、城市天际线 | 可爱卡通、梦幻、文艺风 |
| **生活/情感** | 温暖色调、人物场景、自然元素 | 科幻、赛博朋克、硬核科技 |
| **教程/干货** | 清晰步骤图、界面截图、流程图 | 抽象艺术、过度装饰 |

---

## 7. 科技文章结构化配图规范

**核心原则：科技文章配图 = 信息可视化，而非场景插画。**

### 7.1 配图类型分类

| 类型 | 适用场景 | 特点 |
|------|----------|------|
| **概念图** | 解释核心概念、原理 | 清晰的视觉隐喻、简洁图形、标注说明 |
| **流程图** | 步骤、流程、架构 | 箭头连接、模块化、层次分明 |
| **对比图** | A vs B、前后对比 | 左右/上下分割、清晰对比 |
| **架构图** | 系统架构、技术栈 | 分层结构、组件连接、技术栈展示 |
| **数据图** | 数据展示、统计信息 | 图表、数字、进度条、可视化 |

### 7.2 科技配图 Prompt 模板

**概念图：**
```
<!-- image: infographic 风格。[概念名称]的可视化解释。中央是[核心元素]，周围标注[关键要点1/2/3]。简洁的图标、清晰的文字标签、冷色调蓝灰配色、白底、现代扁平化设计 -->
```

**流程图：**
```
<!-- image: infographic 风格。[流程名称]流程图。从左到右展示[步骤1]→[步骤2]→[步骤3]，每个步骤用圆角矩形框表示，箭头连接，标注关键说明。简洁现代、蓝白配色 -->
```

**架构图：**
```
<!-- image: infographic 风格。[系统名称]架构图。分层展示：顶层是[表现层]，中层是[业务层]，底层是[数据层]，用方框和连接线表示组件关系。技术蓝图风格、深蓝灰配色 -->
```

**对比图：**
```
<!-- image: infographic 风格。[A]与[B]对比图。左右分割布局，左侧列出[A的特点]，右侧列出[B的特点]，中间用VS分隔。清晰对比、现代简约 -->
```

### 7.3 配图 Prompt 要求

1. **必须包含 `infographic 风格`** — 触发信息图生成
2. **明确视觉结构** — 左右/上下/中心辐射/分层
3. **指定配色** — 冷色调、蓝灰、科技蓝、深色主题
4. **禁止模糊描述** — 不要"一个程序员坐在..."这种场景描述

### 7.4 智能体配图工作流

```
文章结构分析
     │
     ▼
┌─────────────────────────────────────┐
│  识别文章中的知识节点：              │
│  • 核心概念 → 概念图                │
│  • 步骤流程 → 流程图                │
│  • 对比分析 → 对比图                │
│  • 架构设计 → 架构图                │
│  • 数据统计 → 数据图                │
└─────────────────────────────────────┘
     │
     ▼
生成结构化 Prompt（infographic 风格）
```

**AI 智能体在 `01_article_analyze` 模块中分析文章类型，并在生成图片 prompt 时自动拼接对应的风格后缀，确保图片与文章气质一致。**

---

## 8. 输出交付

同步成功后返回：
- **media_id**: 草稿 ID
- **thumb_media_id**: 封面图素材 ID
- **sync_record.json**: 完整同步记录

用户需：
1. 打开微信公众号后台预览
2. 确认无误后手动点击"群发"
3. 可选择移动到 `content/04-published/` 归档

---

## 9. 完整示例

```bash
# 1. 在 drafts 目录写好文章（含配图占位符）
vim content/02-drafts/2025-03-25/my_article.md

# 2. 生成配图（自动分析意境、生成封面）
python scripts/generate_images.py "content/02-drafts/2025-03-25/my_article.md"

# 3. 预览 HTML（检查排版效果）
python scripts/preview_html.py "content/03-review/2025-03-25/my_article.md"
open content/03-review/2025-03-25/my_article_preview.html

# 4. 同步到微信草稿箱
python scripts/sync_wechat.py "content/03-review/2025-03-25/my_article.md"
```