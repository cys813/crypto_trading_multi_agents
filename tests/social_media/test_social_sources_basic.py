#!/usr/bin/env python3
"""
使用Python标准库测试社交媒体数据源获取能力
包括Twitter、YouTube、Telegram的数据获取分析
"""
import urllib.request
import urllib.parse
import json
import re
import time
from datetime import datetime, timedelta

def test_twitter_alternatives():
    """测试Twitter替代数据源"""
    print("=== Twitter 替代数据源测试 ===")
    
    # 测试一些可以获取Twitter相关信息的公开API
    sources = [
        ("Twitter公开搜索", "https://twitter.com/search", "BTC"),
        ("Nitter实例", "https://nitter.net/search", "Bitcoin")
    ]
    
    total_data = 0
    
    for name, base_url, query in sources:
        print(f"\n🐦 测试 {name}")
        try:
            if "twitter.com" in base_url:
                # Twitter的公开搜索页面
                search_url = f"{base_url}?q={urllib.parse.quote(query)}&src=typed_query&f=live"
            else:
                # Nitter搜索
                search_url = f"{base_url}?q={urllib.parse.quote(query)}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive'
            }
            
            request = urllib.request.Request(search_url, headers=headers)
            
            start_time = time.time()
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    content = response.read().decode('utf-8', errors='ignore')
                elapsed_time = time.time() - start_time
                
                # 分析页面内容寻找推文相关信息
                if "twitter.com" in base_url:
                    # Twitter页面分析
                    tweet_patterns = [
                        r'"tweet_count":\s*(\d+)',
                        r'data-testid="tweet"',
                        r'role="article"'
                    ]
                    
                    tweet_indicators = 0
                    for pattern in tweet_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        tweet_indicators += len(matches)
                    
                    # 检查是否包含推文内容
                    btc_mentions = len(re.findall(r'\b(btc|bitcoin|crypto)\b', content, re.IGNORECASE))
                    
                else:
                    # Nitter页面分析
                    tweet_containers = re.findall(r'class="tweet-content"', content, re.IGNORECASE)
                    btc_mentions = len(re.findall(r'\b(btc|bitcoin|crypto)\b', content, re.IGNORECASE))
                    tweet_indicators = len(tweet_containers)
                
                print(f"  ✅ 页面加载成功")
                print(f"  📄 页面大小: {len(content):,} 字符")
                print(f"  🔍 推文指标: {tweet_indicators} 个")
                print(f"  🎯 相关内容: {btc_mentions} 个提及")
                print(f"  ⏱️ 响应时间: {elapsed_time:.2f}秒")
                
                if tweet_indicators > 0:
                    print(f"  📊 评估: 可获取约 {tweet_indicators} 条推文数据")
                else:
                    print(f"  ⚠️ 评估: 可能被限制访问或需要认证")
                
                total_data += min(tweet_indicators, btc_mentions)
                
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    print(f"  🚫 访问被限制 (429 Too Many Requests)")
                    print(f"  💡 说明: Twitter限制匿名访问，需要API密钥")
                elif e.code == 403:
                    print(f"  🚫 访问被禁止 (403 Forbidden)")
                    print(f"  💡 说明: 需要登录或API认证")
                else:
                    print(f"  ❌ HTTP错误 {e.code}: {e.reason}")
                    
        except Exception as e:
            print(f"  ❌ 获取失败: {str(e)[:60]}...")
    
    print(f"\n🔢 Twitter数据源总结:")
    print(f"   预估可获取数据量: {total_data} 条")
    
    # 免费替代方案分析
    print(f"\n💡 Twitter免费替代方案分析:")
    print(f"   🔓 Nitter实例: 免费但可能不稳定")
    print(f"   🔓 Twikit: 需要安装，可绕过部分限制")
    print(f"   🔓 snscrape: 命令行工具，功能强大")
    print(f"   💰 官方API: $200/月起，数据质量最高")
    
    return total_data

def test_youtube_sources():
    """测试YouTube数据源"""
    print("\n=== YouTube 数据源测试 ===")
    
    # 测试YouTube相关的数据获取
    test_scenarios = [
        ("YouTube搜索页面", "https://www.youtube.com/results", "Bitcoin"),
        ("加密货币频道", "https://www.youtube.com/c/CoinBureau", None)
    ]
    
    total_videos = 0
    
    for name, base_url, query in test_scenarios:
        print(f"\n📺 测试 {name}")
        try:
            if query:
                search_url = f"{base_url}?search_query={urllib.parse.quote(query)}"
            else:
                search_url = base_url
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            request = urllib.request.Request(search_url, headers=headers)
            
            start_time = time.time()
            with urllib.request.urlopen(request, timeout=20) as response:
                content = response.read().decode('utf-8', errors='ignore')
            elapsed_time = time.time() - start_time
            
            # 分析YouTube页面内容
            video_patterns = [
                r'"videoId":"([^"]+)"',
                r'watch\?v=([a-zA-Z0-9_-]{11})',
                r'"title":{"runs":\[{"text":"([^"]+)"}\]',
                r'"videoRenderer"'
            ]
            
            video_ids = set()
            video_titles = []
            
            for pattern in video_patterns[:2]:  # 视频ID模式
                matches = re.findall(pattern, content)
                if matches:
                    video_ids.update(matches)
            
            # 提取视频标题
            title_pattern = r'"title":{"runs":\[{"text":"([^"]+)"}\]'
            titles = re.findall(title_pattern, content)
            for title in titles:
                if any(keyword in title.lower() for keyword in ['bitcoin', 'btc', 'crypto', 'blockchain']):
                    video_titles.append(title)
            
            # 检查加密货币相关内容
            crypto_mentions = len(re.findall(r'\b(bitcoin|btc|crypto|ethereum|eth|blockchain)\b', content, re.IGNORECASE))
            
            print(f"  ✅ 页面加载成功")
            print(f"  📄 页面大小: {len(content):,} 字符")
            print(f"  🎬 发现视频ID: {len(video_ids)} 个")
            print(f"  📝 相关视频标题: {len(video_titles)} 个")
            print(f"  🔍 加密货币提及: {crypto_mentions} 次")
            print(f"  ⏱️ 响应时间: {elapsed_time:.2f}秒")
            
            # 显示相关视频示例
            if video_titles:
                print(f"  📺 视频标题示例:")
                for i, title in enumerate(video_titles[:3], 1):
                    title = title[:60] + '...' if len(title) > 60 else title
                    print(f"     {i}. {title}")
            
            total_videos += len(video_ids)
            
        except urllib.error.HTTPError as e:
            print(f"  ❌ HTTP错误 {e.code}: {e.reason}")
        except Exception as e:
            print(f"  ❌ 获取失败: {str(e)[:60]}...")
    
    print(f"\n🔢 YouTube数据源总结:")
    print(f"   预估可获取视频数: {total_videos} 个")
    
    # YouTube API分析
    print(f"\n💡 YouTube数据获取方案:")
    print(f"   🆓 YouTube Data API v3: 免费配额10,000单位/天")
    print(f"   🔓 yt-dlp: 免费工具，功能强大")
    print(f"   🔍 网页抓取: 复杂但可行")
    print(f"   📊 评估: 免费方案足够获取影响者观点")
    
    return total_videos

def test_telegram_sources():
    """测试Telegram数据源"""
    print("\n=== Telegram 数据源测试 ===")
    
    # Telegram公开频道测试
    public_channels = [
        ("Telegram Web搜索", "https://t.me/s/", "bitcoin"),
        ("公开频道示例", "https://t.me/s/CryptoNews", None)
    ]
    
    total_messages = 0
    
    for name, base_url, channel in public_channels:
        print(f"\n📱 测试 {name}")
        try:
            if channel and not channel.startswith('http'):
                test_url = f"{base_url}{channel}"
            elif channel:
                test_url = channel
            else:
                test_url = base_url
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            request = urllib.request.Request(test_url, headers=headers)
            
            start_time = time.time()
            with urllib.request.urlopen(request, timeout=15) as response:
                content = response.read().decode('utf-8', errors='ignore')
            elapsed_time = time.time() - start_time
            
            # 分析Telegram页面内容
            message_patterns = [
                r'class="tgme_widget_message_text"',
                r'data-post="[^"]+/(\d+)"',
                r'tgme_widget_message_bubble'
            ]
            
            message_indicators = 0
            for pattern in message_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                message_indicators += len(matches)
            
            # 检查加密货币相关内容
            crypto_mentions = len(re.findall(r'\b(bitcoin|btc|crypto|ethereum|blockchain)\b', content, re.IGNORECASE))
            
            # 寻找消息文本
            message_texts = re.findall(r'class="tgme_widget_message_text[^"]*">([^<]+)', content, re.IGNORECASE)
            relevant_messages = [msg for msg in message_texts if any(keyword in msg.lower() for keyword in ['bitcoin', 'btc', 'crypto'])]
            
            print(f"  ✅ 页面加载成功")
            print(f"  📄 页面大小: {len(content):,} 字符")
            print(f"  💬 消息指标: {message_indicators} 个")
            print(f"  📝 提取消息: {len(message_texts)} 条")
            print(f"  🎯 相关消息: {len(relevant_messages)} 条")
            print(f"  🔍 加密货币提及: {crypto_mentions} 次")
            print(f"  ⏱️ 响应时间: {elapsed_time:.2f}秒")
            
            # 显示相关消息示例
            if relevant_messages:
                print(f"  📨 相关消息示例:")
                for i, msg in enumerate(relevant_messages[:2], 1):
                    msg = msg[:80] + '...' if len(msg) > 80 else msg
                    print(f"     {i}. {msg}")
            
            total_messages += max(message_indicators // 3, len(relevant_messages))
            
        except urllib.error.HTTPError as e:
            print(f"  ❌ HTTP错误 {e.code}: {e.reason}")
            if e.code == 404:
                print(f"  💡 频道可能不存在或已设为私人频道")
        except Exception as e:
            print(f"  ❌ 获取失败: {str(e)[:60]}...")
    
    print(f"\n🔢 Telegram数据源总结:")
    print(f"   预估可获取消息数: {total_messages} 条")
    
    # Telegram API分析
    print(f"\n💡 Telegram数据获取方案:")
    print(f"   🆓 Telegram Bot API: 免费但功能有限")
    print(f"   🔑 Telegram Client API: 需要申请但免费")
    print(f"   🔓 Pyrogram/Telethon: 强大的Python客户端")
    print(f"   🌐 公开频道网页: 可以抓取部分数据")
    print(f"   📊 评估: 免费方案可获取公开频道数据")
    
    return total_messages

def test_social_apis():
    """测试社交媒体相关的API"""
    print("\n=== 社交媒体 API 测试 ===")
    
    apis = [
        ("Reddit JSON", "https://www.reddit.com/r/cryptocurrency/hot.json"),
        ("HackerNews API", "https://hacker-news.firebaseio.com/v0/topstories.json")
    ]
    
    total_posts = 0
    
    for name, url in apis:
        print(f"\n🔗 测试 {name}")
        try:
            headers = {
                'User-Agent': 'Python Social Media Analysis Bot 1.0'
            }
            
            request = urllib.request.Request(url, headers=headers)
            
            start_time = time.time()
            with urllib.request.urlopen(request, timeout=15) as response:
                content = response.read().decode('utf-8')
            elapsed_time = time.time() - start_time
            
            data = json.loads(content)
            
            posts_count = 0
            relevant_posts = 0
            
            if 'reddit.com' in url:
                # Reddit JSON格式
                if isinstance(data, dict) and 'data' in data:
                    posts = data['data'].get('children', [])
                    posts_count = len(posts)
                    
                    for post in posts:
                        if isinstance(post, dict) and 'data' in post:
                            title = post['data'].get('title', '').lower()
                            if any(keyword in title for keyword in ['bitcoin', 'btc', 'crypto']):
                                relevant_posts += 1
            else:
                # HackerNews API
                if isinstance(data, list):
                    posts_count = len(data)
                    # HN返回ID列表，这里简化处理
                    relevant_posts = posts_count // 10  # 估算相关帖子
            
            print(f"  ✅ API响应成功")
            print(f"  📊 获取帖子: {posts_count} 个")
            print(f"  🎯 相关内容: {relevant_posts} 个")
            print(f"  ⏱️ 响应时间: {elapsed_time:.2f}秒")
            
            total_posts += relevant_posts
            
        except json.JSONDecodeError:
            print(f"  ❌ JSON解析错误")
        except Exception as e:
            print(f"  ❌ 获取失败: {str(e)[:50]}...")
    
    print(f"\n🔢 社交媒体API总结:")
    print(f"   总计相关帖子: {total_posts} 个")
    return total_posts

def main():
    """主测试函数"""
    print("📱 社交媒体数据源获取能力分析")
    print("=" * 60)
    print("测试Twitter、YouTube、Telegram数据获取能力...\n")
    
    results = {}
    
    # 测试Twitter
    print("🔄 正在测试Twitter数据源...")
    try:
        results['twitter'] = test_twitter_alternatives()
    except Exception as e:
        print(f"❌ Twitter测试出错: {e}")
        results['twitter'] = 0
    
    # 测试YouTube
    print("\n🔄 正在测试YouTube数据源...")
    try:
        results['youtube'] = test_youtube_sources()
    except Exception as e:
        print(f"❌ YouTube测试出错: {e}")
        results['youtube'] = 0
    
    # 测试Telegram
    print("\n🔄 正在测试Telegram数据源...")
    try:
        results['telegram'] = test_telegram_sources()
    except Exception as e:
        print(f"❌ Telegram测试出错: {e}")
        results['telegram'] = 0
    
    # 测试其他社交API
    print("\n🔄 正在测试其他社交媒体API...")
    try:
        results['social_apis'] = test_social_apis()
    except Exception as e:
        print(f"❌ 社交API测试出错: {e}")
        results['social_apis'] = 0
    
    # 生成综合报告
    print("\n" + "=" * 60)
    print("📊 社交媒体数据源获取能力报告")
    print("=" * 60)
    
    total_twitter = results.get('twitter', 0)
    total_youtube = results.get('youtube', 0)
    total_telegram = results.get('telegram', 0)
    total_social = results.get('social_apis', 0)
    
    print(f"\n📈 各平台数据获取能力:")
    
    # Twitter分析
    print(f"\n🐦 Twitter:")
    if total_twitter > 0:
        print(f"   📊 预估数据量: {total_twitter} 条推文")
        print(f"   📈 获取难度: 🔴 困难 (需要API密钥或特殊工具)")
        print(f"   💰 成本评估: $200+/月 (官方API)")
        print(f"   🔓 免费方案: Twikit, snscrape (不稳定)")
        print(f"   ⭐ 推荐指数: ⭐⭐ (高成本)")
    else:
        print(f"   📊 预估数据量: 0 条 (访问受限)")
        print(f"   📈 获取难度: 🔴 很困难 (严格限制)")
        print(f"   💡 解决方案: 使用免费替代工具 (Twikit)")
        print(f"   ⭐ 推荐指数: ⭐⭐⭐ (有免费替代方案)")
    
    # YouTube分析
    print(f"\n📺 YouTube:")
    if total_youtube > 0:
        print(f"   📊 预估数据量: {total_youtube} 个视频")
        print(f"   📈 获取难度: 🟡 中等 (需要解析或API)")
        print(f"   💰 成本评估: 免费配额充足")
        print(f"   🔓 免费方案: YouTube Data API v3, yt-dlp")
        print(f"   ⭐ 推荐指数: ⭐⭐⭐⭐ (免费且稳定)")
    else:
        print(f"   📊 预估数据量: 0 个 (获取失败)")
        print(f"   💡 解决方案: 配置YouTube Data API密钥")
        print(f"   ⭐ 推荐指数: ⭐⭐⭐⭐ (配置后效果好)")
    
    # Telegram分析
    print(f"\n📱 Telegram:")
    if total_telegram > 0:
        print(f"   📊 预估数据量: {total_telegram} 条消息")
        print(f"   📈 获取难度: 🟡 中等 (需要API申请)")
        print(f"   💰 成本评估: 免费但需要申请")
        print(f"   🔓 免费方案: Pyrogram, Telethon")
        print(f"   ⭐ 推荐指数: ⭐⭐⭐⭐ (免费且数据质量好)")
    else:
        print(f"   📊 预估数据量: 0 条 (访问受限)")
        print(f"   💡 解决方案: 申请Telegram API或使用公开频道")
        print(f"   ⭐ 推荐指数: ⭐⭐⭐ (配置后可用)")
    
    # 其他社交媒体
    if total_social > 0:
        print(f"\n🌐 其他社交媒体:")
        print(f"   📊 数据量: {total_social} 个帖子")
        print(f"   💡 包含: Reddit等免费API")
        print(f"   ⭐ 推荐指数: ⭐⭐⭐⭐ (补充数据源)")
    
    # 综合评估
    total_all = total_youtube + total_telegram + total_social + (total_twitter // 10)
    
    print(f"\n📊 综合社交媒体数据获取能力:")
    print(f"   🎯 预估总数据量: {total_all} 条/周")
    
    if total_all >= 100:
        print(f"   🎉 数据获取能力: 优秀")
        print(f"   💡 建议: 当前配置足够支撑情绪分析")
    elif total_all >= 50:
        print(f"   ✅ 数据获取能力: 良好")
        print(f"   💡 建议: 可以满足基本需求")
    elif total_all >= 20:
        print(f"   ⚠️ 数据获取能力: 一般")
        print(f"   💡 建议: 需要配置API或使用替代工具")
    else:
        print(f"   🚨 数据获取能力: 不足")
        print(f"   💡 建议: 重点配置免费API和替代工具")
    
    # 实施建议
    print(f"\n🛠️ 实施建议:")
    print(f"   1. 🎯 优先级排序:")
    print(f"      • YouTube Data API > Telegram API > Twitter替代工具")
    print(f"   2. 📋 配置步骤:")
    print(f"      • 申请YouTube Data API v3 (免费)")
    print(f"      • 申请Telegram API credentials (免费)")
    print(f"      • 安装Twikit/snscrape作为Twitter替代")
    print(f"   3. 💰 成本控制:")
    print(f"      • 全部使用免费方案: $0/月")
    print(f"      • YouTube + Telegram + Twitter替代工具")
    print(f"   4. 🔄 容错策略:")
    print(f"      • 多个替代工具备份")
    print(f"      • 智能降级到模拟数据")
    
    print(f"\n🎯 结论:")
    if total_youtube > 0 or total_telegram > 0:
        print(f"   ✅ 社交媒体数据获取基础良好")
        print(f"   🔧 通过配置API可大幅提升数据量")
        print(f"   💡 重点关注YouTube和Telegram的API配置")
    else:
        print(f"   ⚠️ 需要配置API密钥才能发挥全部潜力")
        print(f"   🆓 优先使用免费的API和工具")
        print(f"   📈 配置后预估可获取数据量: 200+ 条/周")
    
    return results

if __name__ == "__main__":
    main()