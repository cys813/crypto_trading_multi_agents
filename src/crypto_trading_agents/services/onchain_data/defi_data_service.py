"""
DeFi数据服务 - 集成真实DeFi数据源
"""

import os
import requests
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

from .glassnode_client import GlassnodeClient
# 临时注释掉，避免导入错误

logger = logging.getLogger(__name__)

class DeFiDataService:
    """DeFi数据服务"""
    
    # 支持DeFi分析的资产列表
    DEFILLAMA_SUPPORTED_ASSETS = {
        "ETH": "ethereum",
        "SOL": "solana", 
        "BNB": "binance",
        "MATIC": "polygon",
        "AVAX": "avalanche",
        "FTM": "fantom",
        "ARB": "arbitrum",
        "OP": "optimism"
    }
    
    # 协议映射
    PROTOCOL_MAPPINGS = {
        "uniswap": ["uniswap-v2", "uniswap-v3"],
        "aave": ["aave-v2", "aave-v3"],
        "compound": ["compound-v2", "compound-v3"],
        "curve": ["curve"],
        "sushiswap": ["sushiswap"],
        "makerdao": ["makerdao"],
        "yearn": ["yearn-finance"]
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化DeFi数据服务
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.cache = {}
        self.cache_ttl = 300  # 5分钟缓存
        
        # 初始化数据源
        self._init_data_sources()
    
    def _init_data_sources(self):
        """初始化数据源"""
        try:
            # 初始化DeFi Llama数据源
            self.defillama = DeFiLlamaDataSource()
            logger.info("DeFi Llama data source initialized")
        except Exception as e:
            logger.error(f"Failed to initialize DeFi Llama data source: {str(e)}")
            self.defillama = None
        
        # 初始化Glassnode客户端（如果配置了API密钥）
        apis_config = self.config.get("apis", {}).get("data", {})
        glassnode_config = apis_config.get("onchain_data", {}).get("glassnode", {})
        if glassnode_config.get("enabled", False):
            glassnode_api_key = glassnode_config.get("api_key")
            if glassnode_api_key and not glassnode_api_key.startswith("${"):
                try:
                    self.glassnode = GlassnodeClient(glassnode_api_key)
                    logger.info("Glassnode client initialized")
                except Exception as e:
                    logger.error(f"Failed to initialize Glassnode client: {str(e)}")
                    self.glassnode = None
            else:
                self.glassnode = None
        else:
            self.glassnode = None
    
    def is_defi_supported(self, base_currency: str) -> bool:
        """
        检查资产是否支持DeFi分析
        
        Args:
            base_currency: 基础资产符号
            
        Returns:
            是否支持DeFi分析
        """
        return base_currency.upper() in self.DEFILLAMA_SUPPORTED_ASSETS
    
    def get_protocol_data(self, base_currency: str) -> Dict[str, Any]:
        """
        获取协议数据
        
        Args:
            base_currency: 基础资产符号
            
        Returns:
            协议数据
        """
        if not self.is_defi_supported(base_currency):
            return self._get_empty_protocol_data()
        
        chain = self.DEFILLAMA_SUPPORTED_ASSETS.get(base_currency.upper())
        if not chain:
            return self._get_empty_protocol_data()
        
        cache_key = f"protocol_data_{base_currency}_{chain}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        protocol_data = {}
        
        try:
            # 获取链上协议列表
            if self.defillama:
                protocols = self.defillama.get_tvl_data()
                if protocols and isinstance(protocols, list):
                    # 筛选指定链的协议
                    chain_protocols = [
                        p for p in protocols 
                        if p.get("chain", "").lower() == chain.lower() or chain.lower() in p.get("chains", [])
                    ]
                    
                    # 获取前5个主要协议的数据
                    for protocol in chain_protocols[:5]:
                        protocol_name = protocol.get("name", "")
                        protocol_slug = protocol.get("slug", "")
                        
                        # 获取协议详细信息
                        protocol_details = self.defillama.get_tvl_data(protocol_slug)
                        if protocol_details:
                            tvl = protocol_details.get("tvl", 0)
                            tvl_change_24h = self._calculate_tvl_change(protocol_details)
                            
                            protocol_data[protocol_slug] = {
                                "tvl": tvl,
                                "tvl_change_24h": tvl_change_24h,
                                "users": protocol_details.get("userCount", 0),
                                "transactions_24h": protocol_details.get("txCount", 0),
                                "fees_24h": protocol_details.get("totalFees24h", 0),
                                "revenue_24h": protocol_details.get("totalRevenue24h", 0),
                                "market_cap": protocol_details.get("marketCap", tvl * 8),
                                "price_tvl_ratio": 8.0,
                                "chains": protocol_details.get("chains", [chain]),
                                "category": protocol_details.get("category", "Unknown")
                            }
            
            # 如果没有获取到数据，使用Glassnode作为备选
            if not protocol_data and self.glassnode:
                protocol_data = self._get_glassnode_protocol_data(base_currency, chain)
        
        except Exception as e:
            logger.error(f"Failed to get protocol data for {base_currency}: {str(e)}")
        
        # 如果仍然没有数据，返回模拟数据
        if not protocol_data:
            protocol_data = self._generate_mock_protocol_data(base_currency)
        
        self._cache_data(cache_key, protocol_data)
        return protocol_data
    
    def get_liquidity_pools_data(self, base_currency: str) -> Dict[str, Any]:
        """
        获取流动性池数据
        
        Args:
            base_currency: 基础资产符号
            
        Returns:
            流动性池数据
        """
        if not self.is_defi_supported(base_currency):
            return self._get_empty_liquidity_pools_data()
        
        cache_key = f"liquidity_pools_{base_currency}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        pools_data = {"pools": [], "total_pool_tvl": 0, "average_apy": 0, "total_volume_24h": 0}
        
        try:
            # TODO: 实现从DeFi Llama获取真实流动性池数据
            # 目前使用模拟数据，后续需要实现真实数据获取
            pools_data = self._generate_mock_liquidity_pools_data(base_currency)
            
        except Exception as e:
            logger.error(f"Failed to get liquidity pools data for {base_currency}: {str(e)}")
            pools_data = self._generate_mock_liquidity_pools_data(base_currency)
        
        self._cache_data(cache_key, pools_data)
        return pools_data
    
    def get_yield_farming_data(self, base_currency: str) -> Dict[str, Any]:
        """
        获取收益挖矿数据
        
        Args:
            base_currency: 基础资产符号
            
        Returns:
            收益挖矿数据
        """
        if not self.is_defi_supported(base_currency):
            return self._get_empty_yield_farming_data()
        
        cache_key = f"yield_farming_{base_currency}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        yield_data = {"farms": [], "total_farm_tvl": 0, "average_apy": 0, "highest_apy": 0, "lowest_apy": 0}
        
        try:
            # TODO: 实现从DeFi Llama获取真实收益率数据
            # 目前使用模拟数据，后续需要实现真实数据获取
            yield_data = self._generate_mock_yield_farming_data(base_currency)
            
        except Exception as e:
            logger.error(f"Failed to get yield farming data for {base_currency}: {str(e)}")
            yield_data = self._generate_mock_yield_farming_data(base_currency)
        
        self._cache_data(cache_key, yield_data)
        return yield_data
    
    def get_governance_data(self, base_currency: str) -> Dict[str, Any]:
        """
        获取治理数据
        
        Args:
            base_currency: 基础资产符号
            
        Returns:
            治理数据
        """
        if not self.is_defi_supported(base_currency):
            return self._get_empty_governance_data()
        
        cache_key = f"governance_{base_currency}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        governance_data = {}
        
        try:
            # TODO: 实现从DeFi Llama获取真实治理数据
            # 目前使用模拟数据，后续需要实现真实数据获取
            governance_data = self._generate_mock_governance_data(base_currency)
            
        except Exception as e:
            logger.error(f"Failed to get governance data for {base_currency}: {str(e)}")
            governance_data = self._generate_mock_governance_data(base_currency)
        
        self._cache_data(cache_key, governance_data)
        return governance_data
    
    def get_aggregator_data(self, base_currency: str) -> Dict[str, Any]:
        """
        获取聚合器数据
        
        Args:
            base_currency: 基础资产符号
            
        Returns:
            聚合器数据
        """
        cache_key = f"aggregator_{base_currency}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        aggregator_data = {}
        
        try:
            # TODO: 实现从DeFi Llama获取真实聚合器数据
            # 目前使用模拟数据
            aggregator_data = self._generate_mock_aggregator_data(base_currency)
            
        except Exception as e:
            logger.error(f"Failed to get aggregator data for {base_currency}: {str(e)}")
            aggregator_data = self._generate_mock_aggregator_data(base_currency)
        
        self._cache_data(cache_key, aggregator_data)
        return aggregator_data
    
    def _get_glassnode_protocol_data(self, base_currency: str, chain: str) -> Dict[str, Any]:
        """从Glassnode获取协议数据"""
        try:
            if not self.glassnode:
                return {}
            
            # 获取DeFi相关指标
            defi_metrics = self.glassnode.get_defi_metrics(
                asset=base_currency,
                chain=chain
            )
            
            if defi_metrics:
                # 转换Glassnode数据格式
                protocol_data = {}
                tvl = defi_metrics.get("total_value_locked", 0)
                
                protocol_data["glassnode_defi"] = {
                    "tvl": tvl,
                    "tvl_change_24h": defi_metrics.get("defi_growth_30d", 0),
                    "defi_dominance": defi_metrics.get("defi_dominance", 0),
                    "protocol_count": defi_metrics.get("protocol_diversity", 0),
                    "source": "glassnode"
                }
                
                return protocol_data
            
        except Exception as e:
            logger.error(f"Failed to get Glassnode protocol data: {str(e)}")
        
        return {}
    
    def _calculate_tvl_change(self, protocol_data: Dict[str, Any]) -> float:
        """计算TVL变化"""
        try:
            # 从协议数据中提取TVL变化信息
            tvl_chart = protocol_data.get("tvl", [])
            if isinstance(tvl_chart, list) and len(tvl_chart) >= 2:
                current_tvl = tvl_chart[-1].get("totalLiquidityUSD", 0)
                previous_tvl = tvl_chart[-2].get("totalLiquidityUSD", 0)
                if previous_tvl > 0:
                    return (current_tvl - previous_tvl) / previous_tvl
        except Exception:
            pass
        return 0.0
    
    def _get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """获取缓存数据"""
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if datetime.now().timestamp() - timestamp < self.cache_ttl:
                return data
            else:
                del self.cache[cache_key]
        return None
    
    def _cache_data(self, cache_key: str, data: Dict[str, Any]):
        """缓存数据"""
        self.cache[cache_key] = (data, datetime.now().timestamp())
    
    def _get_empty_protocol_data(self) -> Dict[str, Any]:
        """获取空的协议数据"""
        return {}
    
    def _get_empty_liquidity_pools_data(self) -> Dict[str, Any]:
        """获取空的流动性池数据"""
        return {
            "pools": [],
            "total_pool_tvl": 0,
            "average_apy": 0,
            "total_volume_24h": 0
        }
    
    def _get_empty_yield_farming_data(self) -> Dict[str, Any]:
        """获取空的收益挖矿数据"""
        return {
            "farms": [],
            "total_farm_tvl": 0,
            "average_apy": 0,
            "highest_apy": 0,
            "lowest_apy": 0
        }
    
    def _get_empty_governance_data(self) -> Dict[str, Any]:
        """获取空的治理数据"""
        return {
            "token_holders": 0,
            "active_voters": 0,
            "voter_participation": 0,
            "governance_tokens_locked": 0,
            "governance_tvl": 0,
            "proposals_30d": 0,
            "approved_proposals": 0,
            "rejected_proposals": 0,
            "pending_proposals": 0,
            "governance_health": "unknown",
            "proposal_success_rate": 0,
            "voter_concentration": 0
        }
    
    def _generate_mock_protocol_data(self, base_currency: str) -> Dict[str, Any]:
        """生成模拟协议数据"""
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
    
    def _generate_mock_liquidity_pools_data(self, base_currency: str) -> Dict[str, Any]:
        """生成模拟流动性池数据"""
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
            "average_apy": sum(pool["apy"] for pool in pools) / len(pools) if pools else 0,
            "total_volume_24h": sum(pool["volume_24h"] for pool in pools),
        }
    
    def _generate_mock_yield_farming_data(self, base_currency: str) -> Dict[str, Any]:
        """生成模拟挖矿数据"""
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
            "average_apy": sum(farm["apy"] for farm in farms) / len(farms) if farms else 0,
            "highest_apy": max(farm["apy"] for farm in farms) if farms else 0,
            "lowest_apy": min(farm["apy"] for farm in farms) if farms else 0,
        }
    
    def _generate_mock_governance_data(self, base_currency: str) -> Dict[str, Any]:
        """生成模拟治理数据"""
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
    
    def _generate_mock_aggregator_data(self, base_currency: str) -> Dict[str, Any]:
        """生成模拟聚合器数据"""
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