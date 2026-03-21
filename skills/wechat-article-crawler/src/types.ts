/**
 * 公众号文章信息
 */
export interface WechatArticle {
  /** 文章标题 */
  title: string;
  /** 文章链接 */
  url: string;
  /** 作者/公众号名称 */
  author: string;
  /** 发布时间 */
  publishTime: string;
  /** 文章摘要 */
  summary: string;
  /** 文章正文 (HTML) */
  content: string;
  /** 文章正文 (Markdown) */
  contentMarkdown: string;
  /** 图片列表 */
  images: ArticleImage[];
  /** 视频列表 */
  videos?: ArticleMedia[];
  /** 音频列表 */
  audios?: ArticleMedia[];
  /** 原始HTML */
  rawHtml?: string;
}

/**
 * 文章图片
 */
export interface ArticleImage {
  /** 图片URL */
  url: string;
  /** 本地保存路径 */
  localPath?: string;
  /** Base64 编码 */
  base64?: string;
  /** 图片描述/alt文本 */
  alt?: string;
  /** 图片在文章中的索引 */
  index: number;
}

/**
 * 视频 / 音频等富媒体
 */
export interface ArticleMedia {
  /** 媒体资源 URL */
  url: string;
  /** 本地保存路径 */
  localPath?: string;
  /** 媒体类型，如 video/audio */
  type: 'video' | 'audio';
  /** 在文章中的索引 */
  index: number;
  /** 额外信息（如封面、时长等），暂不强制 */
  meta?: Record<string, unknown>;
}

/**
 * 搜索结果项
 */
export interface SearchResultItem {
  title: string;
  url: string;
  author: string;
  publishTime: string;
  summary: string;
}

/**
 * 爬取配置
 */
export interface CrawlerConfig {
  /** 搜索关键词 */
  keyword: string;
  /** 最大文章数 */
  maxArticles: number;
  /** 开始日期 */
  startDate?: Date;
  /** 结束日期 */
  endDate?: Date;
  /** 是否下载图片 */
  downloadImages: boolean;
  /** 图片保存目录 */
  imageDir: string;
  /** 输出目录 */
  outputDir: string;
  /** 是否转换为Base64 */
  convertToBase64: boolean;
}

/**
 * 总结结果
 */
export interface SummaryResult {
  /** 文章标题 */
  title: string;
  /** 核心要点 */
  keyPoints: string[];
  /** 内容摘要 */
  abstract: string;
  /** 相关云厂商优惠信息 */
  cloudOffers?: CloudOffer[];
}

/**
 * 云厂商优惠信息
 */
export interface CloudOffer {
  /** 云厂商名称 */
  vendor: string;
  /** 优惠内容 */
  offer: string;
  /** 链接 */
  link?: string;
  /** 备注 */
  note?: string;
}