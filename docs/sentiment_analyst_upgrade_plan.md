# 最终修订版计划：全面升级情绪分析师的数据源 (包含Telegram)

**总目标**：将 `SentimentAnalyst` 的多个关键数据输入（新闻、Twitter、Telegram、KOL观点）从当前的模拟数据升级为从真实世界的API获取和处理。

---

### 第一阶段：技术与工具调研 (最终版)

1.  **新闻API方案**:
    *   调研 NewsAPI.org, GNews, CryptoCompare News API。
    *   **目标**：选定一个用于获取通用加密货币新闻。

2.  **社交媒体API方案**:
    *   **X (Twitter) API**: 研究X API及其Python库(`tweepy`)。
    *   **YouTube Data API**: 研究YouTube API及其Python库。
    *   **Telegram API**:
        *   研究从公开的Telegram频道获取消息的可行方案，主要调研`Telethon`或`Pyrogram`库。
        *   **评估重点**：如何匿名或通过应用身份验证来读取公共频道的历史消息，以及相关的限制和配额。
        *   **目标**：找到一个可靠、稳定的方式来监控特定加密货币相关的公开频道。

3.  **情绪分析库**:
    *   初步选定 `VADER (vaderSentiment)`，因为它对社交媒体、新闻和非正式聊天文本都有很好的效果。

---

### 第二阶段：环境与配置准备 (最终版)

1.  **统一管理API密钥与认证**:
    *   在 `src/crypto_trading_agents/default_config.py` 中添加一个统一的外部服务配置段落。
    *   **新增配置项**:
        *   `NEWS_API_KEY: ""`
        *   `X_API_BEARER_TOKEN: ""`
        *   `YOUTUBE_API_KEY: ""`
        *   `TELEGRAM_API_ID: ""`
        *   `TELEGRAM_API_HASH: ""`

2.  **配置目标渠道与KOL列表**:
    *   在配置文件中，扩展源列表以包含Telegram频道。
    *   **示例配置**:
        ```python
        DATA_SOURCES = {
            "kol_twitter_handles": ["VitalikButerin", "saylor"],
            "kol_youtube_channels": ["UCsomething1", "UCsomething2"],
            "target_telegram_channels": ["some_crypto_news_channel", "another_signal_group"]
        }
        ```

3.  **更新项目依赖**:
    *   在 `requirements.txt` 文件中添加所有新需要的库：
        *   `newsapi-python`
        *   `tweepy`
        *   `google-api-python-client`
        *   `Telethon` (或 `Pyrogram`)
        *   `vaderSentiment`

---

### 第三阶段：代码分步修改计划 (最终版)

我将逐个修改`SentimentAnalyst`中返回模拟数据的`_collect_*`方法。

1.  **修改 `_collect_news_sentiment`**: 接入新闻API。
2.  **修改 `_collect_twitter_sentiment`**: 接入X API，搜索公开推文。
3.  **修改 `_collect_telegram_sentiment`**:
    *   **目标**：获取指定Telegram公开频道的情绪。
    *   **逻辑**：
        *   使用`Telethon`客户端进行认证。
        *   从配置中读取目标频道列表。
        *   获取每个频道近期的消息。
        *   使用`VADER`分析消息内容的情绪。
        *   返回一个包含消息总数、情绪分布等指标的结构化字典。
4.  **修改 `_collect_influencer_opinions`**: 接入X和YouTube API，专门获取KOL的观点。
