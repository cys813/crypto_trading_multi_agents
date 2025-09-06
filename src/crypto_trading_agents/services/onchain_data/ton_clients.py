"""
TON API客户端 - 专门为The Open Network设计
"""

import os
import requests
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class TONCenterClient:
    """TONCenter API客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化TONCenter客户端
        
        Args:
            api_key: TONCenter API密钥，如果为None则使用公开接口
        """
        self.api_key = api_key
        self.base_url = "https://toncenter.com/api/v3"
        self.headers = {
            "Accept": "application/json",
        }
        if self.api_key:
            self.headers["X-API-Key"] = self.api_key
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        if not self.api_key:
            logger.info("Using TONCenter public API (rate limited)")
        else:
            logger.info("TONCenter client initialized with API key")
    
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
            logger.error(f"TONCenter API request failed: {str(e)}")
            raise
        except ValueError as e:
            logger.error(f"Failed to parse TONCenter API response: {str(e)}")
            raise
    
    def get_account_info(self, address: str) -> Dict[str, Any]:
        """
        获取账户信息
        
        Args:
            address: TON地址
            
        Returns:
            账户信息
        """
        params = {
            "address": address
        }
        return self._make_request("account", params)
    
    def get_transaction_count(self, address: str, limit: int = 100) -> Dict[str, Any]:
        """
        获取交易数量
        
        Args:
            address: TON地址
            limit: 返回数量限制
            
        Returns:
            交易数量信息
        """
        params = {
            "address": address,
            "limit": limit
        }
        return self._make_request("transactions", params)
    
    def get_block_info(self, workchain: int = None, shard: int = None, seqno: int = None) -> Dict[str, Any]:
        """
        获取区块信息
        
        Args:
            workchain: 工作链ID
            shard: 分片ID
            seqno: 序列号
            
        Returns:
            区块信息
        """
        params = {}
        if workchain is not None:
            params["workchain"] = workchain
        if shard is not None:
            params["shard"] = shard
        if seqno is not None:
            params["seqno"] = seqno
            
        return self._make_request("block", params)
    
    def get_masterchain_info(self) -> Dict[str, Any]:
        """
        获取主链信息
        
        Returns:
            主链信息
        """
        return self._make_request("masterchainInfo")
    
    def get_validator_stats(self) -> Dict[str, Any]:
        """
        获取验证者统计信息
        
        Returns:
            验证者统计
        """
        return self._make_request("validatorStats")


class TONAnalyticsClient:
    """TON Analytics API客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化TON Analytics客户端
        
        Args:
            api_key: TON Analytics API密钥
        """
        self.api_key = api_key
        self.base_url = "https://api.tonanalytics.com/v1"
        self.headers = {
            "Accept": "application/json",
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        if not self.api_key:
            logger.warning("TON Analytics API key not provided, some endpoints may not work")
    
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
            logger.error(f"TON Analytics API request failed: {str(e)}")
            raise
        except ValueError as e:
            logger.error(f"Failed to parse TON Analytics API response: {str(e)}")
            raise
    
    def get_network_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        获取网络指标数据
        
        Args:
            days: 天数范围
            
        Returns:
            网络指标数据
        """
        params = {
            "days": days
        }
        return self._make_request("network/metrics", params)
    
    def get_jetton_holders(self, jetton_address: str) -> Dict[str, Any]:
        """
        获取Jetton持有者分布
        
        Args:
            jetton_address: Jetton合约地址
            
        Returns:
            持有者分布数据
        """
        params = {
            "jetton_address": jetton_address
        }
        return self._make_request("jetton/holders", params)
    
    def get_whale_activity(self, days: int = 30) -> Dict[str, Any]:
        """
        获取巨鲸活动数据
        
        Args:
            days: 天数范围
            
        Returns:
            巨鲸活动数据
        """
        params = {
            "days": days
        }
        return self._make_request("whales/activity", params)
    
    def get_defi_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        获取DeFi指标数据
        
        Args:
            days: 天数范围
            
        Returns:
            DeFi指标数据
        """
        params = {
            "days": days
        }
        return self._make_request("defi/metrics", params)