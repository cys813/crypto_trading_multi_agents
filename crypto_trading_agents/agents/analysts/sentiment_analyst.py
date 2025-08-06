"""
情绪分析师 - 专注加密货币市场情绪分析

分析社交媒体、新闻、社区情绪等
"""

import os
import sys
import json
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, project_root)

# 导入统一LLM服务
from ...services.ai_analysis_mixin import StandardAIAnalysisMixin
from ...services.llm_service import initialize_llm_service

logger = logging.getLogger(__name__)

class SentimentAnalyst(StandardAIAnalysisMixin):
    """加密货币情绪分析师"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化情感分析器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.sentiment_sources = config.get("analysis_config", {}).get("sentiment_sources", [])
        
        # 情感来源权重
        self.source_weights = {
            "twitter": 0.25,
            "reddit": 0.20,
            "telegram": 0.15,
            "news": 0.25,
            "fear_greed": 0.10,
            "social_volume": 0.05,
        }
        
        # 初始化AI分析混入类
        super().__init__()
        
        # 初始化LLM服务（如果还未初始化）
        llm_service_config = config.get("llm_service_config")
        if llm_service_config:
            initialize_llm_service(llm_service_config)
            logger.info("SentimentAnalyst: 统一LLM服务初始化完成")

    def collect_data(self, symbol: str, end_date: str) -> Dict[str, Any]:
        """
        收集情绪数据
        
        Args:
            symbol: 交易对符号
            end_date: 截止日期
            
        Returns:
            情绪数据
        """
        try:
            base_currency = self._parse_symbol(symbol)
            
            return {
                "symbol": symbol,
                "base_currency": base_currency,
                "end_date": end_date,
                "twitter_sentiment": self._collect_twitter_sentiment(base_currency, end_date),
                "reddit_sentiment": self._collect_reddit_sentiment(base_currency, end_date),
                "telegram_sentiment": self._collect_telegram_sentiment(base_currency, end_date),
                "news_sentiment": self._collect_news_sentiment(base_currency, end_date),
                "fear_greed_index": self._collect_fear_greed_index(base_currency, end_date),
                "social_volume": self._collect_social_volume(base_currency, end_date),
                "influencer_opinions": self._collect_influencer_opinions(base_currency, end_date),
            }
            
        except Exception as e:
            logger.error(f"Error collecting sentiment data for {symbol}: {str(e)}")
            return {"error": str(e)}
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析情绪数据
        
        Args:
            data: 情绪数据
            
        Returns:
            情绪分析结果
        """
        try:
            if "error" in data:
                return {"error": data["error"]}
            
            # 使用统一的AI增强分析流程
            return self.analyze_with_ai_enhancement(data, self._traditional_analyze)
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment data: {str(e)}")
            return {"error": str(e)}

    def _traditional_analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        传统情绪分析方法
        
        Args:
            data: 情绪数据
            
        Returns:
            传统分析结果
        """
        # 分析各项情绪源
        twitter_analysis = self._analyze_twitter_sentiment(data.get("twitter_sentiment", {}))
        reddit_analysis = self._analyze_reddit_sentiment(data.get("reddit_sentiment", {}))
        telegram_analysis = self._analyze_telegram_sentiment(data.get("telegram_sentiment", {}))
        news_analysis = self._analyze_news_sentiment(data.get("news_sentiment", {}))
        social_volume_analysis = self._analyze_social_volume(data.get("social_volume", {}))
        
        # 恐惧贪婪指数分析
        fear_greed_analysis = self._analyze_fear_greed_index(data.get("fear_greed_index", {}))
        
        # 意见领袖分析
        influencer_analysis = self._analyze_influencer_opinions(data.get("influencer_opinions", {}))
        
        # 综合情绪分析
        overall_sentiment = self._calculate_overall_sentiment(
            twitter_analysis, reddit_analysis, telegram_analysis, news_analysis
        )
        
        # 情绪趋势分析
        sentiment_trend = self._analyze_sentiment_trend(data)
        
        # 情绪风险评估
        risk_assessment = self._assess_sentiment_risk(
            overall_sentiment, fear_greed_analysis, social_volume_analysis
        )
        
        # 关键情绪信号
        key_signals = self._identify_key_sentiment_signals(
            twitter_analysis, reddit_analysis, news_analysis, fear_greed_analysis
        )
        
        return {
            "overall_sentiment": overall_sentiment,
            "sentiment_trend": sentiment_trend,
            "risk_signals": risk_assessment,
            "key_signals": key_signals,
            "twitter_analysis": twitter_analysis,
            "reddit_analysis": reddit_analysis,
            "telegram_analysis": telegram_analysis,
            "news_analysis": news_analysis,
            "fear_greed_analysis": fear_greed_analysis,
            "social_volume_analysis": social_volume_analysis,
            "influencer_analysis": influencer_analysis,
            "confidence": self._calculate_confidence(overall_sentiment, sentiment_trend),
            "data_quality": self._assess_data_quality(data),
        }
    
    def _parse_symbol(self, symbol: str) -> str:
        """解析交易对符号，获取基础货币"""
        return symbol.split('/')[0]
    
    def _collect_twitter_sentiment(self, currency: str, end_date: str) -> Dict[str, Any]:
        """收集Twitter情绪数据"""
        return {
            "tweet_count": 15420,
            "positive_tweets": 8750,
            "negative_tweets": 3250,
            "neutral_tweets": 3420,
            "sentiment_score": 0.68,
            "engagement_rate": 0.045,
            "trending_hashtags": ["#Bitcoin", "#Crypto", "#BTC"],
            "influencer_mentions": 125,
            "spam_ratio": 0.08,
        }
    
    def _collect_reddit_sentiment(self, currency: str, end_date: str) -> Dict[str, Any]:
        """收集Reddit情绪数据"""
        return {
            "post_count": 850,
            "comment_count": 12500,
            "upvote_ratio": 0.72,
            "sentiment_score": 0.65,
            "active_subreddits": ["r/Bitcoin", "r/CryptoCurrency", "r/CryptoMarkets"],
            "top_posts_sentiment": 0.78,
            "controversy_score": 0.15,
        }
    
    def _collect_telegram_sentiment(self, currency: str, end_date: str) -> Dict[str, Any]:
        """收集Telegram情绪数据"""
        return {
            "message_count": 45000,
            "active_users": 8500,
            "sentiment_score": 0.71,
            "group_growth": 0.05,
            "admin_sentiment": 0.75,
            "spam_ratio": 0.12,
        }
    
    def _collect_news_sentiment(self, currency: str, end_date: str) -> Dict[str, Any]:
        """收集新闻情绪数据"""
        return {
            "article_count": 125,
            "positive_articles": 45,
            "negative_articles": 25,
            "neutral_articles": 55,
            "sentiment_score": 0.62,
            "media_sentiment": 0.58,
            "institutional_coverage": 0.45,
            "breaking_news_impact": 0.15,
        }
    
    def _collect_fear_greed_index(self, currency: str, end_date: str) -> Dict[str, Any]:
        """收集恐惧贪婪指数"""
        return {
            "fear_greed_value": 72,
            "classification": "Greed",
            "components": {
                "volatility": 35,
                "market_momentum": 78,
                "social_media": 85,
                "dominance": 42,
                "trends": 68,
            },
            "weekly_change": 8,
            "monthly_change": 15,
        }
    
    def _collect_social_volume(self, currency: str, end_date: str) -> Dict[str, Any]:
        """收集社交量数据"""
        return {
            "total_mentions": 185000,
            "unique_authors": 45000,
            "volume_trend": "increasing",
            "growth_rate_24h": 0.12,
            "peak_hour": "14:00 UTC",
            "engagement_quality": 0.68,
        }
    
    def _collect_influencer_opinions(self, currency: str, end_date: str) -> Dict[str, Any]:
        """收集意见领袖观点"""
        return {
            "influencer_count": 25,
            "bullish_influencers": 18,
            "bearish_influencers": 4,
            "neutral_influencers": 3,
            "consensus_sentiment": "bullish",
            "confidence_level": 0.78,
            "key_opinions": [
                "长期看好比特币作为数字黄金",
                "机构采用正在加速",
                "监管环境趋于明朗"
            ],
        }
    
    def _analyze_twitter_sentiment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析Twitter情绪"""
        sentiment_score = data.get("sentiment_score", 0.5)
        engagement_rate = data.get("engagement_rate", 0.0)
        
        return {
            "sentiment": "bullish" if sentiment_score > 0.6 else "bearish" if sentiment_score < 0.4 else "neutral",
            "intensity": "high" if engagement_rate > 0.05 else "low" if engagement_rate < 0.02 else "moderate",
            "community_engagement": "strong" if engagement_rate > 0.04 else "weak",
            "spam_level": "high" if data.get("spam_ratio", 0) > 0.1 else "low",
            "virality_potential": "high" if sentiment_score > 0.7 and engagement_rate > 0.04 else "low",
        }
    
    def _analyze_reddit_sentiment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析Reddit情绪"""
        sentiment_score = data.get("sentiment_score", 0.5)
        upvote_ratio = data.get("upvote_ratio", 0.5)
        
        return {
            "sentiment": "bullish" if sentiment_score > 0.6 else "bearish" if sentiment_score < 0.4 else "neutral",
            "community_quality": "high" if upvote_ratio > 0.7 else "low" if upvote_ratio < 0.5 else "moderate",
            "discussion_depth": "deep" if data.get("comment_count", 0) > 10000 else "shallow",
            "controversy_level": "high" if data.get("controversy_score", 0) > 0.2 else "low",
            "organic_growth": "strong" if upvote_ratio > 0.75 else "weak",
        }
    
    def _analyze_telegram_sentiment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析Telegram情绪"""
        sentiment_score = data.get("sentiment_score", 0.5)
        user_growth = data.get("group_growth", 0.0)
        
        return {
            "sentiment": "bullish" if sentiment_score > 0.6 else "bearish" if sentiment_score < 0.4 else "neutral",
            "community_growth": "fast" if user_growth > 0.1 else "slow" if user_growth < 0.02 else "stable",
            "engagement_level": "high" if data.get("active_users", 0) > 5000 else "low",
            "admin_influence": "strong" if data.get("admin_sentiment", 0.5) > 0.7 else "weak",
            "spam_level": "high" if data.get("spam_ratio", 0) > 0.15 else "low",
        }
    
    def _analyze_news_sentiment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析新闻情绪"""
        sentiment_score = data.get("sentiment_score", 0.5)
        institutional_coverage = data.get("institutional_coverage", 0.0)
        
        return {
            "sentiment": "bullish" if sentiment_score > 0.6 else "bearish" if sentiment_score < 0.4 else "neutral",
            "media_tone": "positive" if sentiment_score > 0.65 else "negative" if sentiment_score < 0.35 else "neutral",
            "institutional_interest": "high" if institutional_coverage > 0.5 else "low" if institutional_coverage < 0.3 else "moderate",
            "news_impact": "significant" if data.get("breaking_news_impact", 0) > 0.2 else "minimal",
            "mainstream_adoption": "increasing" if institutional_coverage > 0.4 else "stable",
        }
    
    def _analyze_social_volume(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析社交量"""
        volume_trend = data.get("volume_trend", "stable")
        growth_rate = data.get("growth_rate_24h", 0.0)
        
        return {
            "volume_level": "high" if data.get("total_mentions", 0) > 100000 else "low" if data.get("total_mentions", 0) < 20000 else "moderate",
            "growth_momentum": "strong" if growth_rate > 0.15 else "weak" if growth_rate < 0.05 else "moderate",
            "community_activity": "booming" if volume_trend == "increasing" and growth_rate > 0.1 else "declining" if volume_trend == "decreasing" else "stable",
            "peak_activity": data.get("peak_hour", "unknown"),
            "engagement_quality": "high" if data.get("engagement_quality", 0.5) > 0.7 else "low",
        }
    
    def _analyze_fear_greed_index(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析恐惧贪婪指数"""
        fgi_value = data.get("fear_greed_value", 50)
        classification = data.get("classification", "Neutral")
        
        return {
            "market_psychology": classification.lower(),
            "extreme_level": "extreme" if fgi_value > 80 or fgi_value < 20 else "moderate",
            "contrarian_signal": "strong" if fgi_value > 75 or fgi_value < 25 else "weak",
            "momentum_indicator": "strong" if abs(fgi_value - 50) > 25 else "weak",
            "weekly_trend": "improving" if data.get("weekly_change", 0) > 5 else "declining" if data.get("weekly_change", 0) < -5 else "stable",
        }
    
    def _analyze_influencer_opinions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析意见领袖观点"""
        consensus = data.get("consensus_sentiment", "neutral")
        confidence = data.get("confidence_level", 0.5)
        
        return {
            "influencer_consensus": consensus,
            "confidence_level": "high" if confidence > 0.7 else "low" if confidence < 0.4 else "moderate",
            "opinion_diversity": "low" if abs(data.get("bullish_influencers", 0) - data.get("bearish_influencers", 0)) > 10 else "high",
            "thought_leadership": "strong" if data.get("influencer_count", 0) > 20 else "weak",
            "key_themes": data.get("key_opinions", []),
        }
    
    def _calculate_overall_sentiment(self, twitter_analysis: Dict, reddit_analysis: Dict, 
                                   telegram_analysis: Dict, news_analysis: Dict) -> Dict[str, Any]:
        """计算整体情绪"""
        sentiment_scores = []
        
        # 收集各源的情绪得分
        for analysis, weight in [
            (twitter_analysis, 0.30),
            (reddit_analysis, 0.25),
            (telegram_analysis, 0.15),
            (news_analysis, 0.20),
        ]:
            sentiment = analysis.get("sentiment", "neutral")
            score = 0.75 if sentiment == "bullish" else 0.25 if sentiment == "bearish" else 0.5
            sentiment_scores.append(score * weight)
        
        overall_score = sum(sentiment_scores)
        
        return {
            "score": overall_score,
            "sentiment": "bullish" if overall_score > 0.6 else "bearish" if overall_score < 0.4 else "neutral",
            "strength": "strong" if abs(overall_score - 0.5) > 0.25 else "moderate" if abs(overall_score - 0.5) > 0.15 else "weak",
            "consistency": "high" if all(s.get("sentiment") == list(sentiment_scores)[0] for s in [twitter_analysis, reddit_analysis]) else "low",
        }
    
    def _analyze_sentiment_trend(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析情绪趋势"""
        # 简化的趋势分析
        growth_rates = [
            data.get("twitter_sentiment", {}).get("engagement_rate", 0),
            data.get("social_volume", {}).get("growth_rate_24h", 0),
            data.get("fear_greed_index", {}).get("weekly_change", 0),
        ]
        
        avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0
        
        return {
            "trend": "improving" if avg_growth > 0.05 else "declining" if avg_growth < -0.05 else "stable",
            "momentum": "strong" if avg_growth > 0.1 else "weak" if avg_growth < -0.1 else "moderate",
            "sustainability": "high" if avg_growth > 0.02 else "low",
        }
    
    def _assess_sentiment_risk(self, overall_sentiment: Dict, fear_greed_analysis: Dict, 
                             social_volume_analysis: Dict) -> Dict[str, Any]:
        """评估情绪风险"""
        risk_factors = []
        risk_score = 0.0
        
        # 极端情绪风险
        sentiment_strength = overall_sentiment.get("strength", "weak")
        if sentiment_strength == "strong":
            risk_score += 0.2
            risk_factors.append("情绪过于极端")
        
        # 恐惧贪婪指数风险
        fgi_psychology = fear_greed_analysis.get("market_psychology", "neutral")
        if fgi_psychology in ["extreme greed", "extreme fear"]:
            risk_score += 0.3
            risk_factors.append(f"市场心理: {fgi_psychology}")
        
        # 社交量异常风险
        volume_level = social_volume_analysis.get("volume_level", "moderate")
        if volume_level == "high":
            risk_score += 0.2
            risk_factors.append("社交量异常高涨")
        
        return {
            "overall_score": min(risk_score, 1.0),
            "risk_level": "high" if risk_score > 0.5 else "medium" if risk_score > 0.25 else "low",
            "key_risks": risk_factors,
            "contrarian_opportunity": risk_score > 0.4,
        }
    
    def _identify_key_sentiment_signals(self, twitter_analysis: Dict, reddit_analysis: Dict, 
                                      news_analysis: Dict, fear_greed_analysis: Dict) -> List[str]:
        """识别关键情绪信号"""
        signals = []
        
        # Twitter信号
        if twitter_analysis.get("sentiment") == "bullish":
            signals.append("Twitter情绪看涨")
        
        # Reddit信号
        if reddit_analysis.get("community_quality") == "high":
            signals.append("Reddit社区质量高")
        
        # 新闻信号
        if news_analysis.get("institutional_interest") == "high":
            signals.append("机构关注度提升")
        
        # 恐惧贪婪信号
        fgi_signal = fear_greed_analysis.get("contrarian_signal", "weak")
        if fgi_signal == "strong":
            signals.append("恐惧贪婪指数显示逆向信号")
        
        return signals
    
    def _calculate_confidence(self, overall_sentiment: Dict, sentiment_trend: Dict) -> float:
        """计算分析置信度"""
        consistency_score = 0.8 if overall_sentiment.get("consistency") == "high" else 0.5
        momentum_score = 0.7 if sentiment_trend.get("momentum") == "strong" else 0.5
        
        return (consistency_score + momentum_score) / 2
    
    def _assess_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """评估数据质量"""
        required_fields = [
            "twitter_sentiment", "reddit_sentiment", "news_sentiment",
            "fear_greed_index", "social_volume"
        ]
        
        completeness = sum(1 for field in required_fields if field in data and data[field]) / len(required_fields)
        
        return {
            "completeness": completeness,
            "quality_score": completeness,
            "freshness": "recent",  # 假设数据是最近的
            "reliability": "high" if completeness > 0.8 else "medium" if completeness > 0.6 else "low",
        }

    def _analyze_with_ai(self, traditional_analysis: Dict[str, Any], raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用AI进行情绪分析增强
        
        Args:
            traditional_analysis: 传统分析结果
            raw_data: 原始数据
            
        Returns:
            AI分析结果
        """
        try:
            # 构建情绪分析prompt
            prompt = self._build_sentiment_analysis_prompt(traditional_analysis, raw_data)
            
            # 调用统一LLM服务
            ai_response = self.call_ai_analysis(prompt)
            
            # 解析AI响应
            ai_analysis = self.parse_ai_json_response(ai_response, {
                "sentiment_prediction": {"direction": "中性", "strength": 0.5},
                "market_emotion_cycle": {"current_phase": "未知", "transition_probability": 0.5},
                "anomaly_signals": {"detected": False, "signals": []},
                "trading_psychology": {"crowd_behavior": "中性", "contrarian_value": 0.5},
                "sentiment_forecast": {"short_term": "稳定", "medium_term": "稳定"},
                "confidence_level": 0.5,
                "key_insights": ["AI分析不可用"]
            })
            
            return ai_analysis
            
        except Exception as e:
            logger.error(f"SentimentAnalyst: AI分析失败: {str(e)}")
            raise

    def _build_sentiment_analysis_prompt(self, traditional_analysis: Dict[str, Any], raw_data: Dict[str, Any]) -> str:
        """构建情绪分析AI提示词"""
        
        # 使用标准化prompt构建方法
        analysis_dimensions = [
            "情绪趋势预测 - 基于历史模式预测未来3-7天情绪变化趋势",
            "市场情绪周期 - 判断当前处于情绪周期的哪个阶段",
            "异常情绪信号 - 识别可能影响价格的异常情绪变化和极端情绪",
            "交易心理洞察 - 分析群体心理对交易行为的影响和市场预期",
            "反向指标价值 - 评估情绪指标作为反向指标的可靠性",
            "情绪传导机制 - 分析情绪在不同平台和群体间的传播路径",
            "置信度评估 - 评估情绪分析结果的可靠性和预测准确度"
        ]
        
        output_fields = [
            "sentiment_prediction",
            "market_emotion_cycle",
            "anomaly_signals", 
            "trading_psychology",
            "contrarian_indicators",
            "sentiment_forecast",
            "confidence_level",
            "key_insights"
        ]
        
        return self._build_standard_analysis_prompt(
            "加密货币市场情绪分析师",
            traditional_analysis,
            raw_data,
            analysis_dimensions,
            output_fields
        )
    
    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """解析AI回应"""
        try:
            # 尝试从响应中提取JSON
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = ai_response[json_start:json_end]
                return json.loads(json_str)
            else:
                # 如果没有找到JSON格式，返回文本分析
                return {
                    "executive_summary": ai_response,
                    "confidence_assessment": {"analysis_confidence": 0.7},
                    "sentiment_forecast": {"next_3_days": "中性", "next_7_days": "中性"},
                    "investment_recommendation": {"sentiment_based_action": "观望"}
                }
                
        except json.JSONDecodeError as e:
            logger.error(f"解析AI回应JSON失败: {e}")
            return {
                "executive_summary": ai_response,
                "confidence_assessment": {"analysis_confidence": 0.5},
                "parsing_error": str(e)
            }
        except Exception as e:
            logger.error(f"解析AI回应失败: {e}")
            return {
                "executive_summary": "AI分析解析失败",
                "confidence_assessment": {"analysis_confidence": 0.3},
                "error": str(e)
            }
    
    def _combine_analyses(self, traditional_analysis: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        组合传统分析和AI分析结果
        
        Args:
            traditional_analysis: 传统分析结果
            ai_analysis: AI分析结果
            
        Returns:
            组合后的分析结果
        """
        try:
            # 使用标准化组合方法
            enhanced_analysis = self._combine_standard_analyses(
                traditional_analysis, 
                ai_analysis, 
                confidence_weight_ai=0.6  # AI在情绪分析中的权重
            )
            
            # 添加情绪分析特定的增强字段
            enhanced_analysis.update({
                "ai_sentiment_prediction": ai_analysis.get("sentiment_prediction", {}),
                "ai_emotion_cycle": ai_analysis.get("market_emotion_cycle", {}),
                "ai_anomaly_signals": ai_analysis.get("anomaly_signals", {}),
                "ai_trading_psychology": ai_analysis.get("trading_psychology", {}),
                "ai_contrarian_indicators": ai_analysis.get("contrarian_indicators", {}),
                "ai_sentiment_forecast": ai_analysis.get("sentiment_forecast", {}),
                "ai_key_insights": ai_analysis.get("key_insights", [])
            })
            
            return enhanced_analysis
            
        except Exception as e:
            logger.error(f"SentimentAnalyst: 分析结果组合失败: {str(e)}")
            # 发生错误时返回传统分析结果
            fallback_analysis = traditional_analysis.copy()
            fallback_analysis["ai_enhanced"] = False
            fallback_analysis["combine_error"] = str(e)
            return fallback_analysis

    def _format_traditional_analysis_summary(self, traditional_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """格式化传统分析结果摘要（重写父类方法）"""
        return {
            "整体情绪": traditional_analysis.get("overall_sentiment", {}),
            "情绪趋势": traditional_analysis.get("sentiment_trend", {}),
            "风险信号": traditional_analysis.get("risk_signals", {}),
            "关键信号": traditional_analysis.get("key_signals", {}),
            "置信度": traditional_analysis.get("confidence", 0)
        }

    def _format_raw_data_summary(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化原始数据摘要（重写父类方法）"""
        return {
            "Twitter情绪": raw_data.get("twitter_sentiment", {}),
            "Reddit讨论": raw_data.get("reddit_sentiment", {}),
            "Telegram群组": raw_data.get("telegram_sentiment", {}),
            "新闻情绪": raw_data.get("news_sentiment", {}),
            "恐惧贪婪指数": raw_data.get("fear_greed_index", {}),
            "社交媒体热度": raw_data.get("social_volume", {}),
            "意见领袖观点": raw_data.get("influencer_opinions", {})
        }
