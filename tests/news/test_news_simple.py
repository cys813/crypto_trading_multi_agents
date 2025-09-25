#!/usr/bin/env python3
"""
简化的新闻源测试，不依赖项目的其他模块
直接测试各个新闻API的数据获取能力
"""
import time
from datetime import datetime, timedelta

def test_rss_feeds():
    """测试RSS Feeds"""
    print("=== RSS Feeds 测试 ===")
    
    try:
        import feedparser
    except ImportError:
        print("❌ feedparser 库未安装，尝试安装...")
        import subprocess
        subprocess.check_call(["pip", "install", "feedparser"])
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
        print(f"\n📰 测试 {name}")
        try:
            start_time = time.time()
            feed = feedparser.parse(rss_url)
            elapsed_time = time.time() - start_time
            
            if hasattr(feed, 'entries') and feed.entries:
                # 筛选与BTC相关的文章
                relevant_articles = []
                for entry in feed.entries[:50]:  # 检查前50篇
                    title = entry.get('title', '')
                    summary = entry.get('summary', '')
                    text_content = f"{title} {summary}"
                    
                    if any(keyword in text_content.lower() for keyword in ['btc', 'bitcoin', 'crypto']):
                        relevant_articles.append({
                            'title': title,
                            'published': entry.get('published', ''),
                            'link': entry.get('link', '')
                        })
                
                print(f"  ✅ 成功连接")
                print(f"  📄 总文章数: {len(feed.entries)}")
                print(f"  🎯 {currency}相关: {len(relevant_articles)} 篇")
                print(f"  ⏱️ 响应时间: {elapsed_time:.2f}秒")
                
                if relevant_articles:
                    print(f"  📝 最新相关文章:")
                    for i, article in enumerate(relevant_articles[:2], 1):
                        title = article['title'][:80] + '...' if len(article['title']) > 80 else article['title']
                        print(f"     {i}. {title}")
                
                total_articles += len(relevant_articles)
                
            else:
                print(f"  ❌ 未获取到文章或Feed格式错误")
                
        except Exception as e:
            print(f"  ❌ 连接失败: {str(e)}")
    
    print(f"\n🔢 RSS Feeds 总结:")
    print(f"   总计 {currency} 相关文章: {total_articles} 篇")
    return total_articles

def test_gnews():
    """测试GNews"""
    print("\n=== GNews 测试 ===")
    
    try:
        from gnews import GNews
    except ImportError:
        print("❌ gnews 库未安装，尝试安装...")
        import subprocess
        subprocess.check_call(["pip", "install", "gnews"])
        from gnews import GNews
    
    search_terms = ["Bitcoin", "BTC", "cryptocurrency"]
    total_articles = 0
    
    for term in search_terms:
        print(f"\n🔍 搜索关键词: {term}")
        try:
            gnews = GNews(
                language='en',
                country='US',
                period='7d',
                max_results=30
            )
            
            start_time = time.time()
            articles = gnews.get_news(term)
            elapsed_time = time.time() - start_time
            
            if articles:
                print(f"  ✅ 找到 {len(articles)} 篇文章")
                print(f"  ⏱️ 响应时间: {elapsed_time:.2f}秒")
                
                # 显示文章来源统计
                publishers = {}
                for article in articles:
                    pub = article.get('publisher', {})
                    pub_name = pub.get('title', 'Unknown') if isinstance(pub, dict) else str(pub)
                    publishers[pub_name] = publishers.get(pub_name, 0) + 1
                
                print(f"  📰 主要来源:")
                for pub, count in sorted(publishers.items(), key=lambda x: x[1], reverse=True)[:3]:
                    print(f"     {pub}: {count} 篇")
                
                # 显示最新文章
                print(f"  📝 最新文章:")
                for i, article in enumerate(articles[:2], 1):
                    title = article.get('title', 'No title')
                    title = title[:80] + '...' if len(title) > 80 else title
                    print(f"     {i}. {title}")
                
                total_articles += len(articles)
            else:
                print(f"  ❌ 未找到相关文章")
                
        except Exception as e:
            print(f"  ❌ 搜索失败: {str(e)}")
    
    print(f"\n🔢 GNews 总结:")
    print(f"   总计获取文章: {total_articles} 篇")
    return total_articles

def test_basic_web_scraping():
    """测试基本的网页抓取"""
    print("\n=== 基本网页抓取测试 ===")
    
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("❌ requests 或 beautifulsoup4 未安装，尝试安装...")
        import subprocess
        subprocess.check_call(["pip", "install", "requests", "beautifulsoup4"])
        import requests
        from bs4 import BeautifulSoup
    
    # 测试抓取CoinDesk的Bitcoin页面
    urls = [
        ("CoinDesk Bitcoin", "https://www.coindesk.com/tag/bitcoin/"),
        ("CoinTelegraph Bitcoin", "https://cointelegraph.com/tags/bitcoin")
    ]
    
    total_articles = 0
    
    for name, url in urls:
        print(f"\n🌐 测试 {name}")
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=10)
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 尝试找到文章标题（这是一个简化的例子）
                article_titles = []
                
                # 常见的文章标题选择器
                selectors = ['h2', 'h3', '.title', '.headline', 'article h2', 'article h3']
                
                for selector in selectors:
                    elements = soup.select(selector)
                    if elements and len(elements) > 5:  # 如果找到足够多的元素
                        article_titles = [elem.get_text().strip() for elem in elements[:20]]
                        break
                
                print(f"  ✅ 页面加载成功")
                print(f"  📄 找到可能的文章标题: {len(article_titles)} 个")
                print(f"  ⏱️ 响应时间: {elapsed_time:.2f}秒")
                print(f"  📊 状态码: {response.status_code}")
                
                if article_titles:
                    print(f"  📝 示例标题:")
                    for i, title in enumerate(article_titles[:3], 1):
                        title = title[:80] + '...' if len(title) > 80 else title
                        print(f"     {i}. {title}")
                
                total_articles += len(article_titles)
                
            else:
                print(f"  ❌ HTTP错误: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ 抓取失败: {str(e)}")
    
    print(f"\n🔢 网页抓取总结:")
    print(f"   总计找到标题: {total_articles} 个")
    return total_articles

def test_news_apis():
    """测试需要API密钥的新闻服务"""
    print("\n=== API新闻服务测试 ===")
    
    # NewsAPI测试
    print("\n📡 NewsAPI 测试")
    try:
        from newsapi import NewsApiClient
    except ImportError:
        print("❌ newsapi-python 库未安装，尝试安装...")
        import subprocess
        subprocess.check_call(["pip", "install", "newsapi-python"])
        from newsapi import NewsApiClient
    
    import os
    api_key = os.getenv("NEWS_API_KEY", "")
    
    if api_key:
        try:
            newsapi = NewsApiClient(api_key=api_key)
            
            # 测试搜索
            response = newsapi.get_everything(
                q="Bitcoin",
                from_param=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                language='en',
                sort_by='relevancy',
                page_size=20
            )
            
            if response['status'] == 'ok':
                articles = response['articles']
                print(f"  ✅ NewsAPI 工作正常")
                print(f"  📄 获取文章: {len(articles)} 篇")
                print(f"  🔢 总结果数: {response.get('totalResults', 'Unknown')}")
                return len(articles)
            else:
                print(f"  ❌ NewsAPI 错误: {response.get('message')}")
                return 0
                
        except Exception as e:
            print(f"  ❌ NewsAPI 调用失败: {str(e)}")
            return 0
    else:
        print("  ⚠️ NewsAPI 密钥未配置 (设置 NEWS_API_KEY 环境变量)")
        return 0

def main():
    """主测试函数"""
    print("📰 新闻数据源详细分析")
    print("=" * 60)
    print("测试各个新闻源的数据获取能力...\n")
    
    results = {}
    
    # 测试RSS Feeds
    print("🔄 正在测试RSS Feeds...")
    try:
        results['rss_feeds'] = test_rss_feeds()
    except Exception as e:
        print(f"❌ RSS Feeds 测试出错: {e}")
        results['rss_feeds'] = 0
    
    # 测试GNews
    print("\n🔄 正在测试GNews...")
    try:
        results['gnews'] = test_gnews()
    except Exception as e:
        print(f"❌ GNews 测试出错: {e}")
        results['gnews'] = 0
    
    # 测试网页抓取
    print("\n🔄 正在测试网页抓取...")
    try:
        results['web_scraping'] = test_basic_web_scraping()
    except Exception as e:
        print(f"❌ 网页抓取测试出错: {e}")
        results['web_scraping'] = 0
    
    # 测试API服务
    print("\n🔄 正在测试API服务...")
    try:
        results['news_apis'] = test_news_apis()
    except Exception as e:
        print(f"❌ API服务测试出错: {e}")
        results['news_apis'] = 0
    
    # 总结报告
    print("\n" + "=" * 60)
    print("📊 新闻数据源分析报告")
    print("=" * 60)
    
    total_articles = sum(v for v in results.values() if isinstance(v, int))
    
    print(f"\n📈 各数据源获取能力:")
    if results.get('rss_feeds', 0) > 0:
        print(f"  🟢 RSS Feeds: {results['rss_feeds']} 篇相关文章")
        print(f"     推荐指数: ⭐⭐⭐⭐⭐ (免费、稳定、内容质量高)")
    else:
        print(f"  🔴 RSS Feeds: 获取失败")
    
    if results.get('gnews', 0) > 0:
        print(f"  🟢 GNews: {results['gnews']} 篇文章")
        print(f"     推荐指数: ⭐⭐⭐⭐ (免费、易用、覆盖面广)")
    else:
        print(f"  🔴 GNews: 获取失败")
    
    if results.get('web_scraping', 0) > 0:
        print(f"  🟡 网页抓取: {results['web_scraping']} 个标题")
        print(f"     推荐指数: ⭐⭐⭐ (免费但可能不稳定)")
    else:
        print(f"  🔴 网页抓取: 获取失败")
    
    if results.get('news_apis', 0) > 0:
        print(f"  🟢 NewsAPI: {results['news_apis']} 篇文章")
        print(f"     推荐指数: ⭐⭐⭐⭐ (高质量但需要API密钥)")
    else:
        print(f"  🔴 NewsAPI: 未配置或获取失败")
    
    print(f"\n📊 汇总统计:")
    print(f"   总计可获取文章数: {total_articles} 篇")
    
    # 给出建议
    print(f"\n💡 建议:")
    if results.get('rss_feeds', 0) >= 20:
        print(f"  ✅ RSS Feeds 表现优秀，建议作为主要数据源")
    if results.get('gnews', 0) >= 10:
        print(f"  ✅ GNews 可靠，建议作为重要补充")
    if results.get('news_apis', 0) == 0:
        print(f"  💰 考虑配置 NewsAPI 以获得更高质量的数据")
    
    if total_articles >= 50:
        print(f"\n🎉 新闻数据源配置优秀！数据获取能力强")
        print(f"   系统可以获得充足的新闻数据进行情绪分析")
    elif total_articles >= 20:
        print(f"\n✅ 新闻数据源配置良好，基本满足需求")
        print(f"   建议进一步优化以获得更多数据")
    elif total_articles >= 5:
        print(f"\n⚠️ 新闻数据源配置一般，数据量偏少")
        print(f"   建议检查网络连接和添加更多数据源")
    else:
        print(f"\n🚨 新闻数据源存在问题，建议检查配置")
        print(f"   可能的原因：网络连接、API限制、库未安装")
    
    return results

if __name__ == "__main__":
    main()