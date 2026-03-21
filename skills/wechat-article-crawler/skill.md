---
name: wechat-article-crawler
description: Crawl WeChat official account articles and export full content (Markdown/HTML) plus local assets (images, videos, audio) into per-article directories. Use when the user wants to archive or process WeChat public account articles, scrape articles by keyword or URL, or needs full-fidelity content (text + media) from mp.weixin.qq.com.
---

# WeChat Article Crawler

本 skill 封装当前项目下的 `wechat-article-crawler` 工具，用于：

- 从 **微信公众号文章 URL** 或 **关键词搜索结果（通过搜狗）** 抓取文章
- 导出 **Markdown + HTML 文案**
- 将 **图片 / 视频 / 音频** 下载到与文章同目录，方便整体归档和后续处理

默认不要求阅读量 / 点赞数等指标，能获取则附带，获取不到直接忽略。

---

## 项目结构（约定）

- 目录：`wechat-article-crawler/`
- 主要文件：
  - `src/index.ts`：CLI 入口，解析参数并调用爬虫
  - `src/crawler.ts`：Playwright 爬虫（正文 + 图片 + 视频 + 音频下载）
  - `src/summary.ts`：生成汇总稿（可选）
  - `src/types.ts`：`WechatArticle` 等类型定义

- 输出目录结构（以 `-o ./output` 为例）：

```text
output/
  <safe-title-1>/
    article.md        # Markdown 文案
    article.html      # HTML 文案
    image_1.jpg
    image_2.jpg
    ...
    video_1.mp4
    video_2.mp4
    audio_1.mp3
  <safe-title-2>/
    ...
  README.md           # 抓取文章索引
  articles.json       # 结构化元数据
```

<safe-title> 由标题清洗得到（去除非法字符并截断）。
WechatArticle 结构（核心字段）
来自 src/types.ts：

基础信息

title: string
url: string
author: string
publishTime: string
summary: string
content: string（HTML）
contentMarkdown: string（Markdown）
图片

images: ArticleImage[]
url: string
localPath?: string
base64?: string
alt?: string
index: number
富媒体

videos?: ArticleMedia[]
url: string
localPath?: string
type: 'video'
index: number
audios?: ArticleMedia[]
同上，type: 'audio'

命令用法
在 wechat-article-crawler/ 目录下执行。

1. 单篇文章 URL 模式（推荐）
   抓取单篇 mp.weixin.qq.com 文章，含图文 + 视频/音频：

npm run crawl -- --url "https://mp.weixin.qq.com/s/xxxxxxxx" -o ./output
参数：
--url <文章链接>：单篇文章模式
-o, --output <目录>：输出目录（默认 ./output）
--no-images：只抓文案，不下载任何资源
--no-base64：图片不生成 Base64，仅保存文件
执行后：

控制台会打印标题 / 作者 / 图片数 / 视频数 / 音频数
在 output/<safe-title>/ 下生成：
article.md
article.html
image*\*.jpg
video*_.mp4 / audio\__.mp3（如有）2. 关键词搜索模式（批量）
通过搜狗微信搜索关键词，批量抓取最近 N 篇：

npm run crawl -- -k "关键词" -n 10 -d 7 -o ./output
参数：
-k, --keyword <关键词>
-n, --max <数量>
-d, --days <天数>
其余与 URL 模式相同
内部流程：

打开 https://weixin.sogou.com/，输入关键词搜索
逐条点击结果，打开官方微信文章页
对每篇文章执行正文 + 资源抓取和下载
按「每篇文章一个目录」输出到 output/
资源抓取和下载规则

1. DOM 提取
   在 src/crawler.ts 的 extractArticleContent 中：

正文容器优先级：

#js_content → .rich_media_content → .article-content
资源发现：

图片：
遍历正文内 img 标签
优先 data-src，回退 src
忽略 data: 开头的内联图片
视频：
遍历正文内 video 和部分 iframe
从 src / data-src 中提取 URL
音频：
遍历正文内 audio
同样从 src / data-src 提取 URL 2. 下载行为
所有资源使用 Playwright 的 context.request.get 请求：

Header 含 Referer: https://mp.weixin.qq.com/ 以避免防盗链问题
存储目录：统一写入 output/<safe-title>/

文件命名：

图片：image*<index+1>.<ext>（扩展名从 URL 中推断，默认 jpg）
视频：video*<index+1>.<ext>（推断 mp4/mov/webm/m3u8 等，默认 mp4）
音频：audio\_<index+1>.<ext>（推断 mp3/aac/m4a/wav/ogg 等，默认 mp3）
Base64（可选）：

未传 --no-base64 时，为图片生成 Base64 字符串，挂在 ArticleImage.base64；
saveArticleAsHtml 在 useBase64Images=true 时会将 HTML 中图片 URL 替换为 Base64。

汇总与二次加工（可选）
抓取完成后，可用 summary 命令生成合集稿：

npm run summary -- -o ./output
读取：
output/articles.json
每篇文章的 article.md 及图片 Base64
输出：
output/wechat_article.md
output/wechat_article.html
适合：生成“多篇文章合集”的公众号稿件。

使用场景与注意事项
适合自动触发本 skill 的场景：

用户说「采集/爬取微信公众号文章」「归档公众号文章」「把这篇/这些文章连同图片视频一起保存」等。
用户给出 mp.weixin.qq.com 链接，希望导出 Markdown/HTML 和本地资源。
用户希望按关键词拉一批相关文章做分析或归档。
注意微信风控：

若打开链接时出现「当前环境异常，完成验证后即可继续访问」，Playwright 与浏览器行为一致，会被挡在验证页；
需要用户在本机浏览器中完成验证，或在相同环境下复用已验证的 Cookie，之后再运行爬虫。
性能建议：

不需要 Base64 时，加 --no-base64 提升速度和降低内存占用；
只想要文案时，加 --no-images。
