import { chromium, Browser, Page } from 'playwright';
import * as fs from 'fs/promises';
import * as path from 'path';
import TurndownService from 'turndown';
import { WechatArticle, SearchResultItem, CrawlerConfig, ArticleImage, ArticleMedia } from './types.js';

/**
 * 微信公众号文章爬虫
 */
export class WechatCrawler {
  private browser: Browser | null = null;
  private config: CrawlerConfig;
  private turndown: TurndownService;

  constructor(config: CrawlerConfig) {
    this.config = config;
    this.turndown = new TurndownService({
      headingStyle: 'atx',
      codeBlockStyle: 'fenced',
    });

    // 解析图片，使用 data-src 或 src
    this.turndown.addRule('wechat-image', {
      filter: 'img',
      replacement: function (_content, node: any) {
        let src = node.getAttribute('data-src') || node.getAttribute('src');
        const alt = node.getAttribute('alt') || '';
        if (!src || src.startsWith('data:')) return '';
        return `![${alt}](${src})`;
      }
    });

    // 解析视频
    this.turndown.addRule('wechat-video', {
      filter: ['video', 'iframe'],
      replacement: function (_content, node: any) {
        const src = node.getAttribute('src') || node.getAttribute('data-src');
        return src ? `\n\n<video controls src="${src}"></video>\n\n` : '';
      }
    });

    // 解析音频
    this.turndown.addRule('wechat-audio', {
      filter: 'audio',
      replacement: function (_content, node: any) {
        const src = node.getAttribute('src') || node.getAttribute('data-src');
        return src ? `\n\n<audio controls src="${src}"></audio>\n\n` : '';
      }
    });
  }

  /**
   * 初始化浏览器
   */
  async init(): Promise<void> {
    this.browser = await chromium.launch({
      headless: false, // 设置为 true 可以无头运行
    });
  }

  /**
   * 关闭浏览器
   */
  async close(): Promise<void> {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }
  }

  /**
   * 搜索文章
   */
  async searchArticles(keyword: string, maxResults: number = 10): Promise<SearchResultItem[]> {
    if (!this.browser) {
      throw new Error('Browser not initialized');
    }

    const page = await this.browser.newPage();
    const results: SearchResultItem[] = [];
    let pageNum = 1;

    try {
      // 访问搜狗微信搜索
      await page.goto('https://weixin.sogou.com/', { waitUntil: 'domcontentloaded', timeout: 30000 });
      await page.waitForSelector('#query', { timeout: 10000 });

      // 输入搜索关键词
      await page.fill('#query', keyword);

      // 点击搜索按钮 - 使用多种选择器尝试
      const searchButton = await page.$('button:has-text("搜文章")') ||
        await page.$('#searchbtn') ||
        await page.$('.swz2');

      if (searchButton) {
        await searchButton.click();
      } else {
        // 如果找不到按钮，按 Enter 键提交
        await page.press('#query', 'Enter');
      }

      await page.waitForLoadState('domcontentloaded');
      await this.randomDelay(1000, 2000);

      // 解析搜索结果
      while (results.length < maxResults) {
        await page.waitForSelector('.news-list, ul.news-list', { timeout: 10000 }).catch(() => {});

        const pageResults = await this.parseSearchResults(page);
        console.log(`  第 ${pageNum} 页找到 ${pageResults.length} 篇文章`);
        results.push(...pageResults);

        if (results.length >= maxResults) {
          break;
        }

        // 检查是否有下一页
        const nextButton = await page.$('a:has-text("下一页"), .np:last-child a');
        if (!nextButton) {
          console.log('  没有更多页面');
          break;
        }

        pageNum++;
        await nextButton.click();
        await page.waitForLoadState('domcontentloaded');
        await this.randomDelay(1500, 3000);
      }

      return results.slice(0, maxResults);
    } finally {
      await page.close();
    }
  }

  /**
   * 解析搜索结果页面
   */
  private async parseSearchResults(page: Page): Promise<SearchResultItem[]> {
    return await page.evaluate(() => {
      const results: SearchResultItem[] = [];

      // 尝试多种选择器
      const items = document.querySelectorAll('.news-box .news-list li, .news-list li, ul.news-list > li');

      items.forEach((item) => {
        const titleLink = item.querySelector('h3 a, .txt-box h3 a');
        const authorSpan = item.querySelector('.s2, .account');
        const timeSpan = item.querySelector('.s2 + span, .time, .date');
        const summaryP = item.querySelector('p, .txt-box p');

        if (titleLink) {
          const href = (titleLink as HTMLAnchorElement).href;
          const title = titleLink.textContent?.trim() || '';
          // 跳过空链接或 JavaScript 链接
          if (href && !href.startsWith('javascript:') && title) {
            results.push({
              title,
              url: href,
              author: authorSpan?.textContent?.trim() || '',
              publishTime: timeSpan?.textContent?.trim() || '',
              summary: summaryP?.textContent?.trim() || '',
            });
          }
        }
      });

      return results;
    });
  }

  /**
   * 搜索并直接点击进入文章
   * 这种方式更可靠，因为搜狗链接需要在新标签页打开
   */
  async searchAndClickArticles(keyword: string, maxResults: number = 10): Promise<WechatArticle[]> {
    if (!this.browser) {
      throw new Error('Browser not initialized');
    }

    const page = await this.browser.newPage();
    const articles: WechatArticle[] = [];

    try {
      // 访问搜狗微信搜索
      await page.goto('https://weixin.sogou.com/', { waitUntil: 'domcontentloaded', timeout: 30000 });
      await page.waitForSelector('#query', { timeout: 10000 });

      // 输入搜索关键词
      await page.fill('#query', keyword);

      // 点击搜索按钮或按 Enter
      const searchButton = await page.$('button:has-text("搜文章")') ||
        await page.$('#searchbtn') ||
        await page.$('.swz2');

      if (searchButton) {
        await searchButton.click();
      } else {
        await page.press('#query', 'Enter');
      }

      await page.waitForLoadState('domcontentloaded');
      await this.randomDelay(1500, 2500);

      // 等待搜索结果加载
      await page.waitForSelector('.news-list li h3 a, .news-list li .txt-box h3 a', { timeout: 10000 });

      // 获取所有文章链接
      const articleLinks = await page.$$('.news-list li h3 a, .news-list li .txt-box h3 a');
      console.log(`  找到 ${articleLinks.length} 篇文章`);

      // 逐个点击文章
      for (let i = 0; i < Math.min(articleLinks.length, maxResults); i++) {
        console.log(`\n[${i + 1}/${Math.min(articleLinks.length, maxResults)}] 正在抓取...`);

        // 监听新页面事件
        const [newPage] = await Promise.all([
          this.browser!.contexts()[0].waitForEvent('page', { timeout: 30000 }).catch(() => null),
          articleLinks[i].click(),
        ]);

        if (newPage) {
          try {
            // 等待页面加载
            await newPage.waitForLoadState('domcontentloaded');
            await this.randomDelay(2000, 3000);

            // 提取文章内容
            const articleData = await this.extractArticleContent(newPage);

            const article: WechatArticle = {
              title: articleData.title,
              url: newPage.url(),
              author: articleData.author,
              publishTime: articleData.publishTime,
              summary: '',
              content: articleData.content,
              contentMarkdown: articleData.content ? this.turndown.turndown(articleData.content) : '',
              images: articleData.images,
              videos: articleData.videos,
              audios: articleData.audios,
            };

            console.log(`  标题: ${article.title}`);
            console.log(`  作者: ${article.author}`);
            console.log(`  图片: ${article.images.length} 张`);
            console.log(`  视频: ${article.videos?.length || 0} 个`);
            console.log(`  音频: ${article.audios?.length || 0} 个`);

            // 下载图片 / 视频 / 音频
            if (this.config.downloadImages) {
              if (article.images.length > 0) {
                await this.downloadImages(article.images, article.title);
              }
              if (article.videos && article.videos.length > 0) {
                await this.downloadMedia(article.videos, article.title);
              }
              if (article.audios && article.audios.length > 0) {
                await this.downloadMedia(article.audios, article.title);
              }
            }

            articles.push(article);
          } catch (error) {
            console.error(`  提取内容失败: ${error}`);
          } finally {
            await newPage.close();
          }
        }

        // 返回搜索结果页面
        await this.randomDelay(1000, 2000);
      }

      return articles;
    } finally {
      await page.close();
    }
  }

  /**
   * 抓取单篇文章
   */
  async crawlArticle(searchResult: SearchResultItem): Promise<WechatArticle> {
    if (!this.browser) {
      throw new Error('Browser not initialized');
    }

    const page = await this.browser.newPage();
    const article: WechatArticle = {
      title: searchResult.title,
      url: searchResult.url,
      author: searchResult.author,
      publishTime: searchResult.publishTime,
      summary: searchResult.summary,
      content: '',
      contentMarkdown: '',
      images: [],
    };

    try {
      console.log(`  访问链接: ${searchResult.url.substring(0, 60)}...`);

      // 访问文章页面 - 搜狗链接会跳转到微信
      await page.goto(searchResult.url, { waitUntil: 'domcontentloaded', timeout: 60000 });

      // 等待跳转 - 检查是否在微信公众号页面
      let retries = 0;
      const maxRetries = 3;
      let isWechatPage = false;

      while (retries < maxRetries && !isWechatPage) {
        const currentUrl = page.url();
        isWechatPage = currentUrl.includes('mp.weixin.qq.com');

        if (!isWechatPage) {
          console.log(`  等待跳转... (${retries + 1}/${maxRetries})`);
          await this.randomDelay(2000, 3000);
          retries++;
        }
      }

      if (!isWechatPage) {
        // 如果还未跳转，尝试直接在当前页面提取内容
        console.log('  尝试从当前页面提取内容');
      }

      // 等待文章内容加载
      await page.waitForSelector('#js_content, .rich_media_content, #activity-name', {
        timeout: 10000,
      }).catch(() => {
        console.log('  警告: 未找到文章内容选择器');
      });

      await this.randomDelay(1000, 2000);

      // 获取文章内容
      const articleData = await this.extractArticleContent(page);
      article.content = articleData.content;
      article.title = articleData.title || searchResult.title;
      article.author = articleData.author || searchResult.author;
      article.publishTime = articleData.publishTime || searchResult.publishTime;
      article.images = articleData.images;
      article.videos = articleData.videos;
      article.audios = articleData.audios;

      // 更新实际 URL
      article.url = page.url();

      // 转换为 Markdown
      if (article.content) {
        article.contentMarkdown = this.turndown.turndown(article.content);
      }

      // 下载图片 / 视频 / 音频
      if (this.config.downloadImages) {
        if (article.images.length > 0) {
          await this.downloadImages(article.images, article.title);
        }
        if (article.videos && article.videos.length > 0) {
          await this.downloadMedia(article.videos, article.title);
        }
        if (article.audios && article.audios.length > 0) {
          await this.downloadMedia(article.audios, article.title);
        }
      }

      return article;
    } finally {
      await page.close();
    }
  }

  /**
   * 通过公众号文章链接直接抓取
   */
  async crawlArticleByUrl(url: string): Promise<WechatArticle> {
    if (!this.browser) {
      throw new Error('Browser not initialized');
    }

    const page = await this.browser.newPage();

    try {
      console.log(`  访问公众号文章链接: ${url.substring(0, 80)}...`);

      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });

      // 等待文章内容加载
      await page
        .waitForSelector('#js_content, .rich_media_content, #activity-name', {
          timeout: 10000,
        })
        .catch(() => {
          console.log('  警告: 未找到文章内容选择器');
        });

      await this.randomDelay(1000, 2000);

      const articleData = await this.extractArticleContent(page);

      const article: WechatArticle = {
        title: articleData.title,
        url: page.url(),
        author: articleData.author,
        publishTime: articleData.publishTime,
        summary: '',
        content: articleData.content,
        contentMarkdown: articleData.content ? this.turndown.turndown(articleData.content) : '',
        images: articleData.images,
        videos: articleData.videos,
        audios: articleData.audios,
      };

      console.log(`  标题: ${article.title}`);
      console.log(`  作者: ${article.author}`);
      console.log(`  图片: ${article.images.length} 张`);
      console.log(`  视频: ${article.videos?.length || 0} 个`);
      console.log(`  音频: ${article.audios?.length || 0} 个`);

      if (this.config.downloadImages) {
        if (article.images.length > 0) {
          await this.downloadImages(article.images, article.title);
        }
        if (article.videos && article.videos.length > 0) {
          await this.downloadMedia(article.videos, article.title);
        }
        if (article.audios && article.audios.length > 0) {
          await this.downloadMedia(article.audios, article.title);
        }
      }

      return article;
    } finally {
      await page.close();
    }
  }

  /**
   * 提取文章内容
   */
  private async extractArticleContent(page: Page): Promise<{
    title: string;
    author: string;
    publishTime: string;
    content: string;
    images: ArticleImage[];
    videos: ArticleMedia[];
    audios: ArticleMedia[];
  }> {
    return await page.evaluate(() => {
      // 获取标题 - 多种选择器
      const titleEl =
        document.querySelector('#activity-name') ||
        document.querySelector('.rich_media_title') ||
        document.querySelector('h1.rich_media_title');
      const title = titleEl?.textContent?.trim() || '';

      // 获取作者/公众号名称
      const authorEl =
        document.querySelector('#js_name') ||
        document.querySelector('.rich_media_meta_nickname') ||
        document.querySelector('a#js_name');
      const author = authorEl?.textContent?.trim() || '';

      // 获取发布时间
      const timeEl =
        document.querySelector('#publish_time') ||
        document.querySelector('.rich_media_meta_date') ||
        document.querySelector('#date');
      const publishTime = timeEl?.textContent?.trim() || '';

      // 获取文章正文
      const contentEl =
        document.querySelector('#js_content') ||
        document.querySelector('.rich_media_content') ||
        document.querySelector('.article-content');

      let content = '';
      const images: ArticleImage[] = [];
      const videos: ArticleMedia[] = [];
      const audios: ArticleMedia[] = [];

      if (contentEl) {
        // 克隆内容以便处理
        const cloneEl = contentEl.cloneNode(true) as HTMLElement;
        content = cloneEl.innerHTML;

        // 获取所有图片
        const imgEls = contentEl.querySelectorAll('img');
        imgEls.forEach((img, index) => {
          // 微信图片通常在 data-src 属性中
          const src = img.getAttribute('data-src') || img.getAttribute('src');
          if (src && !src.startsWith('data:')) {
            images.push({
              url: src,
              alt: img.getAttribute('alt') || '',
              index,
            });
          }
        });

        // 获取视频（简单版：直接拿 <video> 和部分 iframe 源）
        const videoEls = contentEl.querySelectorAll('video, iframe');
        videoEls.forEach((el, index) => {
          const src =
            (el as HTMLVideoElement).src ||
            (el as HTMLVideoElement).getAttribute('data-src') ||
            el.getAttribute('src') ||
            el.getAttribute('data-src');
          if (src && !src.startsWith('data:')) {
            videos.push({
              url: src,
              type: 'video',
              index,
            });
          }
        });

        // 获取音频
        const audioEls = contentEl.querySelectorAll('audio');
        audioEls.forEach((el, index) => {
          const src =
            (el as HTMLAudioElement).src ||
            (el as HTMLAudioElement).getAttribute('data-src') ||
            el.getAttribute('src') ||
            el.getAttribute('data-src');
          if (src && !src.startsWith('data:')) {
            audios.push({
              url: src,
              type: 'audio',
              index,
            });
          }
        });
      }

      return { title, author, publishTime, content, images, videos, audios };
    });
  }

  /**
   * 下载图片
   */
  private async downloadImages(images: ArticleImage[], articleTitle: string): Promise<void> {
    // 创建图片目录
    const safeTitle = this.sanitizeFilename(articleTitle);
    const imageDir = path.join(this.config.outputDir, safeTitle);
    await fs.mkdir(imageDir, { recursive: true });

    for (const image of images) {
      try {
        await this.randomDelay(500, 1000); // 避免请求过快

        // 使用 page 下载图片（处理防盗链）
        const imageBuffer = await this.downloadImage(image.url);

        if (imageBuffer) {
          // 保存图片
          const ext = this.getImageExtension(image.url) || 'jpg';
          const filename = `image_${image.index + 1}.${ext}`;
          const localPath = path.join(imageDir, filename);

          await fs.writeFile(localPath, imageBuffer);
          image.localPath = localPath;

          // 转换为 Base64
          if (this.config.convertToBase64) {
            image.base64 = `data:image/${ext};base64,${imageBuffer.toString('base64')}`;
          }
        }
      } catch (error) {
        console.error(`Failed to download image: ${image.url}`, error);
      }
    }
  }

  /**
   * 下载视频 / 音频等媒体资源
   */
  private async downloadMedia(mediaList: ArticleMedia[], articleTitle: string): Promise<void> {
    if (!this.browser || mediaList.length === 0) return;

    const safeTitle = this.sanitizeFilename(articleTitle);
    const mediaDir = path.join(this.config.outputDir, safeTitle);
    await fs.mkdir(mediaDir, { recursive: true });

    for (const media of mediaList) {
      try {
        await this.randomDelay(500, 1200);

        const buffer = await this.downloadImage(media.url);
        if (!buffer) continue;

        const ext = this.getMediaExtension(media.url, media.type);
        const prefix = media.type === 'video' ? 'video' : 'audio';
        const filename = `${prefix}_${media.index + 1}.${ext}`;
        const localPath = path.join(mediaDir, filename);

        await fs.writeFile(localPath, buffer);
        media.localPath = localPath;
      } catch (error) {
        console.error(`Failed to download media: ${media.url}`, error);
      }
    }
  }

  /**
   * 下载单张图片（处理防盗链）
   */
  private async downloadImage(url: string): Promise<Buffer | null> {
    if (!this.browser) return null;

    try {
      // 复用现有上下文，如无则新建一个带 Referer 的上下文
      let context = this.browser.contexts()[0];
      if (!context) {
        context = await this.browser.newContext({
          extraHTTPHeaders: {
            Referer: 'https://mp.weixin.qq.com/',
          },
        });
      }

      const response = await context.request.get(url, {
        timeout: 30000,
        headers: {
          Referer: 'https://mp.weixin.qq.com/',
        },
      });

      if (!response.ok()) {
        console.error(`Failed to download image (status ${response.status()}): ${url}`);
        return null;
      }

      const body = await response.body();
      return Buffer.from(body);
    } catch (error) {
      console.error(`Error downloading image: ${url}`, error);
      return null;
    }
  }

  /**
   * 获取图片扩展名
   */
  private getImageExtension(url: string): string {
    const match = url.match(/\.(jpg|jpeg|png|gif|webp)/i);
    return match ? match[1].toLowerCase() : 'jpg';
  }

  /**
   * 获取媒体扩展名
   */
  private getMediaExtension(url: string, type: 'video' | 'audio'): string {
    const videoMatch = url.match(/\.(mp4|mov|m4v|webm|m3u8)/i);
    const audioMatch = url.match(/\.(mp3|aac|m4a|wav|ogg)/i);
    if (videoMatch) return videoMatch[1].toLowerCase();
    if (audioMatch) return audioMatch[1].toLowerCase();
    return type === 'video' ? 'mp4' : 'mp3';
  }

  /**
   * 清理文件名
   */
  private sanitizeFilename(name: string): string {
    return name.replace(/[<>:"/\\|?*]/g, '_').substring(0, 100);
  }

  /**
   * 随机延迟
   */
  private async randomDelay(min: number, max: number): Promise<void> {
    const delay = Math.floor(Math.random() * (max - min + 1)) + min;
    await new Promise((resolve) => setTimeout(resolve, delay));
  }
}

/**
 * 保存文章到 Markdown 文件
 */
export async function saveArticleAsMarkdown(
  article: WechatArticle,
  outputPath: string
): Promise<void> {
  let mdContent = article.contentMarkdown;

  // 辅助函数：替换远程资源链接为本地路径
  const replaceMediaUrl = (mediaList: any[]) => {
    mediaList.forEach(media => {
      if (media.url && media.localPath) {
        const filename = path.basename(media.localPath);
        // 使用相对路径，因为 md 文件和图片在同一个目录
        const safeUrl = media.url.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        mdContent = mdContent.replace(new RegExp(safeUrl, 'g'), `./${filename}`);
      }
    });
  };

  if (article.images) replaceMediaUrl(article.images);
  if (article.videos) replaceMediaUrl(article.videos);
  if (article.audios) replaceMediaUrl(article.audios);

  // 清洗格式：移除多余空行、零宽字符，规范化排版
  mdContent = mdContent
    .replace(/\u200b/g, '') // 移除零宽字符
    .replace(/\n{3,}/g, '\n\n') // 移除两层以上的空行
    .trim();

  let content = `# ${article.title}\n\n`;
  content += `> 作者: ${article.author} | 发布时间: ${article.publishTime}\n\n`;
  content += `> 原文链接: ${article.url}\n\n`;
  content += `---\n\n`;
  content += mdContent;

  await fs.writeFile(outputPath, content, 'utf-8');
}

/**
 * 保存文章到 HTML 文件
 */
export async function saveArticleAsHtml(
  article: WechatArticle,
  outputPath: string,
  useBase64Images: boolean = false
): Promise<void> {
  let htmlContent = article.content;

  // 替换图片为本地路径或 Base64
  if (useBase64Images) {
    article.images.forEach((img) => {
      if (img.base64 && img.url) {
        htmlContent = htmlContent.replace(new RegExp(img.url.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), img.base64);
      }
    });
  }

  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${article.title}</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
      line-height: 1.8;
      color: #333;
    }
    h1 {
      text-align: center;
      margin-bottom: 10px;
    }
    .meta {
      text-align: center;
      color: #666;
      margin-bottom: 30px;
      font-size: 14px;
    }
    .content img {
      max-width: 100%;
      height: auto;
      display: block;
      margin: 20px auto;
    }
    .content p {
      margin: 1em 0;
    }
  </style>
</head>
<body>
  <h1>${article.title}</h1>
  <div class="meta">
    <span>作者: ${article.author}</span> |
    <span>发布时间: ${article.publishTime}</span> |
    <a href="${article.url}" target="_blank">原文链接</a>
  </div>
  <hr>
  <div class="content">
    ${htmlContent}
  </div>
</body>
</html>`;

  await fs.writeFile(outputPath, html, 'utf-8');
}

export default WechatCrawler;