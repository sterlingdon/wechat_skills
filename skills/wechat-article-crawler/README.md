# 微信公众号文章爬虫

一个用于抓取微信公众号文章、下载图片并生成 Markdown/HTML 输出的工具。

## 功能特点

- 🔍 **文章搜索**: 通过搜狗微信搜索发现公众号文章
- 📄 **内容抓取**: 提取文章标题、正文、发布时间等信息
- 🖼️ **图片下载**: 自动下载文章中的图片，处理防盗链
- 🔄 **格式转换**: 生成 Markdown 和 HTML 两种格式
- 📊 **内容总结**: 提取关键信息，汇总云厂商优惠活动
- 📝 **微信稿件**: 一键生成适合微信公众号的文章稿

## 安装

```bash
cd wechat-article-crawler
npm install
npx playwright install chromium
```

## 使用方法

### 基本使用

```bash
# 使用默认参数抓取
npm run crawl

# 自定义参数
npm run crawl -- -k "OpenCloud 教程" -n 20 -d 10
```

### 命令行参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--keyword` | `-k` | 搜索关键词 | "Open Cloud 小龙虾 云厂商" |
| `--max` | `-n` | 最大文章数 | 10 |
| `--days` | `-d` | 过去多少天的文章 | 7 |
| `--output` | `-o` | 输出目录 | ./output |
| `--no-images` | | 不下载图片 | false |
| `--no-base64` | | 不将图片转换为 Base64 | false |
| `--help` | `-h` | 显示帮助信息 | |

### 示例

```bash
# 抓取过去10天内关于 OpenCloud 部署的20篇文章
npm run crawl -- -k "OpenCloud 部署 教程" -n 20 -d 10

# 只抓取文章，不下载图片
npm run crawl -- -k "小龙虾 优惠" --no-images

# 指定输出目录
npm run crawl -- -o ./my-output
```

## 输出结构

```
output/
├── README.md           # 汇总索引
├── articles.json       # 文章元数据 (JSON)
├── articles/           # 文章详情
│   ├── 文章标题1.md
│   ├── 文章标题1.html
│   ├── 文章标题2.md
│   └── ...
└── images/             # 图片资源
    ├── 文章标题1/
    │   ├── image_1.jpg
    │   ├── image_2.png
    │   └── ...
    └── ...
```

## 生成微信文章稿

抓取完成后，可以运行总结脚本生成微信文章稿：

```bash
npm run summary
```

这将在输出目录生成：
- `wechat_article.md` - Markdown 格式的微信文章稿
- `wechat_article.html` - HTML 格式的微信文章稿

## 注意事项

1. **频率控制**: 工具内置了随机延迟，避免请求过快被限制
2. **防盗链处理**: 图片下载时会自动设置 Referer 头
3. **Base64 图片**: 生成的 HTML 支持将图片转为 Base64 嵌入，方便直接使用
4. **合法使用**: 请尊重原作者版权，仅用于个人学习和研究

## API 使用

也可以作为库使用：

```typescript
import WechatCrawler, { saveArticleAsMarkdown } from './src/crawler.js';

const crawler = new WechatCrawler({
  keyword: 'Open Cloud',
  maxArticles: 10,
  downloadImages: true,
  imageDir: './images',
  outputDir: './output',
  convertToBase64: true,
});

await crawler.init();
const results = await crawler.searchArticles('Open Cloud 小龙虾', 10);
const article = await crawler.crawlArticle(results[0]);
await saveArticleAsMarkdown(article, './article.md');
await crawler.close();
```

## License

MIT