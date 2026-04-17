# 微信公众号自动化管理空间

这是一个用于管理微信公众号（内容创作、自动配图、自动排版及草稿箱同步）的自动化工作空间。

## 📂 目录结构

```text
.
├── content_hub/              # 📝 仓库级内容中枢（多个 skill 共享）
│   ├── 00-account-profile/   # 👤 账号主设定（人设 / 栏目 / 标题铁律 / 写作约束）
│   ├── 01-ideas/             # 💡 灵感碎片、大纲备忘录（按日期 + 每题一个目录）
│   ├── 02-drafts/            # ✍️ 正在撰写的草稿
│   ├── 03-review/            # 🔍 已完成配图，等待同步到微信的成稿
│   └── 04-published/         # 🗂️ 已发布文章的归档目录
├── skills/official_accounts/assets/   # 🖼️ 公众号专属静态资源与模板
│   ├── images/               # 自动生成或手动收集的配图
│   └── templates/            # Markdown 模板、排版 CSS 样式表、Prompt 模板
├── skills/official_accounts/scripts/  # ⚙️ 公众号自动化脚本
│   ├── generate_images.py    # 自动配图脚本：分析文章结构 -> 提取关键画面 -> Gemini 出图 -> Qwen 兜底 -> 插入文章
│   └── sync_wechat.py        # 微信同步脚本：上传图片获取 URL -> Markdown 转 HTML (应用 CSS) -> 推送微信草稿箱
├── skills/official_accounts/.github/workflows/   # 🤖 可选 CI/CD
└── skills/official_accounts/.env.example         # 🔐 环境变量模板
```

## 🔄 自动化工作流设计 (Workflow)

整个工作流分为四个阶段，旨在最大限度减少从“写字”到“发布”的机械劳动：

### 阶段零：账号人设加载 (Persona)
1. 如果仓库根目录存在 `content_hub/00-account-profile/`，且其中只有 1 份 `.md`，则默认将其视为当前账号的激活主设定。
2. 写作前必须先读取这份账号主设定，再读取具体 `idea.md`。
3. 账号主设定负责约束：
   - 这篇文章该像谁写
   - 该服务谁
   - 优先写什么栏目和哪一层内容
   - 标题、开头、结构、价值交付要靠什么方式完成

### 阶段一：内容生产 (Creation)
1. 将日常的灵感记录在仓库根目录 `content_hub/01-ideas/YYYY-MM-DD/` 中，并保持“`daily-overview.md` + 每题一个目录”的结构。
2. 决定写一篇文章时，在 `content_hub/02-drafts` 中创建对应文章目录并开始写作。
3. 专注纯文本输出，遇到需要配图的地方，可以使用特定的占位符（例如：`<!-- 自动配图：描述你想要的画面 -->`，或留白由脚本自动识别）。

### `01-ideas` 推荐结构

```text
content_hub/01-ideas/
  YYYY-MM-DD/
    daily-overview.md
    <article-id>/
      idea.md
      sources.md
```

说明：

- `00-account-profile/*.md` 是账号级长期约束，比单篇 `idea.md` 更稳定
- `daily-overview.md` 用来快速浏览当天所有候选题
- `idea.md` 是后续写作阶段的主入口
- `sources.md` 用来保存完整来源和链接，减少主文档噪音

### 阶段二：自动配图 (Illustration)
1. 文章初稿完成后，你可以调用工作区提供的自动化脚本 `python scripts/generate_images.py`。
2. 脚本会读取 Markdown，或调用本平台的 `/tuzi-article-illustrator` 等技能进行段落分析，自动生成多维度的 Prompt。
3. 脚本调用 AI 绘画 API（如 Skywork Design、Midjourney 等），生成图片下载到 `assets/images/`，并将对应的 Markdown 图片链接自动注入回文档中。
   默认优先走 Gemini；当 Gemini 出图失败或超时时，自动切到千问兜底，提高稳定性。
4. 处理完毕后，文档自动移至 `content_hub/03-review`。

### 阶段三：自动排版与同步 (Syncing)
1. 确认配图无误后，运行 `python scripts/sync_wechat.py`。
2. **图床转换**：由于微信公众号不防盗链，脚本会自动遍历 Markdown 中的本地图片，通过微信公众号 API 上传至“草稿箱临时/永久素材”，并获取微信官方的图片 URL。
3. **排版转换**：读取 `assets/templates/` 中的 CSS 排版模板（类似 Markdown Nice），将 Markdown 解析为带有内联样式（Inline CSS）的 HTML。
4. **推送草稿箱**：调用微信公众号的【新增草稿】API，将富文本 HTML、封面图、标题和摘要推送到公众号草稿箱中。

### 阶段四：发布与归档 (Publish & Archive)
1. 在微信公众平台手机端/PC端预览最终效果，确认无误后点击“群发”或“发布”。
2. 将本地对应的 Markdown 文件移动至 `content_hub/04-published` 归档。

---

## 🛠 初始化设置清单
- [ ] 复制 `.env.example` 为 `.env`
- [ ] 填入 `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET`
- [ ] 填入对应的大模型/绘图 API_KEY
- [ ] 完善 `assets/templates/` 里的文章模板和排版样式
