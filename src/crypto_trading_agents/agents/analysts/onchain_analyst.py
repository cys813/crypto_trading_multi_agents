"""
链上分析师 - 专注加密货币链上数据分析

分析区块链数据、巨鲸动向、DeFi协议状态等
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

# 导入链上数据服务
from ...services.onchain_data.onchain_data_service import OnchainDataService

logger = logging.getLogger(__name__)

class OnchainAnalyst(StandardAIAnalysisMixin):
    """加密货币链上分析师"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化链上分析师
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.supported_chains = config.get("crypto_config", {}).get("supported_chains", [])
        
        # 链上指标权重
        self.metric_weights = {
            "active_addresses": 0.20,
            "transaction_count": 0.15,
            "exchange_flows": 0.25,
            "whale_transactions": 0.20,
            "hash_rate": 0.10,
            "staking_metrics": 0.10,
        }
        
        # 初始化AI分析混入类
        super().__init__()
        
        # 初始化链上数据服务
        self.onchain_data_service = OnchainDataService(config)
        
        # 初始化LLM服务（如果还未初始化）
        llm_service_config = config.get("llm_service_config")
        if llm_service_config:
            initialize_llm_service(llm_service_config)
            logger.info("OnchainAnalyst: 统一LLM服务初始化完成")

    
    def collect_data(self, symbol: str, end_date: str) -> Dict[str, Any]:
        """
        收集链上数据
        
        Args:
            symbol: 交易对符号
            end_date: 截止日期
            
        Returns:
            链上数据
        """
        try:
            # 解析币种和链
            base_currency = self._parse_symbol(symbol)
            chain = self._determine_chain(base_currency)
            
            if not chain:
                return {"error": f"Unsupported chain for symbol: {symbol}"}
            
            # TODO: 实现真实的链上数据收集
            return {
                "symbol": symbol,
                "base_currency": base_currency,
                "chain": chain,
                "end_date": end_date,
                "active_addresses": self._collect_active_addresses(base_currency, chain, end_date),
                "transaction_metrics": self._collect_transaction_metrics(base_currency, chain, end_date),
                "exchange_flows": self._collect_exchange_flows(base_currency, chain, end_date),
                "whale_activity": self._collect_whale_activity(base_currency, chain, end_date),
                "network_health": self._collect_network_health(base_currency, chain, end_date),
                "defi_metrics": self._collect_defi_metrics(base_currency, chain, end_date),
                "holder_distribution": self._collect_holder_distribution(base_currency, chain, end_date),
            }
            
        except Exception as e:
            logger.error(f"Error collecting onchain data for {symbol}: {str(e)}")
            return {"error": str(e)}
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析链上数据
        
        Args:
            data: 链上数据
            
        Returns:
            链上分析结果
        """
        try:
            if "error" in data:
                return {"error": data["error"]}
            
            # 使用统一的AI增强分析流程
            return self.analyze_with_ai_enhancement(data, self._traditional_analyze)
            
        except Exception as e:
            logger.error(f"Error analyzing onchain data: {str(e)}")
            return {"error": str(e)}

    async def run(self, symbol: str = "BTC/USDT", timeframe: str = "1d") -> Dict[str, Any]:
        """
        统一对外接口函数，执行完整的链上数据分析流程
        
        Args:
            symbol: 交易对符号，如 'BTC/USDT'
            timeframe: 时间周期，如 '1d', '4h', '1h'
            
        Returns:
            Dict[str, Any]: 完整的分析结果
        """
        try:
            # 步骤1：收集数据
            collected_data = await self.collect_data(symbol, timeframe)
            
            # 步骤2：执行分析
            analysis_result = await self.analyze(collected_data)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"OnchainAnalyst run失败: {e}")
            return {
                'error': str(e),
                'status': 'failed',
                'symbol': symbol,
                'timeframe': timeframe,
                'analysis_type': 'onchain'
            }

    def _traditional_analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        传统链上分析方法
        
        Args:
            data: 链上数据
            
        Returns:
            传统分析结果
        """
        # 分析各项指标
        address_analysis = self._analyze_active_addresses(data.get("active_addresses", {}))
        transaction_analysis = self._analyze_transaction_metrics(data.get("transaction_metrics", {}))
        flow_analysis = self._analyze_exchange_flows(data.get("exchange_flows", {}))
        whale_analysis = self._analyze_whale_activity(data.get("whale_activity", {}))
        network_analysis = self._analyze_network_health(data.get("network_health", {}))
        defi_analysis = self._analyze_defi_metrics(data.get("defi_metrics", {}))
        holder_analysis = self._analyze_holder_distribution(data.get("holder_distribution", {}))
        
        # 综合分析
        onchain_health = self._calculate_onchain_health(
            address_analysis, transaction_analysis, network_analysis
        )
        
        # 市场情绪分析
        market_sentiment = self._analyze_onchain_sentiment(
            flow_analysis, whale_analysis, defi_analysis
        )
        
        # 风险评估
        risk_assessment = self._assess_onchain_risk(
            whale_analysis, flow_analysis, network_analysis
        )
        
        # 关键洞察
        key_insights = self._generate_key_insights(
            address_analysis, transaction_analysis, flow_analysis, whale_analysis
        )
        
        return {
            "onchain_health": onchain_health,
            "market_sentiment": market_sentiment,
            "risk_metrics": risk_assessment,
            "key_insights": key_insights,
            "address_analysis": address_analysis,
            "transaction_analysis": transaction_analysis,
            "flow_analysis": flow_analysis,
            "whale_analysis": whale_analysis,
            "network_analysis": network_analysis,
            "defi_analysis": defi_analysis,
            "holder_analysis": holder_analysis,
            "confidence": self._calculate_confidence(onchain_health, market_sentiment),
            "data_quality": self._assess_data_quality(data),
        }

    def _analyze_with_ai(self, traditional_analysis: Dict[str, Any], raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用AI进行链上数据分析增强
        
        Args:
            traditional_analysis: 传统分析结果
            raw_data: 原始数据
            
        Returns:
            AI分析结果
        """
        try:
            # 构建链上分析prompt
            prompt = self._build_onchain_analysis_prompt(traditional_analysis, raw_data)
            
            # 调用统一LLM服务
            ai_response = self.call_ai_analysis(prompt)
            
            # 解析AI响应
            ai_analysis = self.parse_ai_json_response(ai_response, {
                "network_health_analysis": {"current_status": "未知", "growth_sustainability": "未知"},
                "capital_flow_analysis": {"exchange_flow_signal": "未知", "whale_behavior_impact": "未知"},
                "onchain_sentiment": {"overall_sentiment": "中性", "sentiment_strength": 0.5},
                "investment_recommendation": {"timeframe": "未知", "recommendation": "观望"},
                "confidence_assessment": {"analysis_confidence": 0.5, "prediction_reliability": "中"}
            })
            
            return ai_analysis
            
        except Exception as e:
            logger.error(f"OnchainAnalyst: AI分析失败: {str(e)}")
            raise

    def _build_onchain_analysis_prompt(self, traditional_analysis: Dict[str, Any], raw_data: Dict[str, Any]) -> str:
        """构建链上分析AI提示词"""
        
        # 使用标准化prompt构建方法
        analysis_dimensions = [
            "网络健康度评估 - 分析区块链网络的整体健康状况和发展趋势",
            "资金流向分析 - 评估交易所流量、巨鲸行为和机构资金动向",
            "链上情绪分析 - 分析链上数据反映的市场情绪和投资者行为",
            "投资建议生成 - 基于链上数据提供具体的投资时机和策略建议",
            "风险机会评估 - 识别链上数据中的风险信号和投资机会",
            "市场周期判断 - 基于链上指标判断当前市场所处的周期阶段",
            "置信度评估 - 评估分析结果的可靠性和数据质量"
        ]
        
        output_fields = [
            "network_health_analysis",
            "capital_flow_analysis", 
            "onchain_sentiment",
            "investment_recommendation",
            "market_cycle_analysis",
            "risk_opportunities",
            "confidence_assessment",
            "executive_summary"
        ]
        
        return self._build_standard_analysis_prompt(
            "链上数据分析师",
            traditional_analysis,
            raw_data,
            analysis_dimensions,
            output_fields
        )

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
            # 使用标准化组合方法，并自定义置信度权重
            enhanced_analysis = self._combine_standard_analyses(
                traditional_analysis, 
                ai_analysis, 
                confidence_weight_ai=0.7  # AI分析在链上数据中权重较高
            )
            
            # 添加链上分析特定的增强字段
            enhanced_analysis.update({
                "ai_network_health": ai_analysis.get("network_health_analysis", {}),
                "ai_capital_flow": ai_analysis.get("capital_flow_analysis", {}),
                "ai_onchain_sentiment": ai_analysis.get("onchain_sentiment", {}),
                "ai_investment_recommendation": ai_analysis.get("investment_recommendation", {}),
                "ai_market_cycle": ai_analysis.get("market_cycle_analysis", {}),
                "ai_risk_opportunities": ai_analysis.get("risk_opportunities", {}),
                "ai_executive_summary": ai_analysis.get("executive_summary", "")
            })
            
            return enhanced_analysis
            
        except Exception as e:
            logger.error(f"OnchainAnalyst: 分析结果组合失败: {str(e)}")
            # 发生错误时返回传统分析结果
            fallback_analysis = traditional_analysis.copy()
            fallback_analysis["ai_enhanced"] = False
            fallback_analysis["combine_error"] = str(e)
            return fallback_analysis

    def _format_traditional_analysis_summary(self, traditional_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """格式化传统分析结果摘要（重写父类方法）"""
        return {
            "链上健康度": traditional_analysis.get("onchain_health", {}),
            "市场情绪": traditional_analysis.get("market_sentiment", {}),
            "风险评估": traditional_analysis.get("risk_metrics", {}),
            "置信度": traditional_analysis.get("confidence", 0),
            "数据质量": traditional_analysis.get("data_quality", 0)
        }

    def _format_raw_data_summary(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化原始数据摘要（重写父类方法）"""
        return {
            "活跃地址": raw_data.get("active_addresses", {}),
            "交易指标": raw_data.get("transaction_metrics", {}),
            "交易所流量": raw_data.get("exchange_flows", {}),
            "巨鲸活动": raw_data.get("whale_activity", {}),
            "网络健康": raw_data.get("network_health", {}),
            "DeFi指标": raw_data.get("defi_metrics", {}),
            "持币分布": raw_data.get("holder_distribution", {})
        }
    
    def _parse_symbol(self, symbol: str) -> str:
        """解析交易对符号，获取基础货币"""
        return symbol.split('/')[0]
    
    def _determine_chain(self, currency: str) -> str:
        """确定币种所属链"""
        chain_mapping = {
            "BTC": "bitcoin",
            "ETH": "ethereum", 
            "BNB": "binance-smart-chain",
            "SOL": "solana",
            "MATIC": "polygon",
            "AVAX": "avalanche",
            "DOT": "polkadot",
            "TON": "ton",
        }
        return chain_mapping.get(currency, "ethereum")
    
    def _collect_active_addresses(self, currency: str, chain: str, end_date: str) -> Dict[str, Any]:
        """收集活跃地址数据"""
        try:
            # 使用真实的链上数据服务获取数据
            return self.onchain_data_service.get_active_addresses(currency, chain, end_date)
        except Exception as e:
            logger.error(f"Failed to collect active addresses data: {str(e)}")
            # 回退到模拟数据
            return {
                "daily_active": 850000,
                "weekly_active": 3200000,
                "monthly_active": 8500000,
                "growth_rate_7d": 0.05,
                "growth_rate_30d": 0.12,
                "historical_avg": 750000,
                "percentile": 75,
                "source": "fallback_mock"
            }
    
    def _collect_transaction_metrics(self, currency: str, chain: str, end_date: str) -> Dict[str, Any]:
        """收集交易指标数据"""
        try:
            # 使用真实的链上数据服务获取数据
            return self.onchain_data_service.get_transaction_metrics(currency, chain, end_date)
        except Exception as e:
            logger.error(f"Failed to collect transaction metrics data: {str(e)}")
            # 回退到模拟数据
            return {
                "daily_transactions": 1250000,
                "average_fee": 15.5,
                "total_fees": 19375000,
                "large_transactions": 1250,
                "transaction_growth": 0.08,
                "fee_trend": "increasing",
                "source": "fallback_mock"
            }
    
    def _collect_exchange_flows(self, currency: str, chain: str, end_date: str) -> Dict[str, Any]:
        """收集交易所流量数据"""
        try:
            # 使用真实的链上数据服务获取数据
            return self.onchain_data_service.get_exchange_flows(currency, chain, end_date)
        except Exception as e:
            logger.error(f"Failed to collect exchange flows data: {str(e)}")
            # 回退到模拟数据
            return {
                "exchange_inflows": 15000,
                "exchange_outflows": 12000,
                "net_flow": -3000,  # 净流出
                "inflow_trend": "decreasing",
                "outflow_trend": "increasing",
                "exchange_balance": 2500000,
                "balance_change_24h": -0.12,
                "source": "fallback_mock"
            }
    
    def _collect_whale_activity(self, currency: str, chain: str, end_date: str) -> Dict[str, Any]:
        """收集巨鲸活动数据"""
        try:
            # 使用真实的链上数据服务获取数据
            return self.onchain_data_service.get_whale_activity(currency, chain, end_date)
        except Exception as e:
            logger.error(f"Failed to collect whale activity data: {str(e)}")
            # 回退到模拟数据
            return {
                "whale_transactions": 45,
                "whale_inflows": 8000,
                "whale_outflows": 6500,
                "net_whale_flow": -1500,
                "whale_concentration": 0.62,
                "large_holder_count": 8500,
                "accumulation_pattern": True,
                "source": "fallback_mock"
            }
    
    def _collect_network_health(self, currency: str, chain: str, end_date: str) -> Dict[str, Any]:
        """收集网络健康数据"""
        try:
            # 使用真实的链上数据服务获取数据
            return self.onchain_data_service.get_network_health(currency, chain, end_date)
        except Exception as e:
            logger.error(f"Failed to collect network health data: {str(e)}")
            # 回退到模拟数据
            if currency == "BTC":
                return {
                    "hash_rate": 450000000000000,  # 450 EH/s
                    "difficulty": 72000000000000,
                    "mining_revenue": 35000000,
                    "network_nodes": 15000,
                    "network_uptime": 0.9999,
                    "source": "fallback_mock"
                }
            else:
                return {
                    "active_validators": 850000,
                    "staking_rate": 0.15,
                    "network_nodes": 8500,
                    "gas_usage": 0.75,
                    "network_uptime": 0.9995,
                    "source": "fallback_mock"
                }
    
    def _collect_defi_metrics(self, currency: str, chain: str, end_date: str) -> Dict[str, Any]:
        """收集DeFi指标数据"""
        try:
            # 使用真实的链上数据服务获取数据
            return self.onchain_data_service.get_defi_metrics(currency, chain, end_date)
        except Exception as e:
            logger.error(f"Failed to collect DeFi metrics data: {str(e)}")
            # 回退到模拟数据
            return {
                "tvl": 25000000000,  # 250亿美元
                "defi_users": 4500000,
                "protocol_count": 350,
                "lending_volume": 850000000,
                "dex_volume": 1200000000,
                "yield_farming_tvl": 8500000000,
                "source": "fallback_mock"
            }
    
    def _collect_holder_distribution(self, currency: str, chain: str, end_date: str) -> Dict[str, Any]:
        """收集持币分布数据"""
        try:
            # 使用真实的链上数据服务获取数据
            return self.onchain_data_service.get_holder_distribution(currency, chain, end_date)
        except Exception as e:
            logger.error(f"Failed to collect holder distribution data: {str(e)}")
            # 回退到模拟数据
            return {
                "top_10_holders": 0.15,
                "top_100_holders": 0.35,
                "retail_holders": 0.65,
                "holder_growth": 0.08,
                "average_balance": 0.85,
                "gini_coefficient": 0.72,
                "source": "fallback_mock"
            }
    
    def _analyze_active_addresses(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析活跃地址"""
        daily_active = data.get("daily_active", 0)
        growth_7d = data.get("growth_rate_7d", 0)
        historical_avg = data.get("historical_avg", 0)
        
        # 计算活跃度得分
        activity_score = min(daily_active / historical_avg, 2.0) if historical_avg > 0 else 1.0
        
        return {
            "activity_level": "high" if activity_score > 1.2 else "low" if activity_score < 0.8 else "normal",
            "growth_trend": "increasing" if growth_7d > 0.05 else "decreasing" if growth_7d < -0.05 else "stable",
            "network_adoption": "strong" if activity_score > 1.1 else "weak" if activity_score < 0.9 else "moderate",
            "score": activity_score,
        }
    
    def _analyze_transaction_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析交易指标"""
        daily_tx = data.get("daily_transactions", 0)
        avg_fee = data.get("average_fee", 0)
        tx_growth = data.get("transaction_growth", 0)
        
        return {
            "network_utilization": "high" if daily_tx > 1000000 else "low" if daily_tx < 100000 else "moderate",
            "fee_pressure": "high" if avg_fee > 20 else "low" if avg_fee < 5 else "normal",
            "usage_growth": "strong" if tx_growth > 0.1 else "declining" if tx_growth < -0.05 else "stable",
            "economic_activity": "high" if daily_tx > 500000 else "low" if daily_tx < 50000 else "moderate",
        }
    
    def _analyze_exchange_flows(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析交易所流量"""
        net_flow = data.get("net_flow", 0)
        balance_change = data.get("balance_change_24h", 0)
        
        return {
            "exchange_pressure": "selling" if net_flow > 0 else "buying" if net_flow < 0 else "neutral",
            "accumulation_phase": balance_change < -0.1,  # 交易所余额下降，可能是积累阶段
            "distribution_phase": balance_change > 0.1,  # 交易所余额上升，可能是分发阶段
            "liquidity_trend": "increasing" if balance_change > 0.05 else "decreasing" if balance_change < -0.05 else "stable",
        }
    
    def _analyze_whale_activity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析巨鲸活动"""
        concentration = data.get("whale_concentration", 0)
        accumulation = data.get("accumulation_pattern", False)
        net_flow = data.get("net_whale_flow", 0)
        
        return {
            "whale_sentiment": "bullish" if accumulation and net_flow < 0 else "bearish" if net_flow > 0 else "neutral",
            "concentration_risk": "high" if concentration > 0.7 else "low" if concentration < 0.4 else "moderate",
            "whale_behavior": "accumulating" if accumulation else "distributing",
            "market_manipulation_risk": "high" if concentration > 0.8 else "low",
        }
    
    def _analyze_network_health(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析网络健康"""
        uptime = data.get("network_uptime", 0)
        
        return {
            "network_status": "healthy" if uptime > 0.99 else "degraded" if uptime > 0.95 else "unhealthy",
            "decentralization": "high" if uptime > 0.99 else "moderate" if uptime > 0.95 else "low",
            "security_level": "high" if uptime > 0.99 else "medium" if uptime > 0.95 else "low",
            "scalability": "good" if uptime > 0.98 else "fair",
        }
    
    def _analyze_defi_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析DeFi指标"""
        tvl = data.get("tvl", 0)
        defi_users = data.get("defi_users", 0)
        
        return {
            "defi_adoption": "high" if tvl > 10000000000 else "low" if tvl < 1000000000 else "moderate",
            "user_engagement": "high" if defi_users > 1000000 else "low" if defi_users < 100000 else "moderate",
            "ecosystem_growth": "strong" if tvl > 5000000000 else "developing",
            "innovation_level": "high" if tvl > 20000000000 else "medium",
        }
    
    def _analyze_holder_distribution(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析持币分布"""
        gini = data.get("gini_coefficient", 0)
        retail_share = data.get("retail_holders", 0)
        
        return {
            "distribution_fairness": "fair" if gini < 0.6 else "concentrated" if gini > 0.8 else "moderate",
            "retail_participation": "high" if retail_share > 0.6 else "low" if retail_share < 0.3 else "moderate",
            "decentralization_level": "high" if gini < 0.5 else "medium" if gini < 0.7 else "low",
            "community_strength": "strong" if retail_share > 0.5 else "weak" if retail_share < 0.3 else "moderate",
        }
    
    def _calculate_onchain_health(self, address_analysis: Dict, transaction_analysis: Dict, network_analysis: Dict) -> Dict[str, Any]:
        """计算链上健康度"""
        scores = []
        
        # 活跃地址得分
        activity_score = address_analysis.get("score", 1.0)
        scores.append(min(activity_score, 1.5) / 1.5)
        
        # 网络健康得分
        uptime = network_analysis.get("network_status", "healthy")
        uptime_score = 1.0 if uptime == "healthy" else 0.7 if uptime == "degraded" else 0.3
        scores.append(uptime_score)
        
        # 交易活动得分
        utilization = transaction_analysis.get("network_utilization", "moderate")
        utilization_score = 0.8 if utilization == "moderate" else 1.0 if utilization == "high" else 0.6
        scores.append(utilization_score)
        
        overall_health = sum(scores) / len(scores) if scores else 0.5
        
        return {
            "overall_score": overall_health,
            "status": "excellent" if overall_health > 0.8 else "good" if overall_health > 0.6 else "fair" if overall_health > 0.4 else "poor",
            "key_metrics": {
                "network_activity": address_analysis.get("activity_level", "unknown"),
                "transaction_volume": transaction_analysis.get("economic_activity", "unknown"),
                "network_stability": network_analysis.get("network_status", "unknown"),
            },
        }
    
    def _analyze_onchain_sentiment(self, flow_analysis: Dict, whale_analysis: Dict, defi_analysis: Dict) -> Dict[str, Any]:
        """分析链上情绪"""
        sentiment_factors = []
        
        # 交易所流量情绪
        exchange_pressure = flow_analysis.get("exchange_pressure", "neutral")
        if exchange_pressure == "buying":
            sentiment_factors.append(0.7)
        elif exchange_pressure == "selling":
            sentiment_factors.append(-0.7)
        else:
            sentiment_factors.append(0.0)
        
        # 巨鲸情绪
        whale_sentiment = whale_analysis.get("whale_sentiment", "neutral")
        if whale_sentiment == "bullish":
            sentiment_factors.append(0.8)
        elif whale_sentiment == "bearish":
            sentiment_factors.append(-0.8)
        else:
            sentiment_factors.append(0.0)
        
        # DeFi采用情绪
        defi_adoption = defi_analysis.get("defi_adoption", "moderate")
        if defi_adoption == "high":
            sentiment_factors.append(0.6)
        elif defi_adoption == "low":
            sentiment_factors.append(-0.3)
        else:
            sentiment_factors.append(0.2)
        
        avg_sentiment = sum(sentiment_factors) / len(sentiment_factors) if sentiment_factors else 0.0
        
        return {
            "sentiment_score": avg_sentiment,
            "sentiment": "bullish" if avg_sentiment > 0.3 else "bearish" if avg_sentiment < -0.3 else "neutral",
            "confidence": min(abs(avg_sentiment) * 1.2, 1.0),
            "key_drivers": [
                f"交易所压力: {exchange_pressure}",
                f"巨鲸情绪: {whale_sentiment}",
                f"DeFi采用: {defi_adoption}",
            ],
        }
    
    def _assess_onchain_risk(self, whale_analysis: Dict, flow_analysis: Dict, network_analysis: Dict) -> Dict[str, Any]:
        """评估链上风险"""
        risk_factors = []
        risk_score = 0.0
        
        # 巨鲸集中度风险
        concentration_risk = whale_analysis.get("concentration_risk", "moderate")
        if concentration_risk == "high":
            risk_score += 0.3
            risk_factors.append("巨鲸集中度过高")
        
        # 网络健康风险
        network_status = network_analysis.get("network_status", "healthy")
        if network_status != "healthy":
            risk_score += 0.2
            risk_factors.append(f"网络状态: {network_status}")
        
        # 流动性风险
        liquidity_trend = flow_analysis.get("liquidity_trend", "stable")
        if liquidity_trend == "decreasing":
            risk_score += 0.2
            risk_factors.append("流动性下降")
        
        return {
            "overall_score": min(risk_score, 1.0),
            "risk_level": "high" if risk_score > 0.6 else "medium" if risk_score > 0.3 else "low",
            "key_risks": risk_factors,
            "risk_categories": {
                "concentration_risk": concentration_risk,
                "network_risk": network_status,
                "liquidity_risk": liquidity_trend,
            },
        }
    
    def _generate_key_insights(self, address_analysis: Dict, transaction_analysis: Dict, flow_analysis: Dict, whale_analysis: Dict) -> List[str]:
        """生成关键洞察"""
        insights = []
        
        # 活跃度洞察
        activity_level = address_analysis.get("activity_level", "unknown")
        insights.append(f"网络活跃度: {activity_level}")
        
        # 交易洞察
        economic_activity = transaction_analysis.get("economic_activity", "unknown")
        insights.append(f"经济活动水平: {economic_activity}")
        
        # 流量洞察
        exchange_pressure = flow_analysis.get("exchange_pressure", "unknown")
        insights.append(f"交易所压力: {exchange_pressure}")
        
        # 巨鲸洞察
        whale_behavior = whale_analysis.get("whale_behavior", "unknown")
        insights.append(f"巨鲸行为: {whale_behavior}")
        
        return insights
    
    def _calculate_confidence(self, onchain_health: Dict, market_sentiment: Dict) -> float:
        """计算分析置信度"""
        health_score = onchain_health.get("overall_score", 0.5)
        sentiment_confidence = market_sentiment.get("confidence", 0.5)
        
        return (health_score + sentiment_confidence) / 2
    
    def _assess_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """评估数据质量"""
        # 检查数据完整性
        required_fields = [
            "active_addresses", "transaction_metrics", "exchange_flows",
            "whale_activity", "network_health"
        ]
        
        completeness = sum(1 for field in required_fields if field in data and data[field]) / len(required_fields)
        
        return {
            "completeness": completeness,
            "quality_score": completeness,
            "data_age": "recent",  # 假设数据是最近的
            "reliability": "high" if completeness > 0.8 else "medium" if completeness > 0.5 else "low",
        }

    
    def _analyze_with_ai(self, traditional_analysis: Dict[str, Any], raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用AI分析链上数据和传统分析结果
        
        Args:
            traditional_analysis: 传统链上分析结果
            raw_data: 原始链上数据
            
        Returns:
            AI增强的链上分析结果
        """
        try:
            # 构建AI分析prompt
            prompt = self._build_onchain_analysis_prompt(traditional_analysis, raw_data)
            
            # 调用AI模型
            ai_response = self._call_llm(prompt)
            
            # 解析AI分析结果
            ai_analysis = self._parse_ai_response(ai_response)
            
            # 结合传统分析和AI分析
            enhanced_analysis = self._combine_onchain_analyses(traditional_analysis, ai_analysis)
            
            return enhanced_analysis
            
        except Exception as e:
            logger.error(f"AI链上分析失败: {e}")
            traditional_analysis["ai_analysis_error"] = str(e)
            return traditional_analysis
    
    def _build_onchain_analysis_prompt(self, traditional_analysis: Dict[str, Any], raw_data: Dict[str, Any]) -> str:
        """构建链上分析AI prompt"""
        
        symbol = raw_data.get("symbol", "未知")
        base_currency = raw_data.get("base_currency", "未知")
        chain = raw_data.get("chain", "未知")
        
        # 提取关键分析结果
        onchain_health = traditional_analysis.get("onchain_health", {})
        market_sentiment = traditional_analysis.get("market_sentiment", {})
        risk_metrics = traditional_analysis.get("risk_metrics", {})
        key_insights = traditional_analysis.get("key_insights", [])
        
        # 提取原始数据
        active_addresses = raw_data.get("active_addresses", {})
        transaction_metrics = raw_data.get("transaction_metrics", {})
        exchange_flows = raw_data.get("exchange_flows", {})
        whale_activity = raw_data.get("whale_activity", {})
        network_health = raw_data.get("network_health", {})
        defi_metrics = raw_data.get("defi_metrics", {})
        
        prompt = f"""你是一位资深的加密货币链上数据分析专家，请基于以下原始链上数据和量化分析结果，对 {symbol} ({base_currency}) 进行深度链上分析。

## 基本信息
- 交易对: {symbol}
- 基础货币: {base_currency}
- 区块链: {chain}
- 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 1. 原始链上数据

### 活跃地址数据
- 日活跃地址: {active_addresses.get('daily_active', 'N/A'):,}
- 周活跃地址: {active_addresses.get('weekly_active', 'N/A'):,}  
- 月活跃地址: {active_addresses.get('monthly_active', 'N/A'):,}
- 7天增长率: {active_addresses.get('growth_rate_7d', 0)*100:.2f}%
- 30天增长率: {active_addresses.get('growth_rate_30d', 0)*100:.2f}%
- 历史平均值: {active_addresses.get('historical_avg', 'N/A'):,}
- 当前百分位: {active_addresses.get('percentile', 'N/A')}%

### 交易指标数据  
- 日交易数: {transaction_metrics.get('daily_transactions', 'N/A'):,}
- 平均手续费: ${transaction_metrics.get('average_fee', 'N/A')}
- 总手续费: ${transaction_metrics.get('total_fees', 'N/A'):,}
- 大额交易数: {transaction_metrics.get('large_transactions', 'N/A'):,}
- 交易增长率: {transaction_metrics.get('transaction_growth', 0)*100:.2f}%
- 手续费趋势: {transaction_metrics.get('fee_trend', 'N/A')}

### 交易所流量数据
- 交易所流入: {exchange_flows.get('exchange_inflows', 'N/A'):,}
- 交易所流出: {exchange_flows.get('exchange_outflows', 'N/A'):,}
- 净流量: {exchange_flows.get('net_flow', 'N/A'):,} ({'净流出' if exchange_flows.get('net_flow', 0) < 0 else '净流入'})
- 交易所余额: {exchange_flows.get('exchange_balance', 'N/A'):,}
- 24小时余额变化: {exchange_flows.get('balance_change_24h', 0)*100:.2f}%
- 流入趋势: {exchange_flows.get('inflow_trend', 'N/A')}
- 流出趋势: {exchange_flows.get('outflow_trend', 'N/A')}

### 巨鲸活动数据
- 巨鲸交易数: {whale_activity.get('whale_transactions', 'N/A')}
- 巨鲸流入: {whale_activity.get('whale_inflows', 'N/A'):,}
- 巨鲸流出: {whale_activity.get('whale_outflows', 'N/A'):,}  
- 巨鲸净流量: {whale_activity.get('net_whale_flow', 'N/A'):,}
- 巨鲸集中度: {whale_activity.get('whale_concentration', 0)*100:.1f}%
- 大持有者数量: {whale_activity.get('large_holder_count', 'N/A'):,}
- 积累模式: {'是' if whale_activity.get('accumulation_pattern', False) else '否'}

### 网络健康数据
{self._format_network_health_data(network_health, base_currency)}

### DeFi生态数据
- 总锁仓价值(TVL): ${defi_metrics.get('tvl', 'N/A'):,}
- DeFi用户数: {defi_metrics.get('defi_users', 'N/A'):,}
- 协议数量: {defi_metrics.get('protocol_count', 'N/A')}
- 借贷量: ${defi_metrics.get('lending_volume', 'N/A'):,}
- DEX交易量: ${defi_metrics.get('dex_volume', 'N/A'):,}
- 流动性挖矿TVL: ${defi_metrics.get('yield_farming_tvl', 'N/A'):,}

## 2. 量化分析结果

### 链上健康度评估
- 综合得分: {onchain_health.get('overall_score', 0):.2f}/1.0
- 健康状态: {onchain_health.get('status', 'unknown')}
- 网络活动水平: {onchain_health.get('key_metrics', {}).get('network_activity', 'unknown')}
- 交易活动水平: {onchain_health.get('key_metrics', {}).get('transaction_volume', 'unknown')}
- 网络稳定性: {onchain_health.get('key_metrics', {}).get('network_stability', 'unknown')}

### 市场情绪分析
- 情绪得分: {market_sentiment.get('sentiment_score', 0):.2f}
- 情绪倾向: {market_sentiment.get('sentiment', 'neutral')}
- 置信度: {market_sentiment.get('confidence', 0)*100:.1f}%
- 关键驱动因素: {', '.join(market_sentiment.get('key_drivers', []))}

### 风险评估
- 风险得分: {risk_metrics.get('overall_score', 0):.2f}/1.0  
- 风险等级: {risk_metrics.get('risk_level', 'unknown')}
- 主要风险: {', '.join(risk_metrics.get('key_risks', []))}

### 关键洞察
{chr(10).join([f'- {insight}' for insight in key_insights])}

## 分析要求

请基于以上数据提供专业的链上分析，包括：

1. **网络健康度深度解读**
   - 分析网络活跃度趋势和质量
   - 评估网络使用增长的可持续性
   - 识别网络发展阶段和成熟度

2. **资金流向分析**
   - 深度解析交易所流量的市场含义
   - 分析巨鲸行为对市场的潜在影响
   - 识别机构vs散户的资金流向模式

3. **DeFi生态评估**（如适用）
   - 分析DeFi锁仓量变化趋势
   - 评估生态系统创新和采用情况
   - 识别DeFi风险和机会

4. **链上情绪判断**
   - 综合各项指标判断当前链上情绪
   - 识别可能的情绪转折信号
   - 分析链上数据与价格的背离情况

5. **投资决策支持**
   - 基于链上数据的中长期投资观点
   - 关键链上指标的监控建议
   - 风险管理和机会识别

6. **市场周期判断**
   - 基于链上数据判断当前市场周期阶段
   - 预测可能的周期转换信号
   - 历史对比和趋势延续性分析

## 输出格式

请以JSON格式输出，包含以下字段：
```json
{{
    "network_health_analysis": {{
        "current_status": "健康/一般/不佳",
        "growth_sustainability": "可持续/放缓/不可持续",
        "network_maturity": "早期/成长期/成熟期",
        "development_trend": "上升/平稳/下降"
    }},
    "capital_flow_analysis": {{
        "exchange_flow_signal": "积累/分发/平衡",
        "whale_behavior_impact": "看涨/看跌/中性",
        "institutional_activity": "增加/减少/稳定",
        "retail_participation": "活跃/一般/低迷"
    }},
    "defi_ecosystem_assessment": {{
        "tvl_trend": "增长/稳定/下降",
        "innovation_level": "高/中/低",
        "adoption_rate": "快速/缓慢/停滞",
        "risk_level": "低/中/高"
    }},
    "onchain_sentiment": {{
        "overall_sentiment": "看涨/看跌/中性",
        "sentiment_strength": 0.0-1.0,
        "divergence_signals": ["信号1", "信号2"],
        "turning_point_probability": 0.0-1.0
    }},
    "investment_recommendation": {{
        "timeframe": "短期/中期/长期",
        "recommendation": "强烈看涨/看涨/中性/看跌/强烈看跌",
        "key_monitoring_metrics": ["指标1", "指标2"],
        "entry_signals": ["信号1", "信号2"],
        "exit_signals": ["信号1", "信号2"]
    }},
    "market_cycle_analysis": {{
        "current_phase": "牛市初期/牛市中期/牛市末期/熊市初期/熊市中期/熊市末期/横盘",
        "cycle_confidence": 0.0-1.0,
        "transition_indicators": ["指标1", "指标2"],
        "historical_comparison": "相似/不同"
    }},
    "risk_opportunities": {{
        "primary_risks": ["风险1", "风险2"],
        "key_opportunities": ["机会1", "机会2"],
        "risk_mitigation": ["策略1", "策略2"]
    }},
    "confidence_assessment": {{
        "analysis_confidence": 0.0-1.0,
        "data_quality_score": 0.0-1.0,
        "prediction_reliability": "高/中/低"
    }},
    "executive_summary": "简洁的分析总结，3-5句话概括关键发现和建议"
}}
```

注意事项：
- 分析要基于数据客观理性，避免主观臆断
- 考虑加密货币市场的高波动性和24/7交易特点
- 重点关注链上数据与价格行为的相关性和背离
- 提供具体的数值阈值和监控建议
- 区分短期噪音和长期趋势信号
"""
        
        return prompt
    
    def _format_network_health_data(self, network_health: Dict[str, Any], currency: str) -> str:
        """格式化网络健康数据"""
        if not network_health:
            return "无网络健康数据"
        
        if currency == "BTC":
            return f"""- 算力: {network_health.get('hash_rate', 'N/A'):,} H/s
- 挖矿难度: {network_health.get('difficulty', 'N/A'):,}
- 挖矿收入: ${network_health.get('mining_revenue', 'N/A'):,}
- 网络节点: {network_health.get('network_nodes', 'N/A'):,}
- 网络正常运行时间: {network_health.get('network_uptime', 0)*100:.2f}%"""
        else:
            return f"""- 活跃验证者: {network_health.get('active_validators', 'N/A'):,}
- 质押率: {network_health.get('staking_rate', 0)*100:.2f}%
- 网络节点: {network_health.get('network_nodes', 'N/A'):,}
- Gas使用率: {network_health.get('gas_usage', 0)*100:.2f}%
- 网络正常运行时间: {network_health.get('network_uptime', 0)*100:.2f}%"""
    
    def _call_llm(self, prompt: str) -> str:
        """调用LLM模型"""
        try:
            from langchain_core.messages import HumanMessage
            
            messages = [HumanMessage(content=prompt)]
            response = self.llm_adapter.invoke(messages)
            
            if hasattr(response, 'content'):
                return response.content
            else:
                return str(response)
                
        except Exception as e:
            logger.error(f"调用LLM失败: {e}")
            raise
    
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
                    "onchain_sentiment": {"overall_sentiment": "中性"},
                    "investment_recommendation": {"recommendation": "中性"}
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
    
    def _combine_onchain_analyses(self, traditional_analysis: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """结合传统链上分析和AI分析"""
        
        # 基础增强分析结构
        enhanced_analysis = {
            "traditional_analysis": traditional_analysis,
            "ai_analysis": ai_analysis,
            "enhanced_insights": {},
            "final_assessment": {}
        }
        
        try:
            # 结合情绪分析
            traditional_sentiment = traditional_analysis.get("market_sentiment", {}).get("sentiment", "neutral")
            ai_sentiment = ai_analysis.get("onchain_sentiment", {}).get("overall_sentiment", "中性")
            
            # 映射中文到英文
            sentiment_mapping = {"看涨": "bullish", "看跌": "bearish", "中性": "neutral"}
            ai_sentiment_en = sentiment_mapping.get(ai_sentiment, "neutral")
            
            sentiment_agreement = traditional_sentiment == ai_sentiment_en
            
            # 结合置信度
            traditional_confidence = traditional_analysis.get("confidence", 0.5)
            ai_confidence = ai_analysis.get("confidence_assessment", {}).get("analysis_confidence", 0.5)
            
            # 计算综合置信度
            if sentiment_agreement:
                combined_confidence = min((traditional_confidence + ai_confidence) / 2 * 1.15, 1.0)
            else:
                combined_confidence = (traditional_confidence + ai_confidence) / 2 * 0.85
            
            # 增强洞察
            enhanced_analysis["enhanced_insights"] = {
                "sentiment_consensus": {
                    "traditional": traditional_sentiment,
                    "ai": ai_sentiment,
                    "agreement": sentiment_agreement,
                    "final_sentiment": traditional_sentiment if sentiment_agreement else "uncertain"
                },
                "confidence_assessment": {
                    "traditional": traditional_confidence,
                    "ai": ai_confidence,
                    "combined": combined_confidence,
                    "reliability": "high" if combined_confidence > 0.75 else "medium" if combined_confidence > 0.55 else "low"
                },
                "network_health": ai_analysis.get("network_health_analysis", {}),
                "capital_flows": ai_analysis.get("capital_flow_analysis", {}),
                "defi_ecosystem": ai_analysis.get("defi_ecosystem_assessment", {}),
                "market_cycle": ai_analysis.get("market_cycle_analysis", {})
            }
            
            # 最终评估
            ai_recommendation = ai_analysis.get("investment_recommendation", {}).get("recommendation", "中性")
            recommendation_mapping = {
                "强烈看涨": "strong_bullish", "看涨": "bullish", "中性": "neutral", 
                "看跌": "bearish", "强烈看跌": "strong_bearish"
            }
            ai_rec_en = recommendation_mapping.get(ai_recommendation, "neutral")
            
            enhanced_analysis["final_assessment"] = {
                "overall_recommendation": ai_rec_en,
                "confidence": combined_confidence,
                "key_risks": ai_analysis.get("risk_opportunities", {}).get("primary_risks", []),
                "key_opportunities": ai_analysis.get("risk_opportunities", {}).get("key_opportunities", []),
                "monitoring_metrics": ai_analysis.get("investment_recommendation", {}).get("key_monitoring_metrics", []),
                "timeframe": ai_analysis.get("investment_recommendation", {}).get("timeframe", "中期"),
                "executive_summary": ai_analysis.get("executive_summary", "AI分析完成"),
                "data_quality": traditional_analysis.get("data_quality", {}),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"结合链上分析失败: {e}")
            enhanced_analysis["combination_error"] = str(e)
            enhanced_analysis["final_assessment"] = {
                "overall_recommendation": "neutral",
                "confidence": 0.5,
                "error": str(e)
            }
        
        return enhanced_analysis
