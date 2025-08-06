"""
DeFi分析师 - 专注去中心化金融协议分析

基于原版分析架构，针对DeFi协议和流动性池分析优化
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

class DefiAnalyst(StandardAIAnalysisMixin):
    """加密货币DeFi分析师"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化DeFi分析师
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.defi_protocols = config.get("defi_config", {}).get("protocols", [])
        self.supported_chains = config.get("defi_config", {}).get("supported_chains", [])
        
        # DeFi指标权重
        self.defi_weights = {
            "tvl": 0.30,
            "liquidity_pools": 0.25,
            "yield_farming": 0.20,
            "governance": 0.15,
            "protocol_health": 0.10,
        }
        
        # 初始化AI分析混入类
        super().__init__()
        
        # 初始化LLM服务（如果还未初始化）
        llm_service_config = config.get("llm_service_config")
        if llm_service_config:
            initialize_llm_service(llm_service_config)
            logger.info("DefiAnalyst: 统一LLM服务初始化完成")

    def collect_data(self, symbol: str, end_date: str) -> Dict[str, Any]:
        """
        收集DeFi数据
        
        Args:
            symbol: 交易对符号
            end_date: 截止日期
            
        Returns:
            DeFi数据
        """
        try:
            # TODO: 实现真实的DeFi数据收集逻辑
            # 这里使用模拟数据
            
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            start_dt = end_dt - timedelta(days=7)
            
            # 提取币种基础信息
            base_currency = symbol.split('/')[0]
            
            return {
                "symbol": symbol,
                "base_currency": base_currency,
                "start_date": start_dt.strftime("%Y-%m-%d"),
                "end_date": end_date,
                "protocol_data": self._generate_protocol_data(base_currency),
                "liquidity_pools": self._generate_liquidity_pools_data(base_currency),
                "yield_farming": self._generate_yield_farming_data(base_currency),
                "governance_data": self._generate_governance_data(base_currency),
                "defi_aggregators": self._generate_aggregator_data(base_currency),
            }
            
        except Exception as e:
            logger.error(f"Error collecting DeFi data for {symbol}: {str(e)}")
            return {"error": str(e)}
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析DeFi数据
        
        Args:
            data: DeFi数据
            
        Returns:
            DeFi分析结果
        """
        try:
            if "error" in data:
                return {"error": data["error"]}
            
            # 使用统一的AI增强分析流程
            return self.analyze_with_ai_enhancement(data, self._traditional_analyze)
            
        except Exception as e:
            logger.error(f"Error analyzing DeFi data: {str(e)}")
            return {"error": str(e)}

    def _traditional_analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        传统DeFi分析方法
        
        Args:
            data: DeFi数据
            
        Returns:
            传统分析结果
        """
        protocol_data = data.get("protocol_data", {})
        liquidity_pools = data.get("liquidity_pools", {})
        yield_farming = data.get("yield_farming", {})
        governance_data = data.get("governance_data", {})
        defi_aggregators = data.get("defi_aggregators", {})
        
        # 分析TVL趋势
        tvl_analysis = self._analyze_tvl(protocol_data)
        
        # 分析流动性池
        pool_analysis = self._analyze_liquidity_pools(liquidity_pools)
        
        # 分析挖矿收益
        yield_analysis = self._analyze_yield_farming(yield_farming)
        
        # 分析治理
        governance_analysis = self._analyze_governance(governance_data)
        
        # 分析协议健康度
        protocol_health = self._analyze_protocol_health(protocol_data)
        
        # 风险评估
        risk_metrics = self._assess_defi_risk(
            tvl_analysis, pool_analysis, yield_analysis, protocol_health
        )
        
        # 生成DeFi信号
        defi_signals = self._generate_defi_signals(
            tvl_analysis, yield_analysis, pool_analysis, governance_analysis
        )
        
        return {
            "tvl_analysis": tvl_analysis,
            "pool_analysis": pool_analysis,
            "yield_analysis": yield_analysis,
            "governance_analysis": governance_analysis,
            "protocol_health": protocol_health,
            "risk_metrics": risk_metrics,
            "defi_signals": defi_signals,
            "confidence": self._calculate_confidence(defi_signals),
            "key_observations": self._generate_key_observations(
                tvl_analysis, yield_analysis, pool_analysis
            ),
            "data_quality": self._assess_data_quality(data),
        }
    
    def _generate_protocol_data(self, base_currency: str) -> Dict[str, Any]:
        """生成协议数据"""
        protocols = ["uniswap", "aave", "compound", "curve", "sushiswap"]
        protocol_data = {}
        
        for protocol in protocols:
            base_tvl = 1000000000 if protocol == "uniswap" else 500000000
            
            protocol_data[protocol] = {
                "tvl": base_tvl * (1 + (hash(base_currency + protocol) % 1000 - 500) / 10000),
                "tvl_change_24h": (hash(base_currency + protocol) % 200 - 100) / 10000,
                "users": int(base_tvl / 10000 * (1 + (hash(base_currency + protocol) % 200 - 100) / 1000)),
                "transactions_24h": int(base_tvl / 1000 * (1 + (hash(base_currency + protocol) % 300 - 150) / 1000)),
                "fees_24h": base_tvl * 0.0002 * (1 + (hash(base_currency + protocol) % 100 - 50) / 1000),
                "revenue_24h": base_tvl * 0.00015 * (1 + (hash(base_currency + protocol) % 100 - 50) / 1000),
                "market_cap": base_tvl * 8,
                "price_tvl_ratio": 8.0,
            }
        
        return protocol_data
    
    def _generate_liquidity_pools_data(self, base_currency: str) -> Dict[str, Any]:
        """生成流动性池数据"""
        pools = []
        
        # 主要交易对
        main_pairs = [f"{base_currency}/USDT", f"{base_currency}/USDC", f"{base_currency}/ETH"]
        
        for pair in main_pairs:
            base_liquidity = 50000000 if base_currency == "ETH" else 10000000
            
            pools.append({
                "pair": pair,
                "tvl": base_liquidity * (1 + (hash(base_currency + pair) % 400 - 200) / 10000),
                "volume_24h": base_liquidity * 0.1 * (1 + (hash(base_currency + pair) % 600 - 300) / 10000),
                "fees_24h": base_liquidity * 0.1 * 0.003 * (1 + (hash(base_currency + pair) % 200 - 100) / 10000),
                "apy": 0.05 + (hash(base_currency + pair) % 1000 - 500) / 20000,
                "liquidity_utilization": 0.7 + (hash(base_currency + pair) % 400 - 200) / 2000,
                "impermanent_loss": 0.02 + (hash(base_currency + pair) % 100 - 50) / 5000,
                "concentration": "high" if base_currency == "ETH" else "medium",
            })
        
        return {
            "pools": pools,
            "total_pool_tvl": sum(pool["tvl"] for pool in pools),
            "average_apy": sum(pool["apy"] for pool in pools) / len(pools),
            "total_volume_24h": sum(pool["volume_24h"] for pool in pools),
        }
    
    def _generate_yield_farming_data(self, base_currency: str) -> Dict[str, Any]:
        """生成挖矿数据"""
        farms = []
        
        farm_types = ["single_stake", "lp_farm", "governance_stake"]
        
        for farm_type in farm_types:
            base_apy = 0.15 if farm_type == "governance_stake" else 0.08
            
            farms.append({
                "type": farm_type,
                "total_tvl": 20000000 * (1 + (hash(base_currency + farm_type) % 400 - 200) / 10000),
                "apy": base_apy + (hash(base_currency + farm_type) % 1000 - 500) / 20000,
                "reward_tokens": [base_currency, "USDT"],
                "lock_period": 0 if farm_type == "single_stake" else 7 if farm_type == "lp_farm" else 30,
                "risk_level": "low" if farm_type == "single_stake" else "medium" if farm_type == "lp_farm" else "high",
                "tvl_change_24h": (hash(base_currency + farm_type) % 400 - 200) / 10000,
            })
        
        return {
            "farms": farms,
            "total_farm_tvl": sum(farm["total_tvl"] for farm in farms),
            "average_apy": sum(farm["apy"] for farm in farms) / len(farms),
            "highest_apy": max(farm["apy"] for farm in farms),
            "lowest_apy": min(farm["apy"] for farm in farms),
        }
    
    def _generate_governance_data(self, base_currency: str) -> Dict[str, Any]:
        """生成治理数据"""
        return {
            "token_holders": 45000,
            "active_voters": 8500,
            "voter_participation": 0.189,
            "governance_tokens_locked": 25000000,
            "governance_tvl": 450000000,
            "proposals_30d": 12,
            "approved_proposals": 8,
            "rejected_proposals": 3,
            "pending_proposals": 1,
            "governance_health": "good",
            "proposal_success_rate": 0.667,
            "voter_concentration": 0.25,
        }
    
    def _generate_aggregator_data(self, base_currency: str) -> Dict[str, Any]:
        """生成聚合器数据"""
        aggregators = ["1inch", "matcha", "paraSwap"]
        
        aggregator_data = {}
        for aggregator in aggregators:
            base_volume = 100000000
            
            aggregator_data[aggregator] = {
                "volume_24h": base_volume * (1 + (hash(base_currency + aggregator) % 400 - 200) / 10000),
                "trades_24h": int(base_volume / 1000 * (1 + (hash(base_currency + aggregator) % 300 - 150) / 1000)),
                "avg_slippage": 0.002 + (hash(base_currency + aggregator) % 100 - 50) / 50000,
                "gas_savings": 0.15 + (hash(base_currency + aggregator) % 100 - 50) / 1000,
                "market_share": 0.25 + (hash(base_currency + aggregator) % 200 - 100) / 1000,
            }
        
        return aggregator_data
    
    def _analyze_tvl(self, protocol_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析TVL"""
        total_tvl = sum(data["tvl"] for data in protocol_data.values())
        
        # 计算TVL变化
        weighted_tvl_change = sum(
            data["tvl"] * data["tvl_change_24h"] for data in protocol_data.values()
        ) / total_tvl if total_tvl > 0 else 0
        
        # 分析TVL分布
        tvl_distribution = {}
        for protocol, data in protocol_data.items():
            tvl_distribution[protocol] = data["tvl"] / total_tvl if total_tvl > 0 else 0
        
        # 计算集中度
        max_share = max(tvl_distribution.values()) if tvl_distribution else 0
        concentration = max_share
        
        # 评估TVL趋势
        if weighted_tvl_change > 0.05:
            trend = "strong_growth"
        elif weighted_tvl_change > 0.02:
            trend = "moderate_growth"
        elif weighted_tvl_change > -0.02:
            trend = "stable"
        elif weighted_tvl_change > -0.05:
            trend = "moderate_decline"
        else:
            trend = "strong_decline"
        
        return {
            "total_tvl": total_tvl,
            "tvl_change_24h": weighted_tvl_change,
            "trend": trend,
            "distribution": tvl_distribution,
            "concentration": concentration,
            "concentration_level": "high" if concentration > 0.5 else "medium" if concentration > 0.3 else "low",
        }
    
    def _analyze_liquidity_pools(self, liquidity_pools: Dict[str, Any]) -> Dict[str, Any]:
        """分析流动性池"""
        pools = liquidity_pools.get("pools", [])
        
        if not pools:
            return {"health": "poor", "average_apy": 0.0}
        
        # 计算平均APY和利用率
        avg_apy = sum(pool["apy"] for pool in pools) / len(pools)
        avg_utilization = sum(pool["liquidity_utilization"] for pool in pools) / len(pools)
        
        # 分析池健康度
        healthy_pools = sum(1 for pool in pools if pool["liquidity_utilization"] < 0.8 and pool["apy"] > 0.02)
        pool_health_ratio = healthy_pools / len(pools)
        
        # 评估整体健康度
        if pool_health_ratio > 0.8 and avg_utilization < 0.7:
            health = "excellent"
        elif pool_health_ratio > 0.6 and avg_utilization < 0.8:
            health = "good"
        elif pool_health_ratio > 0.4:
            health = "fair"
        else:
            health = "poor"
        
        # 分析收益风险比
        avg_il = sum(pool["impermanent_loss"] for pool in pools) / len(pools)
        risk_adjusted_yield = avg_apy - avg_il
        
        return {
            "health": health,
            "total_pools": len(pools),
            "average_apy": avg_apy,
            "average_utilization": avg_utilization,
            "healthy_pool_ratio": pool_health_ratio,
            "risk_adjusted_yield": risk_adjusted_yield,
            "yield_quality": "high" if risk_adjusted_yield > 0.05 else "medium" if risk_adjusted_yield > 0.02 else "low",
            "liquidity_efficiency": "high" if avg_utilization > 0.6 and avg_utilization < 0.8 else "medium",
        }
    
    def _analyze_yield_farming(self, yield_farming: Dict[str, Any]) -> Dict[str, Any]:
        """分析挖矿收益"""
        farms = yield_farming.get("farms", [])
        
        if not farms:
            return {"attractiveness": "low", "sustainability": "unknown"}
        
        avg_apy = yield_farming.get("average_apy", 0.0)
        total_tvl = yield_farming.get("total_farm_tvl", 0.0)
        
        # 分析收益可持续性
        high_apy_farms = sum(1 for farm in farms if farm["apy"] > 0.2)
        high_apy_ratio = high_apy_farms / len(farms)
        
        # 评估收益吸引力
        if avg_apy > 0.15 and high_apy_ratio < 0.3:
            attractiveness = "very_attractive"
        elif avg_apy > 0.1:
            attractiveness = "attractive"
        elif avg_apy > 0.05:
            attractiveness = "moderate"
        else:
            attractiveness = "low"
        
        # 评估可持续性
        if high_apy_ratio > 0.5:
            sustainability = "questionable"  # 可能不可持续的高收益
        elif high_apy_ratio > 0.3:
            sustainability = "moderate"
        else:
            sustainability = "good"
        
        # 分析风险分布
        risk_distribution = {}
        for farm in farms:
            risk_level = farm["risk_level"]
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
        
        return {
            "attractiveness": attractiveness,
            "sustainability": sustainability,
            "average_apy": avg_apy,
            "total_tvl": total_tvl,
            "high_apy_ratio": high_apy_ratio,
            "risk_distribution": risk_distribution,
            "diversification": "good" if len(risk_distribution) > 2 else "limited",
        }
    
    def _analyze_governance(self, governance_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析治理"""
        participation = governance_data.get("voter_participation", 0.0)
        success_rate = governance_data.get("proposal_success_rate", 0.0)
        concentration = governance_data.get("voter_concentration", 0.0)
        
        # 评估治理健康度
        governance_health = 0.0
        
        # 参与度评分
        if participation > 0.2:
            governance_health += 0.3
        elif participation > 0.1:
            governance_health += 0.2
        elif participation > 0.05:
            governance_health += 0.1
        
        # 提案成功率评分
        if 0.5 <= success_rate <= 0.8:
            governance_health += 0.3
        elif 0.3 <= success_rate <= 0.9:
            governance_health += 0.2
        
        # 去中心化程度评分
        if concentration < 0.2:
            governance_health += 0.4
        elif concentration < 0.4:
            governance_health += 0.3
        elif concentration < 0.6:
            governance_health += 0.1
        
        # 评估治理质量
        if governance_health > 0.8:
            quality = "excellent"
        elif governance_health > 0.6:
            quality = "good"
        elif governance_health > 0.4:
            quality = "fair"
        else:
            quality = "poor"
        
        return {
            "health_score": governance_health,
            "quality": quality,
            "participation_rate": participation,
            "proposal_success_rate": success_rate,
            "voter_concentration": concentration,
            "decentralization_level": "high" if concentration < 0.2 else "medium" if concentration < 0.4 else "low",
            "community_engagement": "high" if participation > 0.15 else "medium" if participation > 0.05 else "low",
        }
    
    def _analyze_protocol_health(self, protocol_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析协议健康度"""
        health_metrics = {}
        
        for protocol, data in protocol_data.items():
            # 计算协议健康分数
            health_score = 0.5
            
            # TVL增长
            if data["tvl_change_24h"] > 0.05:
                health_score += 0.2
            elif data["tvl_change_24h"] > 0.02:
                health_score += 0.1
            elif data["tvl_change_24h"] < -0.02:
                health_score -= 0.1
            
            # 价格TVL比率
            price_tvl_ratio = data.get("price_tvl_ratio", 8.0)
            if 5.0 <= price_tvl_ratio <= 15.0:
                health_score += 0.2
            elif 3.0 <= price_tvl_ratio <= 20.0:
                health_score += 0.1
            
            # 用户活跃度
            user_activity = data["transactions_24h"] / max(data["users"], 1)
            if user_activity > 0.1:
                health_score += 0.1
            
            health_metrics[protocol] = {
                "score": min(1.0, max(0.0, health_score)),
                "tvl_growth": data["tvl_change_24h"],
                "user_activity": user_activity,
                "revenue_efficiency": data["revenue_24h"] / max(data["tvl"], 1),
            }
        
        # 计算整体健康度
        avg_health = sum(metrics["score"] for metrics in health_metrics.values()) / len(health_metrics) if health_metrics else 0.5
        
        return {
            "overall_health": avg_health,
            "health_level": "excellent" if avg_health > 0.8 else "good" if avg_health > 0.6 else "fair" if avg_health > 0.4 else "poor",
            "protocol_health": health_metrics,
            "healthy_protocols": sum(1 for metrics in health_metrics.values() if metrics["score"] > 0.6),
            "total_protocols": len(health_metrics),
        }
    
    def _assess_defi_risk(self, tvl_analysis: Dict[str, Any],
                         pool_analysis: Dict[str, Any],
                         yield_analysis: Dict[str, Any],
                         protocol_health: Dict[str, Any]) -> Dict[str, Any]:
        """评估DeFi风险"""
        risk_score = 0.0
        risk_factors = []
        
        # TVL集中度风险
        concentration = tvl_analysis.get("concentration", 0.0)
        if concentration > 0.5:
            risk_score += 0.2
            risk_factors.append("TVL过度集中")
        
        # 流动性池风险
        pool_health = pool_analysis.get("health", "unknown")
        if pool_health in ["poor", "fair"]:
            risk_score += 0.2
            risk_factors.append("流动性池健康度不佳")
        
        # 收益可持续性风险
        sustainability = yield_analysis.get("sustainability", "unknown")
        if sustainability == "questionable":
            risk_score += 0.3
            risk_factors.append("收益可持续性存疑")
        
        # 协议健康风险
        overall_health = protocol_health.get("overall_health", 0.5)
        if overall_health < 0.4:
            risk_score += 0.2
            risk_factors.append("协议整体健康度低")
        
        return {
            "overall_score": min(risk_score, 1.0),
            "risk_level": "high" if risk_score > 0.5 else "medium" if risk_score > 0.2 else "low",
            "key_risks": risk_factors,
        }
    
    def _generate_defi_signals(self, tvl_analysis: Dict[str, Any],
                               yield_analysis: Dict[str, Any],
                               pool_analysis: Dict[str, Any],
                               governance_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成DeFi信号"""
        signals = {
            "bullish_signals": [],
            "bearish_signals": [],
            "neutral_signals": [],
        }
        
        # 基于TVL趋势
        tvl_trend = tvl_analysis.get("trend", "stable")
        if "growth" in tvl_trend:
            signals["bullish_signals"].append("TVL增长趋势")
        elif "decline" in tvl_trend:
            signals["bearish_signals"].append("TVL下降趋势")
        
        # 基于收益吸引力
        attractiveness = yield_analysis.get("attractiveness", "unknown")
        if attractiveness in ["very_attractive", "attractive"]:
            signals["bullish_signals"].append("挖矿收益吸引力高")
        elif attractiveness == "low":
            signals["bearish_signals"].append("挖矿收益吸引力低")
        
        # 基于流动性池健康度
        pool_health = pool_analysis.get("health", "unknown")
        if pool_health in ["excellent", "good"]:
            signals["bullish_signals"].append("流动性池健康度高")
        elif pool_health == "poor":
            signals["bearish_signals"].append("流动性池健康度低")
        
        # 基于治理质量
        governance_quality = governance_analysis.get("quality", "unknown")
        if governance_quality in ["excellent", "good"]:
            signals["bullish_signals"].append("治理质量优秀")
        elif governance_quality == "poor":
            signals["bearish_signals"].append("治理质量较差")
        
        return signals
    
    def _calculate_confidence(self, defi_signals: Dict[str, Any]) -> float:
        """计算分析置信度"""
        total_signals = len(defi_signals["bullish_signals"]) + len(defi_signals["bearish_signals"])
        
        if total_signals == 0:
            return 0.3
        
        # 基于信号一致性
        signal_consistency = abs(len(defi_signals["bullish_signals"]) - len(defi_signals["bearish_signals"])) / total_signals
        
        return signal_consistency
    
    def _generate_key_observations(self, tvl_analysis: Dict[str, Any],
                                   yield_analysis: Dict[str, Any],
                                   pool_analysis: Dict[str, Any]) -> List[str]:
        """生成关键观察"""
        observations = []
        
        # TVL观察
        tvl_trend = tvl_analysis.get("trend", "unknown")
        observations.append(f"TVL趋势: {tvl_trend}")
        
        # 收益观察
        attractiveness = yield_analysis.get("attractiveness", "unknown")
        observations.append(f"收益吸引力: {attractiveness}")
        
        # 流动性池观察
        pool_health = pool_analysis.get("health", "unknown")
        observations.append(f"流动性池健康度: {pool_health}")
        
        return observations

    def _assess_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """评估DeFi数据质量"""
        required_fields = [
            "protocol_data", "liquidity_pools", "yield_farming",
            "governance_data", "defi_aggregators"
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
        使用AI进行DeFi分析增强
        
        Args:
            traditional_analysis: 传统分析结果
            raw_data: 原始数据
            
        Returns:
            AI分析结果
        """
        try:
            # 构建DeFi分析prompt
            prompt = self._build_defi_analysis_prompt(traditional_analysis, raw_data)
            
            # 调用统一LLM服务
            ai_response = self.call_ai_analysis(prompt)
            
            # 解析AI响应
            ai_analysis = self.parse_ai_json_response(ai_response, {
                "defi_ecosystem_health": {"overall_health": "未知", "growth_sustainability": "未知"},
                "protocol_risk_assessment": {"systemic_risk": "中", "smart_contract_risk": "中"},
                "tvl_analysis": {"trend_direction": "稳定", "sustainability_score": 0.5},
                "yield_sustainability": {"current_yields_sustainable": "未知", "risk_adjusted_return": 0.5},
                "capital_efficiency": {"utilization_rate": 0.5, "efficiency_score": 0.5},
                "governance_maturity": {"decentralization_score": 0.5, "community_engagement": "中"},
                "confidence_level": 0.5,
                "key_insights": ["AI分析不可用"]
            })
            
            return ai_analysis
            
        except Exception as e:
            logger.error(f"DefiAnalyst: AI分析失败: {str(e)}")
            raise

    def _build_defi_analysis_prompt(self, traditional_analysis: Dict[str, Any], raw_data: Dict[str, Any]) -> str:
        """构建DeFi分析AI提示词"""
        
        # 使用标准化prompt构建方法
        analysis_dimensions = [
            "DeFi生态健康度 - 评估整体生态系统的健康状况和发展可持续性",
            "协议风险评估 - 识别智能合约风险、系统性风险和协议特定风险",
            "TVL深度分析 - 分析总锁仓价值的真实性、流动性和增长驱动力",
            "收益率可持续性 - 评估当前收益率的可持续性和风险调整后回报",
            "资金效率分析 - 分析资金利用率、流动性挖矿效率和资本配置",
            "治理成熟度 - 评估去中心化程度、社区参与度和治理机制有效性",
            "创新趋势识别 - 识别DeFi领域的新兴趋势、技术突破和市场机会"
        ]
        
        output_fields = [
            "defi_ecosystem_health",
            "protocol_risk_assessment",
            "tvl_analysis",
            "yield_sustainability",
            "capital_efficiency",
            "governance_maturity",
            "innovation_trends",
            "confidence_level",
            "key_insights"
        ]
        
        return self._build_standard_analysis_prompt(
            "DeFi生态分析师",
            traditional_analysis,
            raw_data,
            analysis_dimensions,
            output_fields
        )

    def _format_protocol_data(self, protocol_data: Dict[str, Any]) -> str:
        """格式化协议数据"""
        if not protocol_data:
            return "无协议数据"
        
        formatted = []
        for protocol, data in protocol_data.items():
            formatted.append(f"""
{protocol.upper()}:
  - TVL: ${data.get('tvl', 0):,.0f}
  - 24小时变化: {data.get('tvl_change_24h', 0)*100:.2f}%
  - 日活用户: {data.get('users', 0):,}
  - 24小时交易数: {data.get('transactions_24h', 0):,}
  - 24小时手续费: ${data.get('fees_24h', 0):,.0f}
  - 24小时收入: ${data.get('revenue_24h', 0):,.0f}
  - 市值: ${data.get('market_cap', 0):,.0f}
  - 价格/TVL比率: {data.get('price_tvl_ratio', 0):.1f}""")
        
        return "\n".join(formatted)

    def _format_pool_details(self, pools: List[Dict[str, Any]]) -> str:
        """格式化池详情"""
        if not pools:
            return "无池数据"
        
        formatted = []
        for pool in pools[:5]:  # 只显示前5个池
            formatted.append(f"""
  {pool.get('pair', 'Unknown')}:
    - TVL: ${pool.get('tvl', 0):,.0f}
    - 24小时交易量: ${pool.get('volume_24h', 0):,.0f}
    - APY: {pool.get('apy', 0)*100:.2f}%
    - 流动性利用率: {pool.get('liquidity_utilization', 0)*100:.1f}%
    - 无常损失: {pool.get('impermanent_loss', 0)*100:.2f}%""")
        
        return "\n".join(formatted)

    def _format_farming_details(self, farms: List[Dict[str, Any]]) -> str:
        """格式化挖矿详情"""
        if not farms:
            return "无挖矿数据"
        
        formatted = []
        for farm in farms:
            formatted.append(f"""
  {farm.get('type', 'Unknown')}:
    - TVL: ${farm.get('total_tvl', 0):,.0f}
    - APY: {farm.get('apy', 0)*100:.2f}%
    - 锁定期: {farm.get('lock_period', 0)}天
    - 风险等级: {farm.get('risk_level', '未知')}
    - 奖励代币: {', '.join(farm.get('reward_tokens', []))}""")
        
        return "\n".join(formatted)

    def _format_aggregator_data(self, aggregators: Dict[str, Any]) -> str:
        """格式化聚合器数据"""
        if not aggregators:
            return "无聚合器数据"
        
        formatted = []
        for aggregator, data in aggregators.items():
            formatted.append(f"""
{aggregator}:
  - 24小时交易量: ${data.get('volume_24h', 0):,.0f}
  - 24小时交易数: {data.get('trades_24h', 0):,}
  - 平均滑点: {data.get('avg_slippage', 0)*100:.3f}%
  - Gas节省: {data.get('gas_savings', 0)*100:.1f}%
  - 市场份额: {data.get('market_share', 0)*100:.1f}%""")
        
        return "\n".join(formatted)

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
                confidence_weight_ai=0.65  # AI在DeFi分析中的权重
            )
            
            # 添加DeFi分析特定的增强字段
            enhanced_analysis.update({
                "ai_ecosystem_health": ai_analysis.get("defi_ecosystem_health", {}),
                "ai_protocol_risks": ai_analysis.get("protocol_risk_assessment", {}),
                "ai_tvl_analysis": ai_analysis.get("tvl_analysis", {}),
                "ai_yield_sustainability": ai_analysis.get("yield_sustainability", {}),
                "ai_capital_efficiency": ai_analysis.get("capital_efficiency", {}),
                "ai_governance_maturity": ai_analysis.get("governance_maturity", {}),
                "ai_innovation_trends": ai_analysis.get("innovation_trends", {}),
                "ai_key_insights": ai_analysis.get("key_insights", [])
            })
            
            return enhanced_analysis
            
        except Exception as e:
            logger.error(f"DefiAnalyst: 分析结果组合失败: {str(e)}")
            # 发生错误时返回传统分析结果
            fallback_analysis = traditional_analysis.copy()
            fallback_analysis["ai_enhanced"] = False
            fallback_analysis["combine_error"] = str(e)
            return fallback_analysis

    def _format_traditional_analysis_summary(self, traditional_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """格式化传统分析结果摘要（重写父类方法）"""
        return {
            "TVL分析": traditional_analysis.get("tvl_analysis", {}),
            "流动性池分析": traditional_analysis.get("pool_analysis", {}),
            "收益挖矿分析": traditional_analysis.get("yield_analysis", {}),
            "治理分析": traditional_analysis.get("governance_analysis", {}),
            "协议健康度": traditional_analysis.get("protocol_health", {}),
            "风险评估": traditional_analysis.get("risk_metrics", {}),
            "置信度": traditional_analysis.get("confidence", 0)
        }

    def _format_raw_data_summary(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化原始数据摘要（重写父类方法）"""
        return {
            "协议数据": raw_data.get("protocol_data", {}),
            "流动性池": raw_data.get("liquidity_pools", {}),
            "收益挖矿": raw_data.get("yield_farming", {}),
            "治理数据": raw_data.get("governance_data", {}),
            "聚合器数据": raw_data.get("defi_aggregators", {})
        }
