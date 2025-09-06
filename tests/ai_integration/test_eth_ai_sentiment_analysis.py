#!/usr/bin/env python3
"""
ETH市场情绪AI分析脚本
使用智谱AI glm-4.5-flash模型进行增强分析
"""
import sys
import os
import json
from datetime import datetime

# 添加项目路径
project_root = os.path.join(os.path.dirname(__file__), '../..')
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

# 导入项目中的LLM服务
from src.crypto_trading_agents.config.zhipuai_direct_config import get_zhipuai_direct_config
from src.crypto_trading_agents.services.llm_service import llm_service, initialize_llm_service, is_llm_service_available

# 导入所需的函数
from tests.sentiment.test_eth_sentiment_simple import get_rss_news_sentiment, get_social_media_sentiment, generate_sentiment_insights

def build_ai_prompt(news_data, social_data, analysis):
    """构建AI分析prompt"""
    prompt = f"""你是一位资深的加密货币市场分析师，请基于以下ETH市场情绪分析数据，提供专业的市场洞察和投资建议。

## 基本信息
- 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 分析对象: Ethereum (ETH)

## 情绪分析数据

### 综合情绪
- 综合情绪得分: {analysis['overall_sentiment']:.3f}
- 情绪等级: {analysis['sentiment_level']}
- 市场心态: {analysis['market_mood']}

### 新闻媒体情绪
- 平均得分: {news_data['average_sentiment']:.3f}
- 分析文章: {news_data['total_articles']} 篇
- 正面: {news_data['sentiment_counts']['positive']} 篇
- 负面: {news_data['sentiment_counts']['negative']} 篇
- 中性: {news_data['sentiment_counts']['neutral']} 篇

### 社交媒体情绪
- 平均得分: {social_data['combined']['sentiment']:.3f}
- 分析内容: {social_data['combined']['total']} 条
- 正面: {social_data['combined']['counts']['positive']} 条
- 负面: {social_data['combined']['counts']['negative']} 条
- 中性: {social_data['combined']['counts']['neutral']} 条

## 分析要求

请基于以上数据提供以下分析：

1. **市场情绪深度解读** - 分析当前ETH市场情绪的根本原因
2. **短期趋势预测** (3-7天) - 基于情绪数据预测价格走势
3. **关键风险点识别** - 指出需要关注的潜在风险
4. **投资策略建议** - 提供具体的投资操作建议

## 输出格式要求

请以JSON格式输出，包含以下字段：
- market_insight (市场洞察)
- short_term_prediction (短期预测)
- key_risks (关键风险)
- investment_strategy (投资策略)
- confidence_level (置信度，0-1之间)
- executive_summary (执行摘要)

请确保输出是有效的JSON格式，不要包含其他文本。
"""

    return prompt

def parse_ai_response(response_text):
    """解析AI响应"""
    try:
        # 尝试直接解析JSON
        if response_text.startswith('{') and response_text.endswith('}'):
            return json.loads(response_text)
        
        # 如果响应包含其他文本，尝试提取JSON部分
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        
        # 如果还是失败，返回原始响应
        return {"raw_response": response_text}
    except Exception as e:
        print(f"❌ AI响应解析失败: {e}")
        return {"error": str(e), "raw_response": response_text}

def main():
    """主分析函数"""
    print("🎯 ETH市场情绪AI分析")
    print("=" * 60)
    print("使用智谱AI glm-4.5-flash模型进行增强分析")
    print()
    
    # 1. 初始化智谱AI服务
    print("1️⃣ 初始化智谱AI服务...")
    config = get_zhipuai_direct_config()
    llm_config = config.get('llm_service_config', {})
    
    success = initialize_llm_service(llm_config)
    if not success:
        print("❌ LLM服务初始化失败")
        return
    
    if not is_llm_service_available():
        print("❌ LLM服务不可用")
        return
    
    print("✅ 智谱AI服务初始化成功")
    print(f"   模型: {llm_config['providers']['zhipuai']['model']}")
    print()
    
    # 2. 收集情绪数据
    print("2️⃣ 收集ETH情绪数据...")
    news_data = get_rss_news_sentiment()
    social_data = get_social_media_sentiment()
    analysis = generate_sentiment_insights(news_data, social_data)
    print()
    
    # 3. 构建AI分析prompt
    print("3️⃣ 构建AI分析请求...")
    prompt = build_ai_prompt(news_data, social_data, analysis)
    print(f"   Prompt长度: {len(prompt)} 字符")
    print()
    
    # 4. 调用智谱AI进行分析
    print("4️⃣ 调用智谱AI进行深度分析...")
    try:
        response = llm_service.call_llm(
            prompt,
            provider="zhipuai",
            temperature=0.1,
            max_tokens=2000
        )
        print("✅ AI分析完成")
        print()
        
        # 5. 解析AI响应
        print("5️⃣ 解析AI分析结果...")
        ai_analysis = parse_ai_response(response)
        print("✅ AI响应解析成功")
        print()
        
        # 6. 输出综合分析报告
        print("=" * 60)
        print("📊 ETH市场情绪AI分析报告")
        print("=" * 60)
        
        print(f"🎯 综合情绪得分: {analysis['overall_sentiment']:.3f}")
        print(f"📈 情绪等级: {analysis['sentiment_level']}")
        print(f"💭 市场心态: {analysis['market_mood']}")
        print()
        
        if "executive_summary" in ai_analysis:
            print("🤖 AI执行摘要:")
            print(f"   {ai_analysis['executive_summary']}")
            print()
        
        if "market_insight" in ai_analysis:
            print("🔍 市场洞察:")
            print(f"   {ai_analysis['market_insight']}")
            print()
            
        if "short_term_prediction" in ai_analysis:
            print("🔮 短期预测 (3-7天):")
            print(f"   {ai_analysis['short_term_prediction']}")
            print()
            
        if "key_risks" in ai_analysis:
            print("⚠️ 关键风险:")
            print(f"   {ai_analysis['key_risks']}")
            print()
            
        if "investment_strategy" in ai_analysis:
            print("💡 投资策略:")
            print(f"   {ai_analysis['investment_strategy']}")
            print()
            
        if "confidence_level" in ai_analysis:
            confidence = ai_analysis['confidence_level']
            print(f"📊 AI分析置信度: {confidence*100:.1f}%")
            print()
        
        # 显示原始数据摘要
        print("📋 原始数据分析:")
        print(f"   📰 新闻媒体情绪: {news_data['average_sentiment']:.3f}")
        print(f"   📱 社交媒体情绪: {social_data['combined']['sentiment']:.3f}")
        print(f"   📊 数据点总数: {news_data['total_articles'] + social_data['combined']['total']} 个")
        print()
        
        print("🔗 AI服务信息:")
        print(f"   🤖 提供商: 智谱AI")
        print(f"   🧠 模型: glm-4.5-flash")
        print()
        
        # 显示原始响应（用于调试）
        print("🔍 原始AI响应:")
        print(f"   {response[:200]}...")
        print()
        
        print("⚠️ 免责声明:")
        print("   • 本分析仅供参考，不构成投资建议")
        print("   • 加密货币市场风险极高，请谨慎投资")
        print("   • AI分析可能存在误差，请结合其他信息源")
        
    except Exception as e:
        print(f"❌ AI分析过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()