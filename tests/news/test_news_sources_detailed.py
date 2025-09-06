#!/usr/bin/env python3
"""
详细测试各个新闻源的数据获取情况
分析每个新闻源能获取到多少条数据
"""
import sys
import os
import time
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from crypto_trading_agents.default_config import DEFAULT_CONFIG

def test_rss_feeds_detailed():
    """详细测试RSS Feeds数据源"""
    print("=== RSS Feeds 详细测试 ===")
    
    try:
        import feedparser
        
        rss_feeds = [
            ("Cointelegraph", "https://cointelegraph.com/rss"),
            ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
            ("Decrypt", "https://decrypt.co/feed"),
            ("The Block", "https://theblock.co/rss.xml"),
            ("CryptoSlate", "https://cryptoslate.com/feed/"),
            ("BeInCrypto", "https://beincrypto.com/feed/")
        ]
        
        currency = "BTC"
        total_articles = 0
        
        for name, rss_url in rss_feeds:
            print(f"\n测试 {name} ({rss_url})")
            try:
                start_time = time.time()
                feed = feedparser.parse(rss_url)
                elapsed_time = time.time() - start_time
                
                if feed.entries:
                    # 筛选与BTC相关的文章
                    relevant_articles = []
                    for entry in feed.entries[:50]:  # 检查前50篇文章
                        text_content = f"{entry.get('title', '')} {entry.get('summary', '')}"
                        if any(keyword in text_content.lower() for keyword in ['btc', 'bitcoin', 'crypto']):
                            relevant_articles.append({
                                'title': entry.get('title', ''),
                                'published': entry.get('published', ''),
                                'link': entry.get('link', '')
                            })
                    
                    print(f"  ✅ 成功获取")
                    print(f"  总文章数: {len(feed.entries)}")
                    print(f"  {currency}相关文章: {len(relevant_articles)}")
                    print(f"  响应时间: {elapsed_time:.2f}秒")
                    print(f"  Feed状态: {feed.get('status', 'Unknown')}")
                    
                    # 显示最近的相关文章
                    if relevant_articles:
                        print(f"  最新相关文章:")
                        for i, article in enumerate(relevant_articles[:3], 1):
                            title = article['title'][:60] + '...' if len(article['title']) > 60 else article['title']
                            print(f"    {i}. {title}")
                    
                    total_articles += len(relevant_articles)
                else:
                    print(f"  ❌ 未获取到文章")
                    
            except Exception as e:
                print(f"  ❌ 获取失败: {str(e)}")
        
        print(f"\nRSS Feeds 总结:")
        print(f"  总计获取 {currency} 相关文章: {total_articles} 篇")
        return total_articles
        
    except ImportError:
        print("❌ feedparser 库未安装")
        return 0

def test_gnews_detailed():
    """详细测试GNews数据源"""
    print("\n=== GNews 详细测试 ===")
    
    try:
        from gnews import GNews
        
        currencies = ["BTC", "Bitcoin", "ETH", "Ethereum"]
        total_articles = 0
        
        for currency in currencies:
            print(f"\n测试搜索关键词: {currency}")
            try:
                gnews = GNews(
                    language='en',
                    country='US',
                    period='7d',
                    max_results=50
                )
                
                start_time = time.time()
                articles = gnews.get_news(currency)
                elapsed_time = time.time() - start_time
                
                if articles:
                    print(f"  ✅ 成功获取 {len(articles)} 篇文章")
                    print(f"  响应时间: {elapsed_time:.2f}秒")
                    
                    # 显示最新文章
                    print(f"  最新文章:")
                    for i, article in enumerate(articles[:3], 1):
                        title = article.get('title', 'No title')
                        title = title[:60] + '...' if len(title) > 60 else title
                        publisher = article.get('publisher', {}).get('title', 'Unknown')
                        print(f"    {i}. {title} - {publisher}")
                    
                    total_articles += len(articles)
                else:
                    print(f"  ⚠️ 未找到相关文章")
                    
            except Exception as e:
                print(f"  ❌ 搜索失败: {str(e)}")
        
        print(f"\nGNews 总结:")
        print(f"  总计获取文章: {total_articles} 篇")
        return total_articles
        
    except ImportError:
        print("❌ gnews 库未安装")
        return 0

def test_newsapi_detailed():
    """详细测试NewsAPI数据源"""
    print("\n=== NewsAPI 详细测试 ===")
    
    try:
        from newsapi import NewsApiClient
        
        api_key = DEFAULT_CONFIG.get("api_config", {}).get("news_api", {}).get("api_key", "")
        
        if not api_key:
            print("⚠️ NewsAPI 密钥未配置，跳过测试")
            return 0
        
        newsapi = NewsApiClient(api_key=api_key)
        
        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        search_terms = ["Bitcoin", "BTC", "cryptocurrency"]
        total_articles = 0
        
        for term in search_terms:
            print(f"\n测试搜索关键词: {term}")
            try:
                start_time = time.time()
                response = newsapi.get_everything(
                    q=term,
                    from_param=start_date.strftime("%Y-%m-%d"),
                    to=end_date.strftime("%Y-%m-%d"),
                    language='en',
                    sort_by='relevancy',
                    page_size=100
                )
                elapsed_time = time.time() - start_time
                
                if response['status'] == 'ok':
                    articles = response['articles']
                    print(f"  ✅ 成功获取 {len(articles)} 篇文章")
                    print(f"  响应时间: {elapsed_time:.2f}秒")
                    print(f"  总结果数: {response.get('totalResults', 'Unknown')}")
                    
                    # 按来源统计
                    sources = {}
                    for article in articles:
                        source_name = article.get('source', {}).get('name', 'Unknown')
                        sources[source_name] = sources.get(source_name, 0) + 1
                    
                    print(f"  主要新闻源:")
                    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5]:
                        print(f"    {source}: {count} 篇")
                    
                    # 显示最新文章
                    print(f"  最新文章:")
                    for i, article in enumerate(articles[:3], 1):
                        title = article.get('title', 'No title')
                        title = title[:60] + '...' if len(title) > 60 else title
                        source = article.get('source', {}).get('name', 'Unknown')
                        print(f"    {i}. {title} - {source}")
                    
                    total_articles += len(articles)
                else:
                    print(f"  ❌ API响应错误: {response.get('message', 'Unknown error')}")
                    
            except Exception as e:
                print(f"  ❌ 搜索失败: {str(e)}")
        
        print(f"\nNewsAPI 总结:")
        print(f"  总计获取文章: {total_articles} 篇")
        return total_articles
        
    except ImportError:
        print("❌ newsapi-python 库未安装")
        return 0

def test_news_source_manager():
    """测试新闻数据源管理器"""
    print("\n=== 新闻数据源管理器测试 ===")
    
    try:
        from crypto_trading_agents.agents.analysts.sentiment_analyst import NewsDataSourceManager
        
        manager = NewsDataSourceManager(DEFAULT_CONFIG)
        
        print("数据源状态:")
        status = manager.get_source_status()
        for source, info in status.items():
            available = "✅" if info['available'] else "❌"
            print(f"  {source}: {available}")
        
        print(f"\n测试数据获取...")
        start_time = time.time()
        data = manager.get_data("BTC", "2025-01-15")
        elapsed_time = time.time() - start_time
        
        print(f"✅ 获取成功")
        print(f"数据源: {data.get('_source', 'unknown')}")
        print(f"响应时间: {elapsed_time:.2f}秒")
        print(f"文章总数: {data.get('article_count', 0)}")
        print(f"正面文章: {data.get('positive_articles', 0)}")
        print(f"负面文章: {data.get('negative_articles', 0)}")
        print(f"中性文章: {data.get('neutral_articles', 0)}")
        print(f"情绪得分: {data.get('sentiment_score', 0):.3f}")
        
        return data
        
    except Exception as e:
        print(f"❌ 管理器测试失败: {str(e)}")
        return None

def analyze_news_coverage():
    """分析新闻覆盖范围"""
    print("\n=== 新闻覆盖分析 ===")
    
    # 测试不同货币的覆盖情况
    currencies = ["BTC", "ETH", "ADA", "SOL", "DOGE"]
    
    try:
        import feedparser
        
        # 使用一个主要的RSS源进行测试
        rss_url = "https://cointelegraph.com/rss"
        feed = feedparser.parse(rss_url)
        
        if feed.entries:
            print(f"分析 Cointelegraph 的货币覆盖情况:")
            
            for currency in currencies:
                count = 0
                for entry in feed.entries[:100]:  # 检查前100篇文章
                    text_content = f"{entry.get('title', '')} {entry.get('summary', '')}"
                    if currency.lower() in text_content.lower():
                        count += 1
                
                print(f"  {currency}: {count} 篇相关文章")
        
    except Exception as e:
        print(f"覆盖分析失败: {str(e)}")

def main():
    """主测试函数"""
    print("新闻数据源详细测试分析")
    print("=" * 60)
    
    results = {}
    
    # 测试RSS Feeds
    try:
        results['rss_feeds'] = test_rss_feeds_detailed()
    except Exception as e:
        print(f"RSS Feeds 测试出错: {e}")
        results['rss_feeds'] = 0
    
    # 测试GNews
    try:
        results['gnews'] = test_gnews_detailed()
    except Exception as e:
        print(f"GNews 测试出错: {e}")
        results['gnews'] = 0
    
    # 测试NewsAPI
    try:
        results['newsapi'] = test_newsapi_detailed()
    except Exception as e:
        print(f"NewsAPI 测试出错: {e}")
        results['newsapi'] = 0
    
    # 测试管理器
    try:
        manager_result = test_news_source_manager()
        results['manager'] = manager_result
    except Exception as e:
        print(f"管理器测试出错: {e}")
        results['manager'] = None
    
    # 覆盖分析
    try:
        analyze_news_coverage()
    except Exception as e:
        print(f"覆盖分析出错: {e}")
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    total_articles = sum(v for v in results.values() if isinstance(v, int))
    
    print(f"各数据源文章获取量:")
    if results.get('rss_feeds', 0) > 0:
        print(f"  RSS Feeds: {results['rss_feeds']} 篇")
    if results.get('gnews', 0) > 0:
        print(f"  GNews: {results['gnews']} 篇")
    if results.get('newsapi', 0) > 0:
        print(f"  NewsAPI: {results['newsapi']} 篇")
    
    print(f"\n总计可获取文章数: {total_articles} 篇")
    
    if results.get('manager'):
        manager_data = results['manager']
        print(f"管理器聚合结果: {manager_data.get('article_count', 0)} 篇")
    
    # 建议
    print(f"\n建议:")
    if results.get('rss_feeds', 0) > 0:
        print(f"✅ RSS Feeds 工作良好，建议作为主要数据源")
    if results.get('gnews', 0) > 0:
        print(f"✅ GNews 可用，适合作为备用数据源")
    if results.get('newsapi', 0) == 0:
        print(f"⚠️ NewsAPI 未配置或不可用，考虑添加API密钥")
    
    if total_articles > 50:
        print(f"🎉 新闻数据源运行良好，数据量充足！")
    elif total_articles > 10:
        print(f"✅ 新闻数据源基本可用，建议优化配置")
    else:
        print(f"⚠️ 新闻数据源数据量较少，建议检查网络和配置")

if __name__ == "__main__":
    main()