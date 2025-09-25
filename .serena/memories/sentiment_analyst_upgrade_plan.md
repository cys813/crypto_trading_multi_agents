# 情绪分析师升级计划摘要

**总目标**: 全面升级`SentimentAnalyst`，将其数据源从模拟数据替换为来自真实世界API（新闻, Twitter, Telegram, YouTube）的实时数据。

**核心计划**:

1.  **技术调研**:
    *   **API选择**: 为新闻、X (Twitter)、YouTube和Telegram选择最佳的API服务。
    *   **库确认**: 确认使用`VADER`进行情绪分析，并为每个API确定相应的Python库（如`newsapi-python`, `tweepy`, `Telethon`）。

2.  **配置与环境**:
    *   **集中配置**: 在`default_config.py`中统一添加所有新的API密钥和目标源（如KOL账户、Telegram频道）。
    *   **依赖管理**: 将所有新库添加到`requirements.txt`文件中。

3.  **分步实施**:
    *   采用模块化方法，逐一重构`SentimentAnalyst`中的`_collect_*`方法：
        *   `_collect_news_sentiment`
        *   `_collect_twitter_sentiment`
        *   `_collect_telegram_sentiment`
        *   `_collect_influencer_opinions`
    *   每个方法都将负责调用相应的API，并使用VADER处理返回的数据，最终输出与现有系统兼容的结构化数据。

该计划确保了整个升级过程的模块化、可控性和系统的健壮性。
