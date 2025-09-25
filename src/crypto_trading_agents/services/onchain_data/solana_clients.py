"""
Solana API客户端 - 专门为Solana区块链设计
"""

import os
import requests
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class SolanaRPCClient:
    """Solana RPC客户端"""
    
    def __init__(self, rpc_url: Optional[str] = None):
        """
        初始化Solana RPC客户端
        
        Args:
            rpc_url: Solana RPC节点URL，如果为None则使用默认公共节点
        """
        self.rpc_url = rpc_url or "https://api.mainnet-beta.solana.com"
        self.headers = {
            "Content-Type": "application/json",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        logger.info(f"Solana RPC client initialized with URL: {self.rpc_url}")
    
    def _make_request(self, method: str, params: List[Any] = None) -> Dict[str, Any]:
        """
        发送RPC请求
        
        Args:
            method: RPC方法名
            params: 请求参数
            
        Returns:
            RPC响应数据
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or []
        }
        
        try:
            response = self.session.post(self.rpc_url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Solana RPC request failed: {str(e)}")
            raise
        except ValueError as e:
            logger.error(f"Failed to parse Solana RPC response: {str(e)}")
            raise
    
    def get_slot(self) -> int:
        """
        获取当前slot
        
        Returns:
            当前slot编号
        """
        response = self._make_request("getSlot")
        return response.get("result", 0)
    
    def get_block_height(self) -> int:
        """
        获取当前区块高度
        
        Returns:
            当前区块高度
        """
        response = self._make_request("getBlockHeight")
        return response.get("result", 0)
    
    def get_epoch_info(self) -> Dict[str, Any]:
        """
        获取当前epoch信息
        
        Returns:
            epoch信息
        """
        response = self._make_request("getEpochInfo")
        return response.get("result", {})
    
    def get_account_info(self, pubkey: str) -> Dict[str, Any]:
        """
        获取账户信息
        
        Args:
            pubkey: 账户公钥
            
        Returns:
            账户信息
        """
        response = self._make_request("getAccountInfo", [pubkey])
        return response.get("result", {})
    
    def get_transaction_count(self) -> int:
        """
        获取交易总数
        
        Returns:
            交易总数
        """
        response = self._make_request("getTransactionCount")
        return response.get("result", 0)
    
    def get_recent_performance_samples(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取最近的性能样本
        
        Args:
            limit: 返回样本数量限制
            
        Returns:
            性能样本列表
        """
        response = self._make_request("getRecentPerformanceSamples", [limit])
        return response.get("result", [])


class SolscanClient:
    """Solscan API客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化Solscan客户端
        
        Args:
            api_key: Solscan API密钥
        """
        self.api_key = api_key
        self.base_url = "https://public-api.solscan.io"
        self.headers = {
            "Accept": "application/json",
        }
        if self.api_key:
            self.headers["X-API-Key"] = self.api_key
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        if not self.api_key:
            logger.info("Using Solscan public API (rate limited)")
        else:
            logger.info("Solscan client initialized with API key")
    
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
            logger.error(f"Solscan API request failed: {str(e)}")
            raise
        except ValueError as e:
            logger.error(f"Failed to parse Solscan API response: {str(e)}")
            raise
    
    def get_account_token_balances(self, account: str) -> Dict[str, Any]:
        """
        获取账户代币余额
        
        Args:
            account: 账户地址
            
        Returns:
            代币余额信息
        """
        return self._make_request(f"account/tokens", {"account": account})
    
    def get_token_holders(self, token_address: str, offset: int = 0, limit: int = 10) -> Dict[str, Any]:
        """
        获取代币持有者
        
        Args:
            token_address: 代币地址
            offset: 偏移量
            limit: 返回数量限制
            
        Returns:
            持有者信息
        """
        params = {
            "offset": offset,
            "limit": limit
        }
        return self._make_request(f"token/holders", {**params, "tokenAddress": token_address})
    
    def get_token_meta(self, token_address: str) -> Dict[str, Any]:
        """
        获取代币元数据
        
        Args:
            token_address: 代币地址
            
        Returns:
            代币元数据
        """
        return self._make_request(f"token/meta", {"tokenAddress": token_address})
    
    def get_market_data(self, token_address: str) -> Dict[str, Any]:
        """
        获取代币市场数据
        
        Args:
            token_address: 代币地址
            
        Returns:
            市场数据
        """
        return self._make_request(f"token/market", {"tokenAddress": token_address})


class HeliusClient:
    """Helius API客户端"""
    
    def __init__(self, api_key: str):
        """
        初始化Helius客户端
        
        Args:
            api_key: Helius API密钥
        """
        self.api_key = api_key
        self.base_url = f"https://rpc.helius.xyz/?api-key={api_key}"
        self.headers = {
            "Content-Type": "application/json",
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        logger.info("Helius client initialized")
    
    def _make_request(self, method: str, params: List[Any] = None) -> Dict[str, Any]:
        """
        发送RPC增强请求
        
        Args:
            method: RPC方法名
            params: 请求参数
            
        Returns:
            RPC响应数据
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or []
        }
        
        try:
            response = self.session.post(self.base_url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Helius RPC request failed: {str(e)}")
            raise
        except ValueError as e:
            logger.error(f"Failed to parse Helius RPC response: {str(e)}")
            raise
    
    def get_enhanced_transactions(self, addresses: List[str], 
                                transaction_types: List[str] = None) -> Dict[str, Any]:
        """
        获取增强的交易数据
        
        Args:
            addresses: 地址列表
            transaction_types: 交易类型过滤
            
        Returns:
            增强交易数据
        """
        params = [{
            "addresses": addresses
        }]
        if transaction_types:
            params[0]["transactionTypes"] = transaction_types
            
        return self._make_request("getTransactions", params)
    
    def get_parsed_token_accounts(self, owner: str) -> Dict[str, Any]:
        """
        获取解析后的代币账户
        
        Args:
            owner: 所有者地址
            
        Returns:
            解析后的代币账户信息
        """
        return self._make_request("getParsedTokenAccountsByOwner", 
                                [{"owner": owner, "programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"}])