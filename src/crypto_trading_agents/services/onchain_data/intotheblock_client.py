"""
IntoTheBlock API客户端 - 提供链上数据分析
"""

import os
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class IntoTheBlockClient:
    """IntoTheBlock API客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化IntoTheBlock客户端
        
        Args:
            api_key: IntoTheBlock API密钥，如果为None则从环境变量获取
        """
        self.api_key = api_key or os.getenv("INTOTHEBLOCK_API_KEY")
        self.base_url = "https://api.intotheblock.com/v1"
        self.headers = {
            "Accept": "application/json",
            "x-api-key": self.api_key
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        if not self.api_key:
            logger.warning("IntoTheBlock API key not provided, some endpoints may not work")
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        发送API请求
        
        Args:
            endpoint: API端点
            params: 请求参数
            
        Returns:
            API响应数据
        """
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"IntoTheBlock API request failed: {str(e)}")
            raise
        except ValueError as e:
            logger.error(f"Failed to parse IntoTheBlock API response: {str(e)}")
            raise
    
    def get_whale_activity(self, asset: str, days: int = 30) -> Dict[str, Any]:
        """
        获取巨鲸活动数据
        
        Args:
            asset: 资产符号 (e.g., "BTC", "ETH")
            days: 天数范围
            
        Returns:
            巨鲸活动数据
        """
        params = {
            "coin": asset.lower(),
            "days": days
        }
            
        return self._make_request("whales", params)
    
    def get_holder_distribution(self, asset: str) -> Dict[str, Any]:
        """
        获取持有者分布数据
        
        Args:
            asset: 资产符号
            
        Returns:
            持有者分布数据
        """
        params = {
            "coin": asset.lower()
        }
            
        return self._make_request("holder-distribution", params)
    
    def get_exchange_balance_changes(self, asset: str, days: int = 30) -> Dict[str, Any]:
        """
        获取交易所余额变化数据
        
        Args:
            asset: 资产符号
            days: 天数范围
            
        Returns:
            交易所余额变化数据
        """
        params = {
            "coin": asset.lower(),
            "days": days
        }
            
        return self._make_request("exchange-balance", params)
    
    def get_onchain_sentiment(self, asset: str, days: int = 30) -> Dict[str, Any]:
        """
        获取链上情绪数据
        
        Args:
            asset: 资产符号
            days: 天数范围
            
        Returns:
            链上情绪数据
        """
        params = {
            "coin": asset.lower(),
            "days": days
        }
            
        return self._make_request("onchain-sentiment", params)
    
    def get_network_activity(self, asset: str, days: int = 30) -> Dict[str, Any]:
        """
        获取网络活动数据
        
        Args:
            asset: 资产符号
            days: 天数范围
            
        Returns:
            网络活动数据
        """
        params = {
            "coin": asset.lower(),
            "days": days
        }
            
        return self._make_request("network-activity", params)