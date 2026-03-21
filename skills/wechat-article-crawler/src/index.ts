import WechatCrawler, { saveArticleAsMarkdown, saveArticleAsHtml } from './crawler.js';
import { CrawlerConfig, WechatArticle } from './types.js';
import * as fs from 'fs/promises';
import * as path from 'path';

/**
 * 命令行参数
 */
interface CliArgs {
  keyword: string;
  url?: string;
  maxArticles: number;
  days: number;
  outputDir: string;
  downloadImages: boolean;
  convertToBase64: boolean;
}

/**
 * 解析命令行参数
 */
function parseArgs(): CliArgs {
  const args = process.argv.slice(2);
  const cliArgs: CliArgs = {
    keyword: 'Open Cloud 小龙虾 云厂商',
    maxArticles: 10,
    days: 7,
    outputDir: './output',
    downloadImages: true,
    convertToBase64: true,
  };

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--url':
        cliArgs.url = args[++i];
        break;
      case '-k':
      case '--keyword':
        cliArgs.keyword = args[++i];
        break;
      case '-n':
      case '--max':
        cliArgs.maxArticles = parseInt(args[++i], 10);
        break;
      case '-d':
      case '--days':
        cliArgs.days = parseInt(args[++i], 10);
        break;
      case '-o':
      case '--output':
        cliArgs.outputDir = args[++i];
        break;
      case '--no-images':
        cliArgs.downloadImages = false;
        break;
      case '--no-base64':
        cliArgs.convertToBase64 = false;
        break;
      case '-h':
      case '--help':
        console.log(`
微信公众号文章爬虫

用法: npm run crawl -- [选项]

选项:
  --url <文章链接>           直接抓取指定公众号文章链接（mp.weixin.qq.com）
  -k, --keyword <关键词>    搜索关键词 (默认: "Open Cloud 小龙虾 云厂商")
  -n, --max <数量>          最大文章数 (默认: 10)
  -d, --days <天数>         过去多少天的文章 (默认: 7)
  -o, --output <目录>       输出目录 (默认: ./output)
  --no-images              不下载图片
  --no-base64              不将图片转换为 Base64
  -h, --help               显示帮助信息

示例:
  npm run crawl -- -k "OpenCloud 教程" -n 20 -d 10
        `);
        process.exit(0);
    }
  }

  return cliArgs;
}

/**
 * 主函数
 */
async function main() {
  const args = parseArgs();

  console.log('='.repeat(50));
  console.log('微信公众号文章爬虫');
  console.log('='.repeat(50));
  if (args.url) {
    console.log(`模式: 单篇文章链接抓取`);
    console.log(`文章链接: ${args.url}`);
  } else {
    console.log(`模式: 关键词搜索抓取`);
    console.log(`搜索关键词: ${args.keyword}`);
    console.log(`最大文章数: ${args.maxArticles}`);
    console.log(`时间范围: 过去 ${args.days} 天`);
  }
  console.log(`输出目录: ${args.outputDir}`);
  console.log('='.repeat(50));

  // 创建输出目录
  const outputDir = path.resolve(args.outputDir);

  await fs.mkdir(outputDir, { recursive: true });

  // 配置爬虫
  const config: CrawlerConfig = {
    keyword: args.keyword,
    maxArticles: args.maxArticles,
    startDate: new Date(Date.now() - args.days * 24 * 60 * 60 * 1000),
    endDate: new Date(),
    downloadImages: args.downloadImages,
    imageDir: outputDir,
    outputDir,
    convertToBase64: args.convertToBase64,
  };

  const crawler = new WechatCrawler(config);
  let articles: WechatArticle[] = [];

  try {
    // 初始化浏览器
    console.log('\n正在启动浏览器...');
    await crawler.init();

    if (args.url) {
      console.log(`\n正在抓取指定文章链接: ${args.url}`);
      const article = await crawler.crawlArticleByUrl(args.url);
      articles = [article];
    } else {
      // 使用点击方式搜索和抓取文章（更可靠）
      console.log(`\n正在搜索并抓取文章: "${args.keyword}"...`);
      articles = await crawler.searchAndClickArticles(args.keyword, args.maxArticles);
    }

    // 保存所有文章
    for (let i = 0; i < articles.length; i++) {
      const article = articles[i];
      console.log(`\n保存文章 ${i + 1}/${articles.length}: ${article.title}`);

      const safeTitle = sanitizeFilename(article.title);
      const articleDir = path.join(outputDir, safeTitle);
      await fs.mkdir(articleDir, { recursive: true });

      // 保存为 Markdown
      const mdPath = path.join(articleDir, 'article.md');
      await saveArticleAsMarkdown(article, mdPath);
      console.log(`  ✓ 已保存 Markdown: ${mdPath}`);

      // 保存为 HTML
      const htmlPath = path.join(articleDir, 'article.html');
      await saveArticleAsHtml(article, htmlPath, args.convertToBase64);
      console.log(`  ✓ 已保存 HTML: ${htmlPath}`);
    }

    // 生成汇总索引
    await generateIndex(articles, outputDir);

    console.log('\n' + '='.repeat(50));
    console.log('抓取完成！');
    console.log(`共抓取 ${articles.length} 篇文章`);
    console.log(`输出目录: ${outputDir}`);
    console.log('='.repeat(50));

  } finally {
    await crawler.close();
  }
}

/**
 * 清理文件名
 */
function sanitizeFilename(name: string): string {
  return name.replace(/[<>:"/\\|?*]/g, '_').substring(0, 100);
}

/**
 * 生成汇总索引
 */
async function generateIndex(articles: WechatArticle[], outputDir: string): Promise<void> {
  // Markdown 索引
  let mdIndex = `# 公众号文章汇总\n\n`;
  mdIndex += `> 抓取时间: ${new Date().toLocaleString('zh-CN')}\n`;
  mdIndex += `> 共 ${articles.length} 篇文章\n\n`;
  mdIndex += `---\n\n`;

  articles.forEach((article, index) => {
    mdIndex += `## ${index + 1}. ${article.title}\n\n`;
    mdIndex += `- 作者: ${article.author}\n`;
    mdIndex += `- 发布时间: ${article.publishTime}\n`;
    mdIndex += `- 原文链接: [${article.url}](${article.url})\n`;
    mdIndex += `- 图片数量: ${article.images.length}\n`;
    mdIndex += `- 本地文件: [Markdown](./${sanitizeFilename(article.title)}/article.md) | [HTML](./${sanitizeFilename(article.title)}/article.html)\n\n`;
    mdIndex += `**摘要:** ${article.summary}\n\n`;
    mdIndex += `---\n\n`;
  });

  await fs.writeFile(path.join(outputDir, 'README.md'), mdIndex, 'utf-8');

  // JSON 数据
  const jsonData = articles.map((article) => ({
    title: article.title,
    author: article.author,
    publishTime: article.publishTime,
    url: article.url,
    summary: article.summary,
    imageCount: article.images.length,
    images: article.images.map((img) => ({
      url: img.url,
      localPath: img.localPath,
      hasBase64: !!img.base64,
    })),
  }));

  await fs.writeFile(
    path.join(outputDir, 'articles.json'),
    JSON.stringify(jsonData, null, 2),
    'utf-8'
  );

  console.log('\n✓ 已生成汇总索引');
}

main().catch(console.error);