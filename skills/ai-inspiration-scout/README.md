# AI Inspiration Scout

为 AI 行业内容创作者准备的“每日灵感探索” skill。

它会在用户缺少灵感时，搜索最近 1-2 天的 AI 新闻、X 平台讨论、头部 IP 动向、GitHub Trending 工具与产品发布，然后把结果写成可直接被 `official_accounts` 消费的 ideas 目录。

## 默认输出位置

```text
content_hub/01-ideas/YYYY-MM-DD/
```

## 默认输出结构

```text
content_hub/01-ideas/YYYY-MM-DD/
  daily-overview.md
  <article-id>/
    idea.md
    sources.md
```

## 定位

- 做选题搜索与灵感沉淀
- 不直接产出公众号正文
- 作为 `official_accounts` 的前置层使用
