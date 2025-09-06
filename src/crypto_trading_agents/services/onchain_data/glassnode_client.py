"""
Glassnode API客户端 - 提供链上数据分析
"""

import os
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class GlassnodeClient:
    """Glassnode API客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化Glassnode客户端
        
        Args:
            api_key: Glassnode API密钥，如果为None则从环境变量获取
        """
        self.api_key = api_key or os.getenv("GLASSNODE_API_KEY")
        self.base_url = "https://api.glassnode.com/v1/metrics"
        self.headers = {
            "Accept": "application/json",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        if not self.api_key:
            logger.warning("Glassnode API key not provided, some endpoints may not work")
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送API请求
        
        Args:
            endpoint: API端点
            params: 请求参数
            
        Returns:
            API响应数据
        """
        url = f"{self.base_url}/{endpoint}"
        params["api_key"] = self.api_key
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Glassnode API request failed: {str(e)}")
            raise
        except ValueError as e:
            logger.error(f"Failed to parse Glassnode API response: {str(e)}")
            raise
    
    def get_active_addresses(self, asset: str, chain: str = "ethereum", 
                           since: Optional[str] = None, until: Optional[str] = None) -> Dict[str, Any]:
        """
        获取活跃地址数据
        
        Args:
            asset: 资产符号 (e.g., "BTC", "ETH")
            chain: 区块链 (e.g., "ethereum", "bitcoin")
            since: 开始时间 (ISO格式)
            until: 结束时间 (ISO格式)
            
        Returns:
            活跃地址数据
        """
        params = {
            "a": asset,
            "c": chain,
        }
        
        if since:
            params["s"] = since
        if until:
            params["u"] = until
            
        return self._make_request("addresses/active_count", params)
    
    def get_transaction_metrics(self, asset: str, chain: str = "ethereum",
                              since: Optional[str] = None, until: Optional[str] = None) -> Dict[str, Any]:
        """
        获取交易指标数据
        
        Args:
            asset: 资产符号
            chain: 区块链
            since: 开始时间
            until: 结束时间
            
        Returns:
            交易指标数据
        """
        params = {
            "a": asset,
            "c": chain,
        }
        
        if since:
            params["s"] = since
        if until:
            params["u"] = until
            
        return self._make_request("transactions/count", params)
    
    def get_exchange_flows(self, asset: str, chain: str = "ethereum",
                          since: Optional[str] = None, until: Optional[str] = None) -> Dict[str, Any]:
        """
        获取交易所流量数据
        
        Args:
            asset: 资产符号
            chain: 区块链
            since: 开始时间
            until: 结束时间
            
        Returns:
            交易所流量数据
        """
        params = {
            "a": asset,
            "c": chain,
        }
        
        if since:
            params["s"] = since
        if until:
            params["u"] = until
            
        return self._make_request("exchanges/netflow", params)
    
    def get_miner_data(self, asset: str, chain: str = "ethereum",
                      since: Optional[str] = None, until: Optional[str] = None) -> Dict[str, Any]:
        """
        获取矿工数据
        
        Args:
            asset: 资产符号
            chain: 区块链
            since: 开始时间
            until: 结束时间
            
        Returns:
            矿工数据
        """
        params = {
            "a": asset,
            "c": chain,
        }
        
        if since:
            params["s"] = since
        if until:
            params["u"] = until
            
        return self._make_request("miners/revenue", params)
    
    def get_defi_metrics(self, asset: str, chain: str = "ethereum",
                        since: Optional[str] = None, until: Optional[str] = None) -> Dict[str, Any]:
        """
        获取DeFi指标数据
        
        Args:
            asset: 资产符号
            chain: 区块链
            since: 开始时间
            until: 结束时间
            
        Returns:
            DeFi指标数据
        """
        params = {
            "a": asset,
            "c": chain,
        }
        
        if since:
            params["s"] = since
        if until:
            params["u"] = until
            
        return self._make_request("defi/total_value_locked", params)