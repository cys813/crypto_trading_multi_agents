# 情绪分析师升级计划详情

## 技术选型

### API选择
1. **新闻API**: NewsAPI (newsapi.org) - 提供全球新闻数据，支持情感分析
2. **Twitter API**: Twitter API v2 - 官方API，支持推文搜索和实时数据流
3. **Telegram API**: Telegram Bot API - 通过机器人API访问公开频道和群组消息
4. **YouTube API**: YouTube Data API v3 - 访问视频数据和评论

### Python库选择
1. **NewsAPI**: newsapi-python - 官方Python客户端
2. **Twitter**: tweepy - 广泛使用的Twitter API Python库
3. **Telegram**: python-telegram-bot - 官方推荐的Python库
4. **YouTube**: google-api-python-client - Google官方客户端库
5. **情感分析**: vaderSentiment - 专门针对社交媒体文本的情感分析工具

## 配置管理

### API密钥配置
在`default_config.py`中添加以下配置项：
- NEWS_API_KEY
- TWITTER_BEARER_TOKEN
- TELEGRAM_BOT_TOKEN
- YOUTUBE_API_KEY

### 目标源配置
- 新闻源：主流财经媒体、加密货币专业媒体
- Twitter账户：行业KOL、项目官方账户、交易所官方账户
- Telegram频道：知名分析师频道、项目社区频道
- YouTube频道：知名分析师、项目官方频道

## 依赖管理

在`requirements.txt`中添加以下依赖：
- newsapi-python>=0.2.0
- tweepy>=4.14.0
- python-telegram-bot>=20.0
- google-api-python-client>=2.80.0
- vaderSentiment>=3.3.2

## 实施步骤

### 1. 环境配置
- 在`default_config.py`中添加API密钥和目标源配置
- 在`requirements.txt`中添加新依赖库
- 更新环境变量文件

### 2. 方法重构
#### _collect_news_sentiment
- 使用NewsAPI获取相关新闻文章
- 使用VADER分析文章情感
- 返回结构化情感数据

#### _collect_twitter_sentiment
- 使用Tweepy获取相关推文
- 使用VADER分析推文情感
- 返回结构化情感数据

#### _collect_telegram_sentiment
- 使用python-telegram-bot获取频道消息
- 使用VADER分析消息情感
- 返回结构化情感数据

#### _collect_influencer_opinions
- 使用YouTube Data API获取相关视频和评论
- 使用VADER分析视频标题、描述和评论情感
- 返回结构化情感数据