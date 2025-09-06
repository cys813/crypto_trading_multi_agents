"""
链上数据服务统一接口 - 整合多个链上数据源
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from .glassnode_client import GlassnodeClient
from .intotheblock_client import IntoTheBlockClient
from .ton_data_service import TonDataService
from .solana_data_service import SolanaDataService

logger = logging.getLogger(__name__)

class OnchainDataService:
    """链上数据服务统一接口"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化链上数据服务
        
        Args:
            config: 配置字典，包含API密钥等信息
        """
        self.config = config
        
        # 初始化API客户端
        self._init_clients()
    
    def _init_clients(self):
        """初始化API客户端"""
        # 从配置中获取API密钥
        apis_config = self.config.get("apis", {}).get("data", {})
        
        # 初始化Glassnode客户端
        glassnode_config = apis_config.get("onchain_data", {}).get("glassnode", {})
        if glassnode_config.get("enabled", False):
            glassnode_api_key = glassnode_config.get("api_key")
            if glassnode_api_key and not glassnode_api_key.startswith("${"):
                self.glassnode_client = GlassnodeClient(glassnode_api_key)
                logger.info("Glassnode client initialized")
            else:
                logger.warning("Glassnode API key not configured properly")
                self.glassnode_client = None
        else:
            self.glassnode_client = None
        
        # 初始化IntoTheBlock客户端
        intotheblock_config = apis_config.get("onchain_data", {}).get("intotheblock", {})
        if intotheblock_config.get("enabled", False):
            intotheblock_api_key = intotheblock_config.get("api_key")
            if intotheblock_api_key and not intotheblock_api_key.startswith("${"):
                self.intotheblock_client = IntoTheBlockClient(intotheblock_api_key)
                logger.info("IntoTheBlock client initialized")
            else:
                logger.warning("IntoTheBlock API key not configured properly")
                self.intotheblock_client = None
        else:
            self.intotheblock_client = None
        
        # 初始化TON数据服务
        ton_config = apis_config.get("onchain_data", {}).get("ton", {})
        if ton_config.get("enabled", False):
            self.ton_service = TonDataService(self.config)
            logger.info("TON data service initialized")
        else:
            self.ton_service = None
        
        # 初始化Solana数据服务
        solana_config = apis_config.get("onchain_data", {}).get("solana", {})
        if solana_config.get("enabled", False):
            self.solana_service = SolanaDataService(self.config)
            logger.info("Solana data service initialized")
        else:
            self.solana_service = None
    
    def get_active_addresses(self, currency: str, chain: str, 
                           end_date: str, days: int = 30) -> Dict[str, Any]:
        """
        获取活跃地址数据
        
        Args:
            currency: 货币符号
            chain: 区块链
            end_date: 结束日期
            days: 天数范围
            
        Returns:
            活跃地址数据
        """
        data = {}
        
        # 特殊处理TON链
        if currency.upper() == "TON" or chain.lower() == "ton":
            if self.ton_service:
                try:
                    ton_data = self.ton_service.get_active_addresses(currency, days)
                    data.update({
                        "ton_data": ton_data,
                        "source": "ton_service"
                    })
                except Exception as e:
                    logger.error(f"Failed to get active addresses from TON service: {str(e)}")
            
            if not data:
                data = self._get_mock_active_addresses(currency, chain, end_date, days)
            return data
        
        # 特殊处理Solana链
        if currency.upper() == "SOL" or chain.lower() == "solana":
            if self.solana_service:
                try:
                    solana_data = self.solana_service.get_active_accounts(currency, days)
                    data.update({
                        "solana_data": solana_data,
                        "source": "solana_service"
                    })
                except Exception as e:
                    logger.error(f"Failed to get active addresses from Solana service: {str(e)}")
            
            if not data:
                data = self._get_mock_active_addresses(currency, chain, end_date, days)
            return data
        
        # 尝试从Glassnode获取数据
        if self.glassnode_client:
            try:
                glassnode_data = self.glassnode_client.get_active_addresses(
                    asset=currency, 
                    chain=chain,
                    until=end_date
                )
                data.update({
                    "glassnode_data": glassnode_data,
                    "source": "glassnode"
                })
            except Exception as e:
                logger.error(f"Failed to get active addresses from Glassnode: {str(e)}")
        
        # 如果没有Glassnode数据，返回模拟数据
        if not data:
            data = self._get_mock_active_addresses(currency, chain, end_date, days)
        
        return data
    
    def get_transaction_metrics(self, currency: str, chain: str, 
                              end_date: str, days: int = 30) -> Dict[str, Any]:
        """
        获取交易指标数据
        
        Args:
            currency: 货币符号
            chain: 区块链
            end_date: 结束日期
            days: 天数范围
            
        Returns:
            交易指标数据
        """
        data = {}
        
        # 特殊处理TON链
        if currency.upper() == "TON" or chain.lower() == "ton":
            if self.ton_service:
                try:
                    ton_data = self.ton_service.get_transaction_metrics(currency, days)
                    data.update({
                        "ton_data": ton_data,
                        "source": "ton_service"
                    })
                except Exception as e:
                    logger.error(f"Failed to get transaction metrics from TON service: {str(e)}")
            
            if not data:
                data = self._get_mock_transaction_metrics(currency, chain, end_date, days)
            return data
        
        # 特殊处理Solana链
        if currency.upper() == "SOL" or chain.lower() == "solana":
            if self.solana_service:
                try:
                    solana_data = self.solana_service.get_transaction_metrics(currency, days)
                    data.update({
                        "solana_data": solana_data,
                        "source": "solana_service"
                    })
                except Exception as e:
                    logger.error(f"Failed to get transaction metrics from Solana service: {str(e)}")
            
            if not data:
                data = self._get_mock_transaction_metrics(currency, chain, end_date, days)
            return data
        
        # 尝试从Glassnode获取数据
        if self.glassnode_client:
            try:
                glassnode_data = self.glassnode_client.get_transaction_metrics(
                    asset=currency, 
                    chain=chain,
                    until=end_date
                )
                data.update({
                    "glassnode_data": glassnode_data,
                    "source": "glassnode"
                })
            except Exception as e:
                logger.error(f"Failed to get transaction metrics from Glassnode: {str(e)}")
        
        # 如果没有Glassnode数据，返回模拟数据
        if not data:
            data = self._get_mock_transaction_metrics(currency, chain, end_date, days)
        
        return data
    
    def get_exchange_flows(self, currency: str, chain: str, 
                         end_date: str, days: int = 30) -> Dict[str, Any]:
        """
        获取交易所流量数据
        
        Args:
            currency: 货币符号
            chain: 区块链
            end_date: 结束日期
            days: 天数范围
            
        Returns:
            交易所流量数据
        """
        data = {}
        
        # 尝试从Glassnode获取数据
        if self.glassnode_client:
            try:
                glassnode_data = self.glassnode_client.get_exchange_flows(
                    asset=currency, 
                    chain=chain,
                    until=end_date
                )
                data.update({
                    "glassnode_data": glassnode_data,
                    "source": "glassnode"
                })
            except Exception as e:
                logger.error(f"Failed to get exchange flows from Glassnode: {str(e)}")
        
        # 尝试从IntoTheBlock获取数据
        if not data and self.intotheblock_client:
            try:
                intotheblock_data = self.intotheblock_client.get_exchange_balance_changes(
                    asset=currency, 
                    days=days
                )
                data.update({
                    "intotheblock_data": intotheblock_data,
                    "source": "intotheblock"
                })
            except Exception as e:
                logger.error(f"Failed to get exchange flows from IntoTheBlock: {str(e)}")
        
        # 如果没有数据，返回模拟数据
        if not data:
            data = self._get_mock_exchange_flows(currency, chain, end_date, days)
        
        return data
    
    def get_whale_activity(self, currency: str, chain: str, 
                          end_date: str, days: int = 30) -> Dict[str, Any]:
        """
        获取巨鲸活动数据
        
        Args:
            currency: 货币符号
            chain: 区块链
            end_date: 结束日期
            days: 天数范围
            
        Returns:
            巨鲸活动数据
        """
        data = {}
        
        # 尝试从IntoTheBlock获取数据
        if self.intotheblock_client:
            try:
                intotheblock_data = self.intotheblock_client.get_whale_activity(
                    asset=currency, 
                    days=days
                )
                data.update({
                    "intotheblock_data": intotheblock_data,
                    "source": "intotheblock"
                })
            except Exception as e:
                logger.error(f"Failed to get whale activity from IntoTheBlock: {str(e)}")
        
        # 如果没有数据，返回模拟数据
        if not data:
            data = self._get_mock_whale_activity(currency, chain, end_date, days)
        
        return data
    
    def get_holder_distribution(self, currency: str, chain: str, 
                              end_date: str, days: int = 30) -> Dict[str, Any]:
        """
        获取持有者分布数据
        
        Args:
            currency: 货币符号
            chain: 区块链
            end_date: 结束日期
            days: 天数范围
            
        Returns:
            持有者分布数据
        """
        data = {}
        
        # 尝试从IntoTheBlock获取数据
        if self.intotheblock_client:
            try:
                intotheblock_data = self.intotheblock_client.get_holder_distribution(
                    asset=currency
                )
                data.update({
                    "intotheblock_data": intotheblock_data,
                    "source": "intotheblock"
                })
            except Exception as e:
                logger.error(f"Failed to get holder distribution from IntoTheBlock: {str(e)}")
        
        # 如果没有数据，返回模拟数据
        if not data:
            data = self._get_mock_holder_distribution(currency, chain, end_date, days)
        
        return data
    
    def get_network_health(self, currency: str, chain: str, 
                          end_date: str, days: int = 30) -> Dict[str, Any]:
        """
        获取网络健康度数据
        
        Args:
            currency: 货币符号
            chain: 区块链
            end_date: 结束日期
            days: 天数范围
            
        Returns:
            网络健康度数据
        """
        data = {}
        
        # 特殊处理TON链
        if currency.upper() == "TON" or chain.lower() == "ton":
            if self.ton_service:
                try:
                    ton_data = self.ton_service.get_network_health(currency, days)
                    data.update({
                        "ton_data": ton_data,
                        "source": "ton_service"
                    })
                except Exception as e:
                    logger.error(f"Failed to get network health from TON service: {str(e)}")
            
            if not data:
                data = self._get_mock_network_health(currency, chain, end_date, days)
            return data
        
        # 特殊处理Solana链
        if currency.upper() == "SOL" or chain.lower() == "solana":
            if self.solana_service:
                try:
                    solana_data = self.solana_service.get_network_health(currency, days)
                    data.update({
                        "solana_data": solana_data,
                        "source": "solana_service"
                    })
                except Exception as e:
                    logger.error(f"Failed to get network health from Solana service: {str(e)}")
            
            if not data:
                data = self._get_mock_network_health(currency, chain, end_date, days)
            return data
        
        # 尝试从Glassnode获取数据
        if self.glassnode_client:
            try:
                miner_data = self.glassnode_client.get_miner_data(
                    asset=currency, 
                    chain=chain,
                    until=end_date
                )
                data.update({
                    "miner_data": miner_data,
                    "source": "glassnode"
                })
            except Exception as e:
                logger.error(f"Failed to get network health from Glassnode: {str(e)}")
        
        # 尝试从IntoTheBlock获取数据
        if not data and self.intotheblock_client:
            try:
                network_data = self.intotheblock_client.get_network_activity(
                    asset=currency, 
                    days=days
                )
                data.update({
                    "network_data": network_data,
                    "source": "intotheblock"
                })
            except Exception as e:
                logger.error(f"Failed to get network health from IntoTheBlock: {str(e)}")
        
        # 如果没有数据，返回模拟数据
        if not data:
            data = self._get_mock_network_health(currency, chain, end_date, days)
        
        return data
    
    def get_defi_metrics(self, currency: str, chain: str, 
                        end_date: str, days: int = 30) -> Dict[str, Any]:
        """
        获取DeFi指标数据
        
        Args:
            currency: 货币符号
            chain: 区块链
            end_date: 结束日期
            days: 天数范围
            
        Returns:
            DeFi指标数据
        """
        data = {}
        
        # 尝试从Glassnode获取数据
        if self.glassnode_client:
            try:
                defi_data = self.glassnode_client.get_defi_metrics(
                    asset=currency, 
                    chain=chain,
                    until=end_date
                )
                data.update({
                    "defi_data": defi_data,
                    "source": "glassnode"
                })
            except Exception as e:
                logger.error(f"Failed to get DeFi metrics from Glassnode: {str(e)}")
        
        # 如果没有数据，返回模拟数据
        if not data:
            data = self._get_mock_defi_metrics(currency, chain, end_date, days)
        
        return data
    
    def _get_mock_active_addresses(self, currency: str, chain: str, 
                                  end_date: str, days: int) -> Dict[str, Any]:
        """获取模拟活跃地址数据"""
        return {
            "daily_active": 850000,
            "weekly_active": 3200000,
            "monthly_active": 8500000,
            "growth_rate_7d": 0.05,
            "growth_rate_30d": 0.12,
            "historical_avg": 750000,
            "percentile": 75,
            "source": "mock"
        }
    
    def _get_mock_transaction_metrics(self, currency: str, chain: str, 
                                     end_date: str, days: int) -> Dict[str, Any]:
        """获取模拟交易指标数据"""
        return {
            "daily_transactions": 1250000,
            "average_fee": 15.5,
            "total_fees": 19375000,
            "large_transactions": 1250,
            "transaction_growth": 0.08,
            "fee_trend": "increasing",
            "source": "mock"
        }
    
    def _get_mock_exchange_flows(self, currency: str, chain: str, 
                                end_date: str, days: int) -> Dict[str, Any]:
        """获取模拟交易所流量数据"""
        return {
            "exchange_inflows": 15000,
            "exchange_outflows": 12000,
            "net_flow": -3000,  # 净流出
            "inflow_trend": "decreasing",
            "outflow_trend": "increasing",
            "exchange_balance": 2500000,
            "balance_change_24h": -0.12,
            "source": "mock"
        }
    
    def _get_mock_whale_activity(self, currency: str, chain: str, 
                                end_date: str, days: int) -> Dict[str, Any]:
        """获取模拟巨鲸活动数据"""
        return {
            "whale_concentration": 0.45,
            "accumulation_pattern": True,
            "large_transfers": 150,
            "whale_net_flow": -5000,
            "significant_holders": 1250,
            "whale_growth_30d": 0.08,
            "source": "mock"
        }
    
    def _get_mock_holder_distribution(self, currency: str, chain: str, 
                                    end_date: str, days: int) -> Dict[str, Any]:
        """获取模拟持有者分布数据"""
        return {
            "total_holders": 1500000,
            "holder_growth": 0.08,
            "average_balance": 0.85,
            "gini_coefficient": 0.72,
            "top_10_holdings": 0.35,
            "holder_concentration": "high",
            "source": "mock"
        }
    
    def _get_mock_network_health(self, currency: str, chain: str, 
                                end_date: str, days: int) -> Dict[str, Any]:
        """获取模拟网络健康度数据"""
        return {
            "hash_rate": 185000000000,
            "active_nodes": 12500,
            "block_time": 12.5,
            "difficulty": 28500000000000,
            "network_load": "high",
            "mining_profitability": "profitable",
            "source": "mock"
        }
    
    def _get_mock_defi_metrics(self, currency: str, chain: str, 
                              end_date: str, days: int) -> Dict[str, Any]:
        """获取模拟DeFi指标数据"""
        return {
            "total_value_locked": 85000000000,
            "defi_dominance": 0.15,
            "protocol_diversity": 125,
            "yield_farming_activity": "high",
            "defi_growth_30d": 0.12,
            "tvl_trend": "increasing",
            "source": "mock"
        }