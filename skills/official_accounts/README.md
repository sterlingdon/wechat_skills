# 微信公众号自动化管理空间

这是一个用于管理微信公众号（内容创作、自动配图、自动排版及草稿箱同步）的自动化工作空间。

## 📂 目录结构

```text
.
├── content/                  # 📝 内容产出目录 (Markdown 格式)
│   ├── 01-ideas/             # 💡 灵感碎片、大纲备忘录
│   ├── 02-drafts/            # ✍️ 正在撰写的草稿
│   ├── 03-review/            # 🔍 已完成配图，等待同步到微信的成稿
│   └── 04-published/         # 🗂️ 已发布文章的归档目录
├── assets/                   # 🖼️ 静态资源与模板
│   ├── images/               # 自动生成或手动收集的配图
│   └── templates/            # Markdown 模板、排版 CSS 样式表、Prompt 模板
├── scripts/                  # ⚙️ 自动化脚本目录
│   ├── generate_images.py    # 自动配图脚本：分析文章结构 -> 提取关键画面 -> 调用文生图 API -> 插入文章
│   └── sync_wechat.py        # 微信同步脚本：上传图片获取 URL -> Markdown 转 HTML (应用 CSS) -> 推送微信草稿箱
├── .github/workflows/        # 🤖 GitHub Actions CI/CD 配置 (可选：实现定时触发或 Push 自动同步)
└── .env.example              # 🔐 环境变量模板 (存放微信 AppID、Secret、AI API Key 等)
```

## 🔄 自动化工作流设计 (Workflow)

整个工作流分为四个阶段，旨在最大限度减少从“写字”到“发布”的机械劳动：

### 阶段一：内容生产 (Creation)
1. 将日常的灵感记录在 `content/01-ideas` 中。
2. 决定写一篇文章时，从 `assets/templates/article.md` 复制模板到 `content/02-drafts` 中进行写作。
3. 专注纯文本输出，遇到需要配图的地方，可以使用特定的占位符（例如：`<!-- 自动配图：描述你想要的画面 -->`，或留白由脚本自动识别）。

### 阶段二：自动配图 (Illustration)
1. 文章初稿完成后，你可以调用工作区提供的自动化脚本 `python scripts/generate_images.py`。
2. 脚本会读取 Markdown，或调用本平台的 `/tuzi-article-illustrator` 等技能进行段落分析，自动生成多维度的 Prompt。
3. 脚本调用 AI 绘画 API（如 Skywork Design、Midjourney 等），生成图片下载到 `assets/images/`，并将对应的 Markdown 图片链接自动注入回文档中。
4. 处理完毕后，文档自动移至 `content/03-review`。

### 阶段三：自动排版与同步 (Syncing)
1. 确认配图无误后，运行 `python scripts/sync_wechat.py`。
2. **图床转换**：由于微信公众号不防盗链，脚本会自动遍历 Markdown 中的本地图片，通过微信公众号 API 上传至“草稿箱临时/永久素材”，并获取微信官方的图片 URL。
3. **排版转换**：读取 `assets/templates/` 中的 CSS 排版模板（类似 Markdown Nice），将 Markdown 解析为带有内联样式（Inline CSS）的 HTML。
4. **推送草稿箱**：调用微信公众号的【新增草稿】API，将富文本 HTML、封面图、标题和摘要推送到公众号草稿箱中。

### 阶段四：发布与归档 (Publish & Archive)
1. 在微信公众平台手机端/PC端预览最终效果，确认无误后点击“群发”或“发布”。
2. 将本地对应的 Markdown 文件移动至 `content/04-published` 归档。

---

## 🛠 初始化设置清单
- [ ] 复制 `.env.example` 为 `.env`
- [ ] 填入 `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET`
- [ ] 填入对应的大模型/绘图 API_KEY
- [ ] 完善 `assets/templates/` 里的文章模板和排版样式
