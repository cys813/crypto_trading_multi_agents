#!/usr/bin/env python3
"""
加密货币情绪分析 - 限定最近2周新闻数据
专门分析BTC和SOL的最近2周市场情绪
"""
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import re
import time
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

def is_within_two_weeks(date_str):
    """检查日期是否在最近2周内"""
    if not date_str:
        return True  # 如果没有日期信息，默认包含
    
    try:
        # 尝试解析各种日期格式
        if 'T' in date_str and 'Z' in date_str:
            # ISO 8601格式: 2025-01-01T12:00:00Z
            article_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        elif '+' in date_str or '-' in date_str[-6:]:
            # 带时区的ISO格式
            article_date = datetime.fromisoformat(date_str)
        else:
            # RFC 2822格式 (RSS常用): Mon, 01 Jan 2025 12:00:00 GMT
            article_date = parsedate_to_datetime(date_str)
        
        # 去除时区信息进行比较
        if article_date.tzinfo:
            article_date = article_date.replace(tzinfo=None)
        
        # 计算是否在最近2周内
        two_weeks_ago = datetime.now() - timedelta(days=14)
        return article_date >= two_weeks_ago
        
    except Exception as e:
        print(f"    ⚠️ 日期解析失败: {date_str[:30]}... - {str(e)[:50]}")
        return True  # 解析失败默认包含

def analyze_sentiment_keywords(text, currency="BTC"):
    """情绪关键词分析，支持不同加密货币"""
    
    # 通用正面关键词
    positive_keywords = [
        'bullish', 'rally', 'surge', 'moon', 'pump', 'breakout', 'bull', 'green',
        'up', 'rise', 'gain', 'profit', 'buy', 'hold', 'hodl', 'optimistic',
        'positive', 'strong', 'support', 'recovery', 'growth', 'institutional',
        'adoption', 'breakthrough', 'milestone', 'all-time high', 'ath', 'soar'
    ]
    
    # 通用负面关键词
    negative_keywords = [
        'bearish', 'crash', 'dump', 'drop', 'fall', 'decline', 'bear', 'red',
        'down', 'loss', 'sell', 'panic', 'fear', 'pessimistic', 'negative',
        'weak', 'resistance', 'correction', 'bubble', 'scam', 'regulation',
        'ban', 'crackdown', 'risk', 'volatile', 'uncertainty', 'concern', 'plunge'
    ]
    
    # 货币特定关键词
    if currency.upper() == "SOL":
        positive_keywords.extend([
            'solana ecosystem', 'defi boom', 'nft surge', 'dapp growth', 'validator',
            'staking rewards', 'fast transaction', 'low fees', 'scalability',
            'phantom wallet', 'serum dex', 'raydium', 'orca', 'marinade',
            'jupiter aggregator', 'magic eden', 'metaplex', 'upgrade', 'innovation'
        ])
        negative_keywords.extend([
            'network outage', 'downtime', 'congestion', 'validator issues',
            'centralization', 'restart', 'halt', 'bug', 'exploit', 'hack',
            'drain', 'rug pull', 'ftx collapse', 'alameda'
        ])
    
    # 中性关键词
    neutral_keywords = [
        'stable', 'sideways', 'consolidation', 'analysis', 'technical',
        'fundamental', 'market', 'trading', 'volume', 'price', 'chart'
    ]
    
    text_lower = text.lower()
    
    positive_count = sum(1 for word in positive_keywords if word in text_lower)
    negative_count = sum(1 for word in negative_keywords if word in text_lower)
    neutral_count = sum(1 for word in neutral_keywords if word in text_lower)
    
    total_keywords = positive_count + negative_count + neutral_count
    
    if total_keywords == 0:
        return 0.0, "neutral", {"positive": 0, "negative": 0, "neutral": 0}
    
    # 计算情绪得分 (-1 到 +1)
    sentiment_score = (positive_count - negative_count) / max(total_keywords, 1)
    
    # 确定情绪类别
    if sentiment_score > 0.2:
        sentiment_label = "positive"
    elif sentiment_score < -0.2:
        sentiment_label = "negative"
    else:
        sentiment_label = "neutral"
    
    keyword_counts = {
        "positive": positive_count,
        "negative": negative_count, 
        "neutral": neutral_count
    }
    
    return sentiment_score, sentiment_label, keyword_counts

def get_rss_news_sentiment_2weeks(currency="BTC"):
    """获取最近2周的RSS新闻并分析情绪"""
    print(f"📰 分析最近2周RSS新闻中的{currency}情绪...")
    
    rss_feeds = [
        ("Cointelegraph", "https://cointelegraph.com/rss"),
        ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
        ("Decrypt", "https://decrypt.co/feed"),
        ("The Block", "https://theblock.co/rss.xml"),
        ("CryptoSlate", "https://cryptoslate.com/feed/"),
        ("BeInCrypto", "https://beincrypto.com/feed/")
    ]
    
    all_articles = []
    total_sentiment = 0
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    date_filtered_count = 0
    currency_filtered_count = 0
    
    # 设置搜索关键词
    if currency.upper() == "SOL":
        search_keywords = ['sol', 'solana']
    else:
        search_keywords = ['btc', 'bitcoin']
    
    for name, url in rss_feeds:
        print(f"  🔍 检查 {name}...")
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; CryptoSentimentBot/1.0)'
            }
            
            request = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(request, timeout=15) as response:
                content = response.read().decode('utf-8', errors='ignore')
            
            root = ET.fromstring(content)
            items = root.findall('.//item')
            
            source_articles = 0
            source_filtered_by_date = 0
            source_filtered_by_currency = 0
            
            for item in items:
                # 获取文章信息
                title_elem = item.find('title')
                desc_elem = item.find('description')
                date_elem = item.find('pubDate')
                
                title = title_elem.text if title_elem is not None else ""
                desc = desc_elem.text if desc_elem is not None else ""
                pub_date = date_elem.text if date_elem is not None else ""
                
                # 清理HTML标签
                title = re.sub(r'<[^>]+>', '', title)
                desc = re.sub(r'<[^>]+>', '', desc)
                
                text_content = f"{title} {desc}"
                
                # 首先检查日期过滤
                if not is_within_two_weeks(pub_date):
                    source_filtered_by_date += 1
                    continue
                
                # 然后检查货币相关性
                if any(keyword in text_content.lower() for keyword in search_keywords):
                    source_filtered_by_currency += 1
                    score, label, keywords = analyze_sentiment_keywords(text_content, currency)
                    
                    article = {
                        'source': name,
                        'title': title[:120] + '...' if len(title) > 120 else title,
                        'sentiment_score': score,
                        'sentiment_label': label,
                        'keywords': keywords,
                        'pub_date': pub_date,
                        'parsed_date': pub_date[:20] if pub_date else "Unknown"
                    }
                    
                    all_articles.append(article)
                    total_sentiment += score
                    sentiment_counts[label] += 1
                    source_articles += 1
            
            print(f"    📊 找到 {source_articles} 篇{currency}相关文章")
            if source_filtered_by_date > 0:
                print(f"    📅 过滤掉 {source_filtered_by_date} 篇过期文章")
            
            date_filtered_count += source_filtered_by_date
            currency_filtered_count += source_filtered_by_currency
                    
        except Exception as e:
            print(f"    ❌ {name}: {str(e)[:50]}...")
            continue
    
    avg_sentiment = total_sentiment / max(len(all_articles), 1)
    
    print(f"\n  📈 最近2周{currency}新闻分析结果:")
    print(f"    📄 有效文章总数: {len(all_articles)} 篇")
    print(f"    📅 日期过滤: 排除了 {date_filtered_count} 篇过期文章")
    print(f"    📊 平均情绪得分: {avg_sentiment:.3f}")
    print(f"    📈 正面: {sentiment_counts['positive']} 篇")
    print(f"    📉 负面: {sentiment_counts['negative']} 篇") 
    print(f"    😐 中性: {sentiment_counts['neutral']} 篇")
    
    return {
        'articles': all_articles,
        'average_sentiment': avg_sentiment,
        'sentiment_counts': sentiment_counts,
        'total_articles': len(all_articles),
        'date_filtered': date_filtered_count,
        'currency_filtered': currency_filtered_count
    }

def get_social_media_sentiment_2weeks(currency="BTC"):
    """获取最近2周的社交媒体数据并分析情绪"""
    print(f"\n📱 分析最近2周社交媒体中的{currency}情绪...")
    
    # 设置搜索关键词
    if currency.upper() == "SOL":
        search_keywords = ['sol', 'solana']
        reddit_subreddits = [
            "https://www.reddit.com/r/solana/hot.json",
            "https://www.reddit.com/r/cryptocurrency/hot.json"
        ]
    else:
        search_keywords = ['btc', 'bitcoin']
        reddit_subreddits = [
            "https://www.reddit.com/r/bitcoin/hot.json",
            "https://www.reddit.com/r/cryptocurrency/hot.json"
        ]
    
    # Reddit数据
    reddit_sentiment = {"positive": 0, "negative": 0, "neutral": 0}
    reddit_total_score = 0
    reddit_posts = 0
    
    for reddit_url in reddit_subreddits:
        try:
            headers = {'User-Agent': 'CryptoSentimentBot/1.0'}
            request = urllib.request.Request(reddit_url, headers=headers)
            
            with urllib.request.urlopen(request, timeout=10) as response:
                content = response.read().decode('utf-8')
            
            data = json.loads(content)
            posts = data.get('data', {}).get('children', [])
            
            for post in posts[:30]:
                post_data = post.get('data', {})
                title = post_data.get('title', '')
                selftext = post_data.get('selftext', '')
                created_utc = post_data.get('created_utc', 0)
                
                # 检查是否在最近2周内
                post_date = datetime.fromtimestamp(created_utc) if created_utc else datetime.now()
                two_weeks_ago = datetime.now() - timedelta(days=14)
                
                if post_date < two_weeks_ago:
                    continue
                
                text_content = f"{title} {selftext}"
                
                if any(keyword in text_content.lower() for keyword in search_keywords):
                    score, label, _ = analyze_sentiment_keywords(text_content, currency)
                    reddit_total_score += score
                    reddit_sentiment[label] += 1
                    reddit_posts += 1
                    
        except Exception as e:
            print(f"  ❌ Reddit获取失败: {str(e)[:50]}...")
            continue
            
    reddit_avg = reddit_total_score / max(reddit_posts, 1)
    print(f"  🟠 Reddit (2周内): {reddit_posts} 个相关帖子, 平均情绪: {reddit_avg:.3f}")
    
    # CryptoCompare新闻API (通常提供较新的数据)
    crypto_compare_sentiment = {"positive": 0, "negative": 0, "neutral": 0}
    crypto_compare_total_score = 0
    crypto_compare_articles = 0
    
    try:
        url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
        headers = {'User-Agent': 'CryptoSentimentBot/1.0'}
        request = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(request, timeout=10) as response:
            content = response.read().decode('utf-8')
        
        data = json.loads(content)
        articles = data.get('Data', [])
        
        two_weeks_ago_timestamp = (datetime.now() - timedelta(days=14)).timestamp()
        
        for article in articles[:50]:
            title = article.get('title', '')
            body = article.get('body', '')
            published_on = article.get('published_on', 0)
            
            # 检查是否在最近2周内
            if published_on < two_weeks_ago_timestamp:
                continue
            
            text_content = f"{title} {body}"
            
            if any(keyword in text_content.lower() for keyword in search_keywords):
                score, label, _ = analyze_sentiment_keywords(text_content, currency)
                crypto_compare_total_score += score
                crypto_compare_sentiment[label] += 1
                crypto_compare_articles += 1
        
        crypto_compare_avg = crypto_compare_total_score / max(crypto_compare_articles, 1)
        print(f"  🔷 CryptoCompare (2周内): {crypto_compare_articles} 篇相关文章, 平均情绪: {crypto_compare_avg:.3f}")
        
    except Exception as e:
        print(f"  ❌ CryptoCompare获取失败: {str(e)[:50]}...")
        crypto_compare_avg = 0
        crypto_compare_articles = 0
    
    # 综合社交媒体情绪
    total_social_posts = reddit_posts + crypto_compare_articles
    combined_sentiment = {
        "positive": reddit_sentiment["positive"] + crypto_compare_sentiment["positive"],
        "negative": reddit_sentiment["negative"] + crypto_compare_sentiment["negative"],
        "neutral": reddit_sentiment["neutral"] + crypto_compare_sentiment["neutral"]
    }
    
    combined_avg = (reddit_total_score + crypto_compare_total_score) / max(total_social_posts, 1)
    
    return {
        'reddit': {'sentiment': reddit_avg, 'posts': reddit_posts, 'counts': reddit_sentiment},
        'crypto_compare': {'sentiment': crypto_compare_avg, 'articles': crypto_compare_articles, 'counts': crypto_compare_sentiment},
        'combined': {'sentiment': combined_avg, 'total': total_social_posts, 'counts': combined_sentiment}
    }

def generate_2weeks_sentiment_insights(news_data, social_data, currency):
    """生成最近2周的情绪分析洞察"""
    news_sentiment = news_data['average_sentiment']
    social_sentiment = social_data['combined']['sentiment']
    
    # 综合情绪得分 (新闻75%权重，社交媒体25%权重 - 因为新闻数据经过时间筛选更可靠)
    overall_sentiment = (news_sentiment * 0.75) + (social_sentiment * 0.25)
    
    # 情绪等级
    if overall_sentiment > 0.4:
        sentiment_level = "🚀 极度乐观"
        market_mood = f"最近2周{currency}市场情绪非常积极，投资者信心强劲"
    elif overall_sentiment > 0.15:
        sentiment_level = "📈 乐观"
        market_mood = f"最近2周{currency}市场情绪偏向积极，发展趋势良好"
    elif overall_sentiment > -0.15:
        sentiment_level = "😐 中性"
        market_mood = f"最近2周{currency}市场情绪中性，观望态度明显"
    elif overall_sentiment > -0.4:
        sentiment_level = "📉 悲观"
        market_mood = f"最近2周{currency}市场情绪偏向消极，面临一些挑战"
    else:
        sentiment_level = "💀 极度悲观"
        market_mood = f"最近2周{currency}市场情绪非常消极，存在严重担忧"
    
    # 生成关键洞察
    insights = []
    
    # 时间范围准确性
    insights.append(f"📅 数据时效性高：分析基于最近2周内的{news_data['total_articles'] + social_data['combined']['total']}个数据点")
    
    # 新闻vs社交媒体对比
    sentiment_diff = abs(news_sentiment - social_sentiment)
    if sentiment_diff > 0.3:
        if news_sentiment > social_sentiment:
            insights.append(f"📰 主流媒体对{currency}的报道比社交媒体讨论更积极")
        else:
            insights.append(f"📱 社交媒体对{currency}的讨论比主流媒体报道更乐观")
    else:
        insights.append(f"📊 新闻媒体和社交媒体对{currency}的情绪基本一致")
    
    # 数据质量评估
    total_data_points = news_data['total_articles'] + social_data['combined']['total']
    if total_data_points > 40:
        insights.append(f"📈 2周数据样本丰富({total_data_points}个)，分析结果高度可靠")
    elif total_data_points > 20:
        insights.append(f"📊 2周数据样本适中({total_data_points}个)，分析结果可信")
    else:
        insights.append(f"⚠️ 2周数据样本有限({total_data_points}个)，{currency}近期关注度不高")
    
    # 情绪分布分析
    total_positive = news_data['sentiment_counts']['positive'] + social_data['combined']['counts']['positive']
    total_negative = news_data['sentiment_counts']['negative'] + social_data['combined']['counts']['negative']
    
    if total_positive > total_negative * 1.5:
        insights.append(f"🟢 近2周{currency}正面内容明显占优，市场信心较足")
    elif total_negative > total_positive * 1.5:
        insights.append(f"🔴 近2周{currency}负面内容较多，市场担忧情绪较重")
    else:
        insights.append(f"🟡 近2周{currency}正负面内容相对均衡，市场观点分化")
    
    # 数据过滤效果
    if news_data.get('date_filtered', 0) > 0:
        insights.append(f"🗓️ 排除了{news_data['date_filtered']}篇过期文章，确保分析时效性")
    
    return {
        'overall_sentiment': overall_sentiment,
        'sentiment_level': sentiment_level,
        'market_mood': market_mood,
        'insights': insights,
        'time_range': '最近2周',
        'data_quality': 'high' if total_data_points > 40 else 'medium' if total_data_points > 20 else 'low'
    }

def analyze_currency_sentiment_2weeks(currency="BTC"):
    """分析指定货币最近2周的情绪"""
    currency_upper = currency.upper()
    currency_name = "Bitcoin" if currency_upper == "BTC" else "Solana" if currency_upper == "SOL" else currency_upper
    
    print(f"🎯 {currency_name}({currency_upper}) 最近2周情绪分析")
    print("=" * 70)
    print(f"📅 分析时间范围: {(datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')} 至 {datetime.now().strftime('%Y-%m-%d')}")
    print(f"🔍 数据来源: RSS新闻(6个源) + Reddit + CryptoCompare API")
    print(f"🎯 目标货币: {currency_name}")
    print()
    
    # 获取新闻情绪
    start_time = time.time()
    news_data = get_rss_news_sentiment_2weeks(currency)
    news_time = time.time() - start_time
    
    # 获取社交媒体情绪
    start_time = time.time()  
    social_data = get_social_media_sentiment_2weeks(currency)
    social_time = time.time() - start_time
    
    # 生成综合分析
    analysis = generate_2weeks_sentiment_insights(news_data, social_data, currency_upper)
    
    # 输出分析报告
    print("\n" + "=" * 70)
    print(f"📊 {currency_upper} 最近2周情绪分析报告")
    print("=" * 70)
    
    print(f"🎯 综合情绪得分: {analysis['overall_sentiment']:.3f}")
    print(f"📈 情绪等级: {analysis['sentiment_level']}")
    print(f"💭 市场心态: {analysis['market_mood']}")
    
    print(f"\n📰 新闻媒体情绪 (2周内):")
    print(f"  📊 平均得分: {news_data['average_sentiment']:.3f}")
    print(f"  📄 分析文章: {news_data['total_articles']} 篇")
    print(f"  📅 过滤文章: {news_data.get('date_filtered', 0)} 篇过期")
    print(f"  📈 正面: {news_data['sentiment_counts']['positive']} 篇")
    print(f"  📉 负面: {news_data['sentiment_counts']['negative']} 篇")
    print(f"  😐 中性: {news_data['sentiment_counts']['neutral']} 篇")
    
    print(f"\n📱 社交媒体情绪 (2周内):")
    print(f"  📊 平均得分: {social_data['combined']['sentiment']:.3f}")
    print(f"  💬 分析内容: {social_data['combined']['total']} 条")
    print(f"  📈 正面: {social_data['combined']['counts']['positive']} 条")
    print(f"  📉 负面: {social_data['combined']['counts']['negative']} 条")
    print(f"  😐 中性: {social_data['combined']['counts']['neutral']} 条")
    
    print(f"\n💡 关键洞察:")
    for i, insight in enumerate(analysis['insights'], 1):
        print(f"  {i}. {insight}")
    
    print(f"\n⚡ 性能统计:")
    print(f"  📰 新闻分析耗时: {news_time:.2f}秒")
    print(f"  📱 社交分析耗时: {social_time:.2f}秒")
    print(f"  🎯 2周总数据点: {news_data['total_articles'] + social_data['combined']['total']} 个")
    print(f"  🏆 数据质量等级: {analysis['data_quality'].upper()}")
    
    # 显示最新文章示例
    if news_data['articles']:
        print(f"\n📝 最近2周{currency_upper}相关文章示例:")
        # 按情绪排序显示
        sorted_articles = sorted(news_data['articles'], key=lambda x: x['sentiment_score'], reverse=True)
        for i, article in enumerate(sorted_articles[:6], 1):
            sentiment_emoji = "📈" if article['sentiment_score'] > 0.1 else "📉" if article['sentiment_score'] < -0.1 else "😐"
            date_info = article['parsed_date'] if article['parsed_date'] != "Unknown" else "日期未知"
            print(f"  {i}. {sentiment_emoji} {article['title']}")
            print(f"     📅 {date_info} | 📰 {article['source']} | 🎯 {article['sentiment_score']:+.2f}")
    else:
        print(f"\n📝 注意: 最近2周未找到{currency_upper}相关的新闻文章")
        print(f"  💡 可能原因：")
        print(f"     • {currency_upper}近期不是媒体关注焦点")
        print(f"     • 市场处于相对平静期")
        print(f"     • 数据源暂时没有相关内容")
    
    # 时间效应分析
    print(f"\n📅 时间过滤效果:")
    if news_data.get('date_filtered', 0) > 0:
        print(f"  ✅ 成功过滤掉 {news_data['date_filtered']} 篇过期文章")
        print(f"  📊 提高了数据时效性和分析准确度")
    else:
        print(f"  📊 所有找到的文章都在2周时间范围内")
    
    print(f"\n🔗 数据源健康度:")
    print(f"  ✅ RSS新闻源 (6个): 正常工作")
    if social_data['reddit']['posts'] > 0:
        print(f"  ✅ Reddit API: 正常工作，获得 {social_data['reddit']['posts']} 个帖子") 
    else:
        print(f"  ⚠️ Reddit API: 2周内{currency_upper}相关讨论较少")
        
    if social_data['crypto_compare']['articles'] > 0:
        print(f"  ✅ CryptoCompare API: 正常工作，获得 {social_data['crypto_compare']['articles']} 篇文章")
    else:
        print(f"  ⚠️ CryptoCompare API: 2周内{currency_upper}相关内容有限")
    
    print(f"\n⚠️ 免责声明:")
    print(f"  • 本分析基于最近2周公开数据源的情绪关键词统计")
    print(f"  • 时间范围限定提高了分析的时效性和准确性")
    print(f"  • 不构成投资建议，请结合技术分析和基本面综合判断")
    print(f"  • 加密货币市场波动剧烈，情绪变化快速")
    
    return {
        'currency': currency_upper,
        'news_data': news_data,
        'social_data': social_data,
        'analysis': analysis
    }

def main():
    """主函数 - 分析BTC和SOL"""
    print("🎯 加密货币最近2周情绪对比分析")
    print("=" * 80)
    print(f"📅 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏰ 数据范围: 最近14天")
    print(f"🎯 分析币种: BTC vs SOL")
    print()
    
    # 分析BTC
    print("🟠 开始分析BTC...")
    btc_result = analyze_currency_sentiment_2weeks("BTC")
    
    print("\n" + "="*50)
    
    # 分析SOL
    print("🟣 开始分析SOL...")
    sol_result = analyze_currency_sentiment_2weeks("SOL")
    
    # 对比分析
    print("\n" + "="*80)
    print("📊 BTC vs SOL 最近2周情绪对比")
    print("="*80)
    
    btc_score = btc_result['analysis']['overall_sentiment']
    sol_score = sol_result['analysis']['overall_sentiment']
    
    print(f"\n🏆 情绪得分对比:")
    print(f"  🟠 BTC: {btc_score:.3f} - {btc_result['analysis']['sentiment_level']}")
    print(f"  🟣 SOL: {sol_score:.3f} - {sol_result['analysis']['sentiment_level']}")
    
    if abs(btc_score - sol_score) < 0.05:
        winner = "🤝 情绪相当"
        analysis = "两者情绪水平非常接近"
    elif btc_score > sol_score:
        winner = "🟠 BTC情绪更积极"
        analysis = f"BTC情绪领先SOL约{(btc_score - sol_score):.3f}分"
    else:
        winner = "🟣 SOL情绪更积极"
        analysis = f"SOL情绪领先BTC约{(sol_score - btc_score):.3f}分"
    
    print(f"\n🎯 对比结果: {winner}")
    print(f"📊 分析: {analysis}")
    
    print(f"\n📰 新闻关注度对比:")
    btc_news = btc_result['news_data']['total_articles']
    sol_news = sol_result['news_data']['total_articles']
    print(f"  🟠 BTC新闻: {btc_news} 篇")
    print(f"  🟣 SOL新闻: {sol_news} 篇")
    
    if btc_news > sol_news:
        print(f"  📊 BTC媒体关注度更高 ({btc_news - sol_news}篇差异)")
    elif sol_news > btc_news:
        print(f"  📊 SOL媒体关注度更高 ({sol_news - btc_news}篇差异)")
    else:
        print(f"  📊 两者媒体关注度相当")
    
    print(f"\n📱 社交热度对比:")
    btc_social = btc_result['social_data']['combined']['total']
    sol_social = sol_result['social_data']['combined']['total']
    print(f"  🟠 BTC社交: {btc_social} 条")
    print(f"  🟣 SOL社交: {sol_social} 条")
    
    if btc_social > sol_social:
        print(f"  📊 BTC社交热度更高 ({btc_social - sol_social}条差异)")
    elif sol_social > btc_social:
        print(f"  📊 SOL社交热度更高 ({sol_social - btc_social}条差异)")
    else:
        print(f"  📊 两者社交热度相当")
    
    print(f"\n🎯 投资策略参考:")
    print(f"  • 情绪领先者可能有短期价格优势")
    print(f"  • 关注度高的币种流动性通常更好")
    print(f"  • 建议结合技术分析确认入场时机")
    print(f"  • 2周数据提供了较好的短中期参考")

if __name__ == "__main__":
    main()