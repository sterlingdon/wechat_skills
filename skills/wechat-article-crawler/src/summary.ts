#!/usr/bin/env tsx
import * as fs from 'fs/promises';
import * as path from 'path';
import { WechatArticle, ArticleImage } from './types.js';

/**
 * 从已抓取的文章目录读取文章数据
 */
async function loadArticles(outputDir: string): Promise<WechatArticle[]> {
  const jsonPath = path.join(outputDir, 'articles.json');

  try {
    const data = await fs.readFile(jsonPath, 'utf-8');
    const articlesData = JSON.parse(data);

    const articles: WechatArticle[] = [];

    for (const meta of articlesData) {
      const mdPath = path.join(outputDir, sanitizeFilename(meta.title), 'article.md');

      try {
        const mdContent = await fs.readFile(mdPath, 'utf-8');
        const { title, author, publishTime, url, content } = parseMarkdown(mdContent);

        const imagesWithBase64 = await loadImagesBase64(
          meta.images || [],
          outputDir,
          meta.title
        );

        articles.push({
          title: title || meta.title,
          author: author || meta.author,
          publishTime: publishTime || meta.publishTime,
          url: url || meta.url,
          summary: meta.summary || '',
          content: content || '',
          contentMarkdown: mdContent,
          images: imagesWithBase64,
        });
      } catch (error) {
        console.log(`跳过文章: ${meta.title}`);
      }
    }

    return articles;
  } catch {
    console.error('无法读取 articles.json，请先运行 crawl 命令');
    throw new Error('No articles found');
  }
}

/**
 * 解析 Markdown 文件
 */
function parseMarkdown(content: string): {
  title: string;
  author: string;
  publishTime: string;
  url: string;
  content: string;
} {
  const lines = content.split('\n');
  let title = '';
  let author = '';
  let publishTime = '';
  let url = '';
  let contentStart = 0;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (line.startsWith('# ')) {
      title = line.substring(2).trim();
    } else if (line.startsWith('> 作者:')) {
      const match = line.match(/作者:\s*([^|]+)/);
      if (match) author = match[1].trim();
    } else if (line.startsWith('> 发布时间:')) {
      const match = line.match(/发布时间:\s*([^|]+)/);
      if (match) publishTime = match[1].trim();
    } else if (line.startsWith('> 原文链接:')) {
      const match = line.match(/原文链接:\s*(\[.*?\]\((.*?)\)|(.+))/);
      if (match) url = match[2] || match[3];
    } else if (line.startsWith('---')) {
      contentStart = i + 1;
      break;
    }
  }

  return {
    title,
    author,
    publishTime,
    url,
    content: lines.slice(contentStart).join('\n'),
  };
}

/**
 * 加载图片的 Base64 编码
 */
async function loadImagesBase64(
  images: { url?: string; localPath?: string }[],
  outputDir: string,
  articleTitle: string
): Promise<ArticleImage[]> {
  const result: ArticleImage[] = [];

  for (let i = 0; i < images.length; i++) {
    const img = images[i];
    let localPath = img.localPath;

    if (!localPath) {
      const imageDir = path.join(outputDir, 'images', sanitizeFilename(articleTitle));
      const ext = getImageExtension(img.url || '') || 'jpg';
      localPath = path.join(imageDir, `image_${i + 1}.${ext}`);
    }

    try {
      const buffer = await fs.readFile(localPath);
      const ext = path.extname(localPath).substring(1) || 'jpg';
      const base64 = `data:image/${ext};base64,${buffer.toString('base64')}`;

      result.push({
        url: img.url || '',
        localPath,
        base64,
        alt: '',
        index: i,
      });
    } catch {
      // 图片不存在，跳过
    }
  }

  return result;
}

function getImageExtension(url: string): string {
  const match = url.match(/\.(jpg|jpeg|png|gif|webp)/i);
  return match ? match[1].toLowerCase() : 'jpg';
}

function sanitizeFilename(name: string): string {
  return name.replace(/[<>:"/\\|?*]/g, '_').substring(0, 100);
}

/**
 * 提取云厂商优惠信息
 */
function extractCloudOffers(article: WechatArticle): { vendor: string; offer: string }[] {
  const offers: { vendor: string; offer: string }[] = [];
  const content = article.contentMarkdown.toLowerCase();
  const fullContent = article.contentMarkdown;

  const cloudVendors = [
    { name: '阿里云', keywords: ['阿里云', 'aliyun', 'alibaba'] },
    { name: '腾讯云', keywords: ['腾讯云', 'tencent cloud', 'tencentcloud'] },
    { name: '百度智能云', keywords: ['百度云', '百度智能云', 'baidu cloud', 'bce'] },
    { name: '华为云', keywords: ['华为云', 'huawei cloud', 'huaweicloud'] },
    { name: '京东云', keywords: ['京东云', 'jd cloud'] },
    { name: '优刻得', keywords: ['优刻得', 'ucloud'] },
  ];

  const offerKeywords = ['免费', '优惠', '折扣', '活动', '福利', '领', '送', '券', '试用', '0元'];

  for (const vendor of cloudVendors) {
    const hasVendor = vendor.keywords.some((kw) => content.includes(kw.toLowerCase()));
    if (hasVendor) {
      const sentences = fullContent.split(/[。！？\n]/);
      for (const sentence of sentences) {
        const hasOffer = offerKeywords.some((kw) => sentence.includes(kw));
        if (hasOffer && vendor.keywords.some((kw) => sentence.toLowerCase().includes(kw.toLowerCase()))) {
          const cleanSentence = sentence.trim().replace(/[#*`>\[\]]/g, '').substring(0, 150);
          if (cleanSentence.length > 10) {
            offers.push({
              vendor: vendor.name,
              offer: cleanSentence,
            });
          }
        }
      }
    }
  }

  const seen = new Set<string>();
  return offers.filter((offer) => {
    const key = `${offer.vendor}-${offer.offer}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function extractKeyPoints(article: WechatArticle): string[] {
  const points: string[] = [];
  const content = article.contentMarkdown;

  const headings = content.match(/^#{1,3}\s+.+$/gm);
  if (headings) {
    points.push(...headings.slice(0, 5).map((h) => h.replace(/^#+\s+/, '')));
  }

  const listItems = content.match(/^[-*]\s+.+$/gm);
  if (listItems) {
    points.push(...listItems.slice(0, 5).map((i) => i.replace(/^[-*]\s+/, '').substring(0, 50)));
  }

  return [...new Set(points)].slice(0, 5);
}

function generateAbstract(article: WechatArticle): string {
  if (article.summary) {
    return article.summary.substring(0, 200);
  }

  const text = article.contentMarkdown
    .replace(/[#*`>\[\]!]/g, '')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/\n+/g, ' ')
    .trim();

  return text.substring(0, 200) + (text.length > 200 ? '...' : '');
}

/**
 * 生成微信文章稿（Markdown 格式）
 */
async function generateWechatArticleMd(
  articles: WechatArticle[],
  outputPath: string
): Promise<void> {
  console.log('\n正在生成 Markdown 文章稿...');

  let md = `# Open Cloud 小龙虾：国内云厂商优惠活动盘点

> 本文汇总了近期关于 Open Cloud（小龙虾）的国内云厂商优惠活动信息。
>
> 整理时间: ${new Date().toLocaleDateString('zh-CN')} | 共 ${articles.length} 篇文章

---

## 云厂商优惠速览

`;

  // 汇总云厂商优惠
  const allOffers: Map<string, Set<string>> = new Map();

  for (const article of articles) {
    const offers = extractCloudOffers(article);
    for (const offer of offers) {
      if (!allOffers.has(offer.vendor)) {
        allOffers.set(offer.vendor, new Set());
      }
      allOffers.get(offer.vendor)!.add(offer.offer);
    }
  }

  if (allOffers.size > 0) {
    for (const [vendor, offers] of allOffers) {
      md += `### ${vendor}\n\n`;
      for (const offer of Array.from(offers).slice(0, 5)) {
        md += `- ${offer}\n`;
      }
      md += '\n';
    }
  } else {
    md += '*暂无明确的云厂商优惠信息*\n\n';
  }

  md += `---

## 文章详情

`;

  for (let i = 0; i < articles.length; i++) {
    const article = articles[i];
    const keyPoints = extractKeyPoints(article);
    const abstract = generateAbstract(article);

    md += `### ${i + 1}. ${article.title}\n\n`;
    md += `> 作者: ${article.author} | 发布时间: ${article.publishTime}\n\n`;

    if (keyPoints.length > 0) {
      md += `**核心要点:**\n`;
      for (const point of keyPoints.slice(0, 3)) {
        md += `- ${point}\n`;
      }
      md += '\n';
    }

    md += `**摘要:** ${abstract}\n\n`;

    const imagesWithBase64 = article.images.filter((img) => img.base64);
    if (imagesWithBase64.length > 0) {
      md += `**配图 (${imagesWithBase64.length} 张):**\n\n`;
      for (const img of imagesWithBase64.slice(0, 3)) {
        md += `![配图](${img.base64})\n\n`;
      }
    }

    md += `[查看原文](${article.url})\n\n---\n\n`;
  }

  md += `## 使用建议

1. 选择合适的云厂商 - 根据需求选择合适的服务商
2. 注意活动时间 - 优惠活动通常有时限
3. 阅读官方文档 - 部署前了解详细配置要求
4. 安全第一 - 注意数据安全，配置好访问权限

---

*声明: 本文内容整理自公开的微信公众号文章，仅供参考。*
`;

  await fs.writeFile(outputPath, md, 'utf-8');
  console.log(`已生成 Markdown: ${outputPath}`);
}

/**
 * 生成微信文章稿（HTML 格式，带 Base64 图片）
 */
async function generateWechatArticleHtml(
  articles: WechatArticle[],
  outputPath: string
): Promise<void> {
  console.log('\n正在生成 HTML 文章稿...');

  // 汇总云厂商优惠
  const allOffers: Map<string, Set<string>> = new Map();

  for (const article of articles) {
    const offers = extractCloudOffers(article);
    for (const offer of offers) {
      if (!allOffers.has(offer.vendor)) {
        allOffers.set(offer.vendor, new Set());
      }
      allOffers.get(offer.vendor)!.add(offer.offer);
    }
  }

  let html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Open Cloud 小龙虾：国内云厂商优惠活动盘点</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; max-width: 750px; margin: 0 auto; padding: 20px; line-height: 1.8; color: #333; background: #f5f5f5; }
    .container { background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    h1 { text-align: center; color: #d43c33; margin-bottom: 10px; font-size: 24px; }
    .subtitle { text-align: center; color: #666; font-size: 14px; margin-bottom: 30px; }
    h2 { color: #d43c33; border-left: 4px solid #d43c33; padding-left: 15px; margin-top: 30px; font-size: 20px; }
    h3 { color: #333; margin-top: 25px; font-size: 18px; }
    .meta { color: #999; font-size: 14px; padding: 15px; background: #f9f9f9; border-radius: 8px; margin-bottom: 20px; }
    .vendor-card { background: linear-gradient(135deg, #fff5f5 0%, #fff 100%); border: 1px solid #ffd6d6; border-radius: 12px; padding: 20px; margin: 15px 0; }
    .vendor-card h4 { color: #d43c33; margin: 0 0 15px 0; font-size: 18px; }
    .vendor-card ul { margin: 0; padding-left: 20px; }
    .vendor-card li { margin: 8px 0; color: #555; }
    .article-card { border: 1px solid #eee; border-radius: 12px; padding: 25px; margin: 20px 0; background: #fafafa; }
    .article-card h3 { margin-top: 0; color: #1a1a1a; }
    .article-meta { color: #888; font-size: 13px; margin-bottom: 15px; }
    .key-points { background: #f0f7ff; padding: 15px; border-radius: 8px; margin: 15px 0; }
    .key-points h4 { margin: 0 0 10px 0; color: #1890ff; }
    .abstract { color: #555; padding: 10px 0; border-bottom: 1px dashed #ddd; }
    .images-section { margin: 15px 0; }
    .images-section img { max-width: 100%; border-radius: 8px; margin: 10px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    .image-count { background: #e8f5e9; color: #2e7d32; padding: 5px 12px; border-radius: 20px; font-size: 13px; display: inline-block; margin-bottom: 10px; }
    .source-link { display: inline-block; background: #1890ff; color: #fff; padding: 8px 20px; border-radius: 20px; text-decoration: none; font-size: 14px; margin-top: 10px; }
    .source-link:hover { background: #40a9ff; }
    .tips { background: #fff3e0; border-left: 4px solid #ff9800; padding: 20px; border-radius: 8px; margin: 30px 0; }
    .tips h3 { color: #ff9800; margin-top: 0; }
    .tips ol { margin: 0; padding-left: 25px; }
    .tips li { margin: 8px 0; }
    .footer { text-align: center; color: #999; font-size: 13px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; }
    .divider { height: 1px; background: linear-gradient(to right, transparent, #ddd, transparent); margin: 30px 0; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Open Cloud 小龙虾<br>国内云厂商优惠活动盘点</h1>
    <div class="subtitle">
      整理时间: ${new Date().toLocaleDateString('zh-CN')} | 共 ${articles.length} 篇文章
    </div>
`;

  // 云厂商优惠速览
  if (allOffers.size > 0) {
    html += `    <h2>云厂商优惠速览</h2>\n`;
    for (const [vendor, offers] of allOffers) {
      html += `    <div class="vendor-card">
      <h4>${vendor}</h4>
      <ul>\n`;
      for (const offer of Array.from(offers).slice(0, 5)) {
        html += `        <li>${offer}</li>\n`;
      }
      html += `      </ul>
    </div>\n`;
    }
  }

  html += `    <div class="divider"></div>
    <h2>文章详情</h2>
`;

  // 生成每篇文章
  for (let i = 0; i < articles.length; i++) {
    const article = articles[i];
    const keyPoints = extractKeyPoints(article);
    const abstract = generateAbstract(article);
    const imagesWithBase64 = article.images.filter((img) => img.base64);

    html += `    <div class="article-card">
      <h3>${i + 1}. ${article.title}</h3>
      <div class="article-meta">
        作者: ${article.author} | 发布时间: ${article.publishTime}
      </div>
`;

    if (keyPoints.length > 0) {
      html += `      <div class="key-points">
        <h4>核心要点</h4>
        <ul>\n`;
      for (const point of keyPoints.slice(0, 3)) {
        html += `          <li>${point}</li>\n`;
      }
      html += `        </ul>
      </div>\n`;
    }

    html += `      <div class="abstract">
        <strong>摘要:</strong> ${abstract}
      </div>
`;

    if (imagesWithBase64.length > 0) {
      html += `      <div class="images-section">
        <span class="image-count">配图 ${imagesWithBase64.length} 张</span>\n`;
      for (const img of imagesWithBase64.slice(0, 3)) {
        html += `        <img src="${img.base64}" alt="配图">\n`;
      }
      if (imagesWithBase64.length > 3) {
        html += `        <p style="color:#888;font-size:13px;">... 还有 ${imagesWithBase64.length - 3} 张图片</p>\n`;
      }
      html += `      </div>\n`;
    }

    html += `      <a href="${article.url}" target="_blank" class="source-link">查看原文</a>
    </div>\n`;
  }

  html += `    <div class="tips">
      <h3>使用建议</h3>
      <ol>
        <li><strong>选择合适的云厂商</strong> - 根据需求选择合适的服务商</li>
        <li><strong>注意活动时间</strong> - 优惠活动通常有时限</li>
        <li><strong>阅读官方文档</strong> - 部署前了解详细配置要求</li>
        <li><strong>安全第一</strong> - 注意数据安全，配置好访问权限</li>
      </ol>
    </div>

    <div class="footer">
      <p>声明: 本文内容整理自公开的微信公众号文章，仅供参考。</p>
      <p>工具: WeChat Article Crawler</p>
    </div>
  </div>
</body>
</html>`;

  await fs.writeFile(outputPath, html, 'utf-8');
  console.log(`已生成 HTML: ${outputPath}`);
}

/**
 * 主函数
 */
async function main() {
  const args = process.argv.slice(2);
  let outputDir = './output';

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '-o' || args[i] === '--output') {
      outputDir = args[++i];
    } else if (args[i] === '-h' || args[i] === '--help') {
      console.log(`
微信文章稿生成器

用法: npm run summary -- [选项]

选项:
  -o, --output <目录>  文章输出目录 (默认: ./output)
  -h, --help          显示帮助信息
      `);
      process.exit(0);
    }
  }

  outputDir = path.resolve(outputDir);

  console.log('==================================================');
  console.log('微信文章稿生成器');
  console.log('==================================================');
  console.log(`文章目录: ${outputDir}`);

  try {
    console.log('\n正在加载文章...');
    const articles = await loadArticles(outputDir);
    console.log(`加载了 ${articles.length} 篇文章`);

    if (articles.length === 0) {
      console.log('没有找到文章，请先运行 crawl 命令');
      return;
    }

    // 统计图片
    let totalImages = 0;
    let imagesWithBase64 = 0;
    for (const article of articles) {
      totalImages += article.images.length;
      imagesWithBase64 += article.images.filter((img) => img.base64).length;
    }
    console.log(`共 ${totalImages} 张图片，其中 ${imagesWithBase64} 张已转换为 Base64`);

    const mdPath = path.join(outputDir, 'wechat_article.md');
    await generateWechatArticleMd(articles, mdPath);

    const htmlPath = path.join(outputDir, 'wechat_article.html');
    await generateWechatArticleHtml(articles, htmlPath);

    console.log('\n==================================================');
    console.log('生成完成！');
    console.log('==================================================');
    console.log(`Markdown 文件: ${mdPath}`);
    console.log(`HTML 文件: ${htmlPath}`);
    console.log('\n提示: HTML 文件可以直接在浏览器中打开，然后复制内容到微信公众号编辑器');
  } catch (error) {
    console.error('生成失败:', error);
    process.exit(1);
  }
}

main();