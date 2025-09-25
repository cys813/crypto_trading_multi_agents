#!/usr/bin/env python3
"""
使用Python标准库测试新闻源获取能力
不需要安装额外依赖
"""
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import re
import time
from datetime import datetime

def test_rss_feeds_basic():
    """使用标准库测试RSS feeds"""
    print("=== RSS Feeds 基础测试 ===")
    
    rss_feeds = [
        ("Cointelegraph", "https://cointelegraph.com/rss"),
        ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
        ("Decrypt", "https://decrypt.co/feed"),
        ("The Block", "https://theblock.co/rss.xml"),
        ("CryptoSlate", "https://cryptoslate.com/feed/"),
    ]
    
    total_articles = 0
    currency_keywords = ['btc', 'bitcoin', 'crypto', 'cryptocurrency', 'blockchain']
    
    for name, url in rss_feeds:
        print(f"\n📰 测试 {name}")
        try:
            # 设置请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; NewsBot/1.0)',
                'Accept': 'application/rss+xml, application/xml, text/xml'
            }
            
            # 创建请求
            request = urllib.request.Request(url, headers=headers)
            
            start_time = time.time()
            with urllib.request.urlopen(request, timeout=15) as response:
                content = response.read().decode('utf-8', errors='ignore')
            elapsed_time = time.time() - start_time
            
            # 解析XML
            try:
                root = ET.fromstring(content)
            except ET.ParseError as e:
                print(f"  ❌ XML解析错误: {str(e)[:50]}...")
                continue
            
            # 查找文章项目
            items = []
            
            # RSS 2.0 格式
            rss_items = root.findall('.//item')
            if rss_items:
                items = rss_items
            else:
                # Atom 格式
                atom_entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')
                if atom_entries:
                    items = atom_entries
            
            if items:
                relevant_count = 0
                total_count = len(items)
                
                # 检查相关文章
                for item in items[:50]:  # 检查前50个项目
                    title_elem = item.find('title')
                    desc_elem = item.find('description') or item.find('{http://www.w3.org/2005/Atom}summary')
                    
                    title = title_elem.text if title_elem is not None and title_elem.text else ""
                    desc = desc_elem.text if desc_elem is not None and desc_elem.text else ""
                    
                    # 清理HTML标签
                    title = re.sub(r'<[^>]+>', '', title)
                    desc = re.sub(r'<[^>]+>', '', desc)
                    
                    text_content = f"{title} {desc}".lower()
                    
                    if any(keyword in text_content for keyword in currency_keywords):
                        relevant_count += 1
                
                print(f"  ✅ 成功获取")
                print(f"  📄 总文章数: {total_count}")
                print(f"  🎯 加密货币相关: {relevant_count} 篇")
                print(f"  ⏱️ 响应时间: {elapsed_time:.2f}秒")
                
                # 显示最新标题示例
                if relevant_count > 0:
                    print(f"  📝 示例标题:")
                    count = 0
                    for item in items[:20]:
                        if count >= 2:
                            break
                        title_elem = item.find('title')
                        if title_elem is not None and title_elem.text:
                            title = re.sub(r'<[^>]+>', '', title_elem.text)
                            if any(keyword in title.lower() for keyword in currency_keywords):
                                title = title[:70] + '...' if len(title) > 70 else title
                                print(f"     • {title}")
                                count += 1
                
                total_articles += relevant_count
            else:
                print(f"  ⚠️ 未找到文章项目")
                
        except urllib.error.HTTPError as e:
            print(f"  ❌ HTTP错误 {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            print(f"  ❌ 连接错误: {str(e)}")
        except Exception as e:
            print(f"  ❌ 其他错误: {str(e)[:50]}...")
    
    print(f"\n🔢 RSS Feeds 总结:")
    print(f"   总计加密货币相关文章: {total_articles} 篇")
    return total_articles

def test_web_pages_basic():
    """测试基本网页内容获取"""
    print("\n=== 网页内容基础测试 ===")
    
    urls = [
        ("CoinDesk Bitcoin页面", "https://www.coindesk.com/tag/bitcoin/"),
        ("Cointelegraph", "https://cointelegraph.com/"),
    ]
    
    total_content = 0
    
    for name, url in urls:
        print(f"\n🌐 测试 {name}")
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            request = urllib.request.Request(url, headers=headers)
            
            start_time = time.time()
            with urllib.request.urlopen(request, timeout=15) as response:
                content = response.read().decode('utf-8', errors='ignore')
            elapsed_time = time.time() - start_time
            
            # 简单分析页面内容
            bitcoin_mentions = len(re.findall(r'\bbitcoin\b', content, re.IGNORECASE))
            crypto_mentions = len(re.findall(r'\bcrypt[o|a]\w*', content, re.IGNORECASE))
            btc_mentions = len(re.findall(r'\bbtc\b', content, re.IGNORECASE))
            
            # 寻找可能的标题
            title_patterns = [
                r'<h[1-3][^>]*>([^<]+)</h[1-3]>',
                r'<title[^>]*>([^<]+)</title>',
                r'"title":\s*"([^"]+)"'
            ]
            
            titles_found = []
            for pattern in title_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                titles_found.extend(matches)
                if len(titles_found) >= 10:
                    break
            
            print(f"  ✅ 页面加载成功")
            print(f"  📄 页面大小: {len(content):,} 字符")
            print(f"  🔍 Bitcoin提及: {bitcoin_mentions} 次")
            print(f"  🔍 Crypto相关: {crypto_mentions} 次")
            print(f"  🔍 BTC提及: {btc_mentions} 次")
            print(f"  📝 找到标题: {len(titles_found)} 个")
            print(f"  ⏱️ 响应时间: {elapsed_time:.2f}秒")
            
            # 显示一些标题示例
            if titles_found:
                print(f"  📰 标题示例:")
                for i, title in enumerate(titles_found[:3], 1):
                    clean_title = re.sub(r'[^\w\s-]', '', title).strip()
                    if len(clean_title) > 10:
                        clean_title = clean_title[:60] + '...' if len(clean_title) > 60 else clean_title
                        print(f"     {i}. {clean_title}")
            
            total_content += bitcoin_mentions + crypto_mentions + btc_mentions
            
        except Exception as e:
            print(f"  ❌ 获取失败: {str(e)[:50]}...")
    
    print(f"\n🔢 网页内容总结:")
    print(f"   总计加密货币相关内容: {total_content} 个提及")
    return total_content

def test_json_apis():
    """测试一些提供JSON数据的免费API"""
    print("\n=== JSON API 基础测试 ===")
    
    apis = [
        ("CoinGecko新闻", "https://api.coingecko.com/api/v3/news"),
        ("CryptoCompare新闻", "https://min-api.cryptocompare.com/data/v2/news/?lang=EN")
    ]
    
    total_articles = 0
    
    for name, url in apis:
        print(f"\n🔗 测试 {name}")
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; CryptoBot/1.0)',
                'Accept': 'application/json'
            }
            
            request = urllib.request.Request(url, headers=headers)
            
            start_time = time.time()
            with urllib.request.urlopen(request, timeout=15) as response:
                content = response.read().decode('utf-8')
            elapsed_time = time.time() - start_time
            
            # 解析JSON
            data = json.loads(content)
            
            article_count = 0
            if isinstance(data, dict):
                if 'Data' in data and isinstance(data['Data'], list):
                    # CryptoCompare格式
                    article_count = len(data['Data'])
                    articles = data['Data']
                elif 'data' in data and isinstance(data['data'], list):
                    # 其他格式
                    article_count = len(data['data'])
                    articles = data['data']
                elif isinstance(data.get('results'), list):
                    article_count = len(data['results'])
                    articles = data['results']
                else:
                    articles = []
            elif isinstance(data, list):
                article_count = len(data)
                articles = data
            else:
                articles = []
            
            print(f"  ✅ API响应成功")
            print(f"  📄 获取文章: {article_count} 篇")
            print(f"  ⏱️ 响应时间: {elapsed_time:.2f}秒")
            
            # 显示示例文章
            if articles and len(articles) > 0:
                print(f"  📰 文章示例:")
                for i, article in enumerate(articles[:3], 1):
                    if isinstance(article, dict):
                        title = article.get('title', article.get('Title', 'No Title'))
                        source = article.get('source', article.get('source_info', {}).get('name', 'Unknown'))
                        if isinstance(source, dict):
                            source = source.get('name', 'Unknown')
                        
                        title = title[:60] + '...' if len(str(title)) > 60 else str(title)
                        print(f"     {i}. {title} - {source}")
            
            total_articles += article_count
            
        except json.JSONDecodeError:
            print(f"  ❌ JSON解析错误")
        except urllib.error.HTTPError as e:
            print(f"  ❌ HTTP错误 {e.code}: {e.reason}")
        except Exception as e:
            print(f"  ❌ 获取失败: {str(e)[:50]}...")
    
    print(f"\n🔢 JSON API总结:")
    print(f"   总计获取文章: {total_articles} 篇")
    return total_articles

def main():
    """主测试函数"""
    print("📰 新闻数据源基础分析")
    print("=" * 60)
    print("使用Python标准库测试各个新闻源...\n")
    
    results = {}
    
    # 测试RSS feeds
    print("🔄 正在测试RSS Feeds...")
    try:
        results['rss_feeds'] = test_rss_feeds_basic()
    except Exception as e:
        print(f"❌ RSS测试出错: {e}")
        results['rss_feeds'] = 0
    
    # 测试网页内容
    print("\n🔄 正在测试网页内容...")
    try:
        results['web_pages'] = test_web_pages_basic()
    except Exception as e:
        print(f"❌ 网页测试出错: {e}")
        results['web_pages'] = 0
    
    # 测试JSON APIs
    print("\n🔄 正在测试JSON APIs...")
    try:
        results['json_apis'] = test_json_apis()
    except Exception as e:
        print(f"❌ JSON API测试出错: {e}")
        results['json_apis'] = 0
    
    # 生成报告
    print("\n" + "=" * 60)
    print("📊 新闻数据源获取能力报告")
    print("=" * 60)
    
    # 计算总数
    total_rss = results.get('rss_feeds', 0)
    total_web = results.get('web_pages', 0)
    total_json = results.get('json_apis', 0)
    
    print(f"\n📈 各数据源表现:")
    
    # RSS Feeds分析
    if total_rss > 0:
        print(f"  🟢 RSS Feeds: {total_rss} 篇相关文章")
        if total_rss >= 30:
            print(f"     评级: ⭐⭐⭐⭐⭐ 优秀 - 数据量丰富")
        elif total_rss >= 15:
            print(f"     评级: ⭐⭐⭐⭐ 良好 - 数据量适中")
        elif total_rss >= 5:
            print(f"     评级: ⭐⭐⭐ 一般 - 数据量偏少")
        else:
            print(f"     评级: ⭐⭐ 较差 - 数据量很少")
        print(f"     推荐: RSS是最稳定可靠的新闻源")
    else:
        print(f"  🔴 RSS Feeds: 无法获取数据")
        print(f"     可能原因: 网络连接问题或RSS源暂时不可用")
    
    # 网页内容分析  
    if total_web > 0:
        print(f"  🟡 网页内容: {total_web} 个相关提及")
        print(f"     评级: ⭐⭐⭐ 可用 - 需要解析处理")
        print(f"     推荐: 可作为RSS的补充数据源")
    else:
        print(f"  🔴 网页内容: 无法获取数据")
    
    # JSON API分析
    if total_json > 0:
        print(f"  🟢 JSON APIs: {total_json} 篇文章")
        if total_json >= 50:
            print(f"     评级: ⭐⭐⭐⭐⭐ 优秀 - 结构化数据")
        else:
            print(f"     评级: ⭐⭐⭐⭐ 良好 - 结构化数据")
        print(f"     推荐: 提供结构化的高质量数据")
    else:
        print(f"  🔴 JSON APIs: 无法获取数据")
    
    # 总体评估
    total_all = total_rss + (total_web // 10) + total_json  # 网页内容权重降低
    
    print(f"\n📊 综合评估:")
    print(f"   预估可获取新闻文章总数: {total_all} 篇/周")
    
    if total_all >= 50:
        print(f"   🎉 新闻数据获取能力: 优秀")
        print(f"   💡 建议: 当前配置足够支撑高质量的情绪分析")
    elif total_all >= 25:
        print(f"   ✅ 新闻数据获取能力: 良好") 
        print(f"   💡 建议: 基本满足需求，可考虑添加更多源")
    elif total_all >= 10:
        print(f"   ⚠️ 新闻数据获取能力: 一般")
        print(f"   💡 建议: 需要优化配置或添加付费API")
    else:
        print(f"   🚨 新闻数据获取能力: 不足")
        print(f"   💡 建议: 检查网络连接，考虑使用付费API")
    
    # 实施建议
    print(f"\n🛠️ 实施建议:")
    if total_rss > 0:
        print(f"   1. ✅ RSS Feeds 优先 - 稳定可靠的主要数据源")
    if total_json > 0:
        print(f"   2. ✅ JSON APIs 补充 - 结构化数据质量高") 
    
    print(f"   3. 📦 多源聚合策略:")
    print(f"      • RSS Feeds 作为主要数据源 (70%权重)")
    print(f"      • JSON APIs 作为补充数据源 (20%权重)") 
    print(f"      • 网页抓取作为备用数据源 (10%权重)")
    
    print(f"   4. 🎯 优化方向:")
    if total_rss < 20:
        print(f"      • 添加更多RSS源提高覆盖面")
    if total_json == 0:
        print(f"      • 集成免费的JSON API (CoinGecko, CryptoCompare)")
    print(f"      • 实现智能缓存减少重复请求")
    print(f"      • 添加情绪分析和关键词过滤")
    
    return results

if __name__ == "__main__":
    main()