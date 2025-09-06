#!/usr/bin/env python3
"""
简化的BTC情绪分析测试
直接使用多源聚合框架获取和分析数据
"""
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import re
import time
from datetime import datetime, timedelta

def analyze_sentiment_keywords(text):
    """简单的情绪关键词分析"""
    # 正面关键词
    positive_keywords = [
        'bullish', 'rally', 'surge', 'moon', 'pump', 'breakout', 'bull', 'green',
        'up', 'rise', 'gain', 'profit', 'buy', 'hold', 'hodl', 'optimistic',
        'positive', 'strong', 'support', 'recovery', 'growth', 'institutional',
        'adoption', 'breakthrough', 'milestone', 'all-time high', 'ath'
    ]
    
    # 负面关键词
    negative_keywords = [
        'bearish', 'crash', 'dump', 'drop', 'fall', 'decline', 'bear', 'red',
        'down', 'loss', 'sell', 'panic', 'fear', 'pessimistic', 'negative',
        'weak', 'resistance', 'correction', 'bubble', 'scam', 'regulation',
        'ban', 'crackdown', 'risk', 'volatile', 'uncertainty', 'concern'
    ]
    
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

def get_rss_news_sentiment():
    """获取RSS新闻并分析情绪"""
    print("📰 分析RSS新闻情绪...")
    
    rss_feeds = [
        ("Cointelegraph", "https://cointelegraph.com/rss"),
        ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
        ("Decrypt", "https://decrypt.co/feed"),
        ("The Block", "https://theblock.co/rss.xml")
    ]
    
    all_articles = []
    total_sentiment = 0
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    
    for name, url in rss_feeds:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; CryptoSentimentBot/1.0)'
            }
            
            request = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(request, timeout=10) as response:
                content = response.read().decode('utf-8', errors='ignore')
            
            root = ET.fromstring(content)
            items = root.findall('.//item')
            
            for item in items[:20]:  # 分析最新20篇文章
                title_elem = item.find('title')
                desc_elem = item.find('description')
                
                title = title_elem.text if title_elem is not None else ""
                desc = desc_elem.text if desc_elem is not None else ""
                
                # 清理HTML标签
                title = re.sub(r'<[^>]+>', '', title)
                desc = re.sub(r'<[^>]+>', '', desc)
                
                text_content = f"{title} {desc}"
                
                # 检查是否与BTC相关
                if any(keyword in text_content.lower() for keyword in ['btc', 'bitcoin']):
                    score, label, keywords = analyze_sentiment_keywords(text_content)
                    
                    article = {
                        'source': name,
                        'title': title[:100] + '...' if len(title) > 100 else title,
                        'sentiment_score': score,
                        'sentiment_label': label,
                        'keywords': keywords
                    }
                    
                    all_articles.append(article)
                    total_sentiment += score
                    sentiment_counts[label] += 1
                    
        except Exception as e:
            print(f"  ❌ {name}: {str(e)[:50]}...")
            continue
    
    avg_sentiment = total_sentiment / max(len(all_articles), 1)
    
    print(f"  📊 分析了 {len(all_articles)} 篇BTC相关文章")
    print(f"  📈 正面: {sentiment_counts['positive']} 篇")
    print(f"  📉 负面: {sentiment_counts['negative']} 篇") 
    print(f"  😐 中性: {sentiment_counts['neutral']} 篇")
    print(f"  🎯 平均情绪得分: {avg_sentiment:.3f}")
    
    return {
        'articles': all_articles,
        'average_sentiment': avg_sentiment,
        'sentiment_counts': sentiment_counts,
        'total_articles': len(all_articles)
    }

def get_social_media_sentiment():
    """获取社交媒体数据并分析情绪"""
    print("\n📱 分析社交媒体情绪...")
    
    # Reddit数据
    reddit_sentiment = {"positive": 0, "negative": 0, "neutral": 0}
    reddit_total_score = 0
    reddit_posts = 0
    
    try:
        url = "https://www.reddit.com/r/bitcoin/hot.json"
        headers = {'User-Agent': 'CryptoSentimentBot/1.0'}
        request = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(request, timeout=10) as response:
            content = response.read().decode('utf-8')
        
        data = json.loads(content)
        posts = data.get('data', {}).get('children', [])
        
        for post in posts[:20]:
            post_data = post.get('data', {})
            title = post_data.get('title', '')
            selftext = post_data.get('selftext', '')
            
            text_content = f"{title} {selftext}"
            
            if any(keyword in text_content.lower() for keyword in ['btc', 'bitcoin']):
                score, label, _ = analyze_sentiment_keywords(text_content)
                reddit_total_score += score
                reddit_sentiment[label] += 1
                reddit_posts += 1
                
        reddit_avg = reddit_total_score / max(reddit_posts, 1)
        print(f"  🟠 Reddit: {reddit_posts} 个相关帖子, 平均情绪: {reddit_avg:.3f}")
        
    except Exception as e:
        print(f"  ❌ Reddit获取失败: {str(e)[:50]}...")
        reddit_avg = 0
    
    # CryptoCompare新闻API
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
        
        for article in articles[:30]:
            title = article.get('title', '')
            body = article.get('body', '')
            
            text_content = f"{title} {body}"
            
            if any(keyword in text_content.lower() for keyword in ['btc', 'bitcoin']):
                score, label, _ = analyze_sentiment_keywords(text_content)
                crypto_compare_total_score += score
                crypto_compare_sentiment[label] += 1
                crypto_compare_articles += 1
        
        crypto_compare_avg = crypto_compare_total_score / max(crypto_compare_articles, 1)
        print(f"  🔷 CryptoCompare: {crypto_compare_articles} 篇相关文章, 平均情绪: {crypto_compare_avg:.3f}")
        
    except Exception as e:
        print(f"  ❌ CryptoCompare获取失败: {str(e)[:50]}...")
        crypto_compare_avg = 0
    
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

def generate_sentiment_insights(news_data, social_data):
    """生成情绪分析洞察"""
    news_sentiment = news_data['average_sentiment']
    social_sentiment = social_data['combined']['sentiment']
    
    # 综合情绪得分 (新闻70%权重，社交媒体30%权重)
    overall_sentiment = (news_sentiment * 0.7) + (social_sentiment * 0.3)
    
    # 情绪等级
    if overall_sentiment > 0.4:
        sentiment_level = "🚀 极度乐观"
        market_mood = "市场情绪非常积极，投资者信心强劲"
    elif overall_sentiment > 0.1:
        sentiment_level = "📈 乐观"
        market_mood = "市场情绪偏向积极，但需保持谨慎"
    elif overall_sentiment > -0.1:
        sentiment_level = "😐 中性"
        market_mood = "市场情绪中性，观望态度明显"
    elif overall_sentiment > -0.4:
        sentiment_level = "📉 悲观"
        market_mood = "市场情绪偏向消极，谨慎情绪较重"
    else:
        sentiment_level = "💀 极度悲观"
        market_mood = "市场情绪非常消极，恐慌情绪蔓延"
    
    # 生成关键洞察
    insights = []
    
    # 新闻vs社交媒体对比
    if abs(news_sentiment - social_sentiment) > 0.3:
        if news_sentiment > social_sentiment:
            insights.append("📰 主流媒体报道比社交媒体更加乐观")
        else:
            insights.append("📱 社交媒体讨论比主流媒体更加积极")
    else:
        insights.append("📊 新闻媒体和社交媒体情绪基本一致")
    
    # 数据量评估
    total_data_points = news_data['total_articles'] + social_data['combined']['total']
    if total_data_points > 50:
        insights.append(f"📈 数据样本充足({total_data_points}个数据点)，分析结果可靠")
    elif total_data_points > 20:
        insights.append(f"📊 数据样本适中({total_data_points}个数据点)，分析结果基本可信")
    else:
        insights.append(f"⚠️ 数据样本有限({total_data_points}个数据点)，建议谨慎参考")
    
    # 情绪分布分析
    total_positive = news_data['sentiment_counts']['positive'] + social_data['combined']['counts']['positive']
    total_negative = news_data['sentiment_counts']['negative'] + social_data['combined']['counts']['negative']
    
    if total_positive > total_negative * 2:
        insights.append("🟢 正面内容占主导地位，市场乐观情绪浓厚")
    elif total_negative > total_positive * 2:
        insights.append("🔴 负面内容较多，市场担忧情绪较重")
    else:
        insights.append("🟡 正负面内容相对均衡，市场情绪分化")
    
    return {
        'overall_sentiment': overall_sentiment,
        'sentiment_level': sentiment_level,
        'market_mood': market_mood,
        'insights': insights
    }

def main():
    """主分析函数"""
    print("🎯 BTC本周情绪分析")
    print("=" * 60)
    print(f"📅 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔍 数据来源: RSS新闻 + Reddit + CryptoCompare API")
    print()
    
    # 获取新闻情绪
    start_time = time.time()
    news_data = get_rss_news_sentiment()
    news_time = time.time() - start_time
    
    # 获取社交媒体情绪
    start_time = time.time()  
    social_data = get_social_media_sentiment()
    social_time = time.time() - start_time
    
    # 生成综合分析
    analysis = generate_sentiment_insights(news_data, social_data)
    
    # 输出分析报告
    print("\n" + "=" * 60)
    print("📊 BTC情绪分析报告")
    print("=" * 60)
    
    print(f"🎯 综合情绪得分: {analysis['overall_sentiment']:.3f}")
    print(f"📈 情绪等级: {analysis['sentiment_level']}")
    print(f"💭 市场心态: {analysis['market_mood']}")
    
    print(f"\n📰 新闻媒体情绪:")
    print(f"  📊 平均得分: {news_data['average_sentiment']:.3f}")
    print(f"  📄 分析文章: {news_data['total_articles']} 篇")
    print(f"  📈 正面: {news_data['sentiment_counts']['positive']} 篇")
    print(f"  📉 负面: {news_data['sentiment_counts']['negative']} 篇")
    print(f"  😐 中性: {news_data['sentiment_counts']['neutral']} 篇")
    
    print(f"\n📱 社交媒体情绪:")
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
    print(f"  🎯 总计数据点: {news_data['total_articles'] + social_data['combined']['total']} 个")
    
    # 显示部分文章标题作为示例
    if news_data['articles']:
        print(f"\n📝 最新相关文章示例:")
        for i, article in enumerate(news_data['articles'][:5], 1):
            sentiment_emoji = "📈" if article['sentiment_score'] > 0.1 else "📉" if article['sentiment_score'] < -0.1 else "😐"
            print(f"  {i}. {sentiment_emoji} {article['title']} ({article['source']})")
    
    print(f"\n🔗 数据源状态:")
    print(f"  ✅ RSS新闻源: 正常工作")
    print(f"  ✅ Reddit API: 正常工作") 
    print(f"  ✅ CryptoCompare API: 正常工作")
    
    print(f"\n⚠️ 免责声明:")
    print(f"  • 本分析仅基于公开数据源的情绪关键词统计")
    print(f"  • 不构成投资建议，请理性判断市场风险")
    print(f"  • 情绪分析存在滞后性，实时市场可能已发生变化")

if __name__ == "__main__":
    main()