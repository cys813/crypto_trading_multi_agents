"""
加密货币交易所API配置管理
"""

import os
from typing import Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)

class ExchangeConfig:
    """交易所配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file or "exchange_config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        # 默认配置
        default_config = {
            "binance": {
                "api_key": os.getenv("BINANCE_API_KEY", ""),
                "api_secret": os.getenv("BINANCE_API_SECRET", ""),
                "testnet": os.getenv("BINANCE_TESTNET", "false").lower() == "true",
                "base_url": "https://api.binance.com",
                "testnet_url": "https://testnet.binance.vision",
                "rate_limit": 1200,  # 每分钟请求数
                "timeout": 10,
                "enabled": True,
            },
            "coinbase": {
                "api_key": os.getenv("COINBASE_API_KEY", ""),
                "api_secret": os.getenv("COINBASE_API_SECRET", ""),
                "passphrase": os.getenv("COINBASE_PASSPHRASE", ""),
                "base_url": "https://api.coinbase.com",
                "sandbox_url": "https://api-public.sandbox.pro.coinbase.com",
                "rate_limit": 10,  # 每秒请求数
                "timeout": 30,
                "enabled": False,
            },
            "ftx": {
                "api_key": os.getenv("FTX_API_KEY", ""),
                "api_secret": os.getenv("FTX_API_SECRET", ""),
                "base_url": "https://ftx.com/api",
                "rate_limit": 30,  # 每秒请求数
                "timeout": 10,
                "enabled": False,
            },
            "okx": {
                "api_key": os.getenv("OKX_API_KEY", ""),
                "api_secret": os.getenv("OKX_API_SECRET", ""),
                "passphrase": os.getenv("OKX_PASSPHRASE", ""),
                "base_url": "https://www.okx.com",
                "demo_url": "https://www.okx.com",
                "rate_limit": 20,  # 每秒请求数
                "timeout": 10,
                "enabled": False,
            },
            "huobi": {
                "api_key": os.getenv("HUOBI_API_KEY", ""),
                "api_secret": os.getenv("HUOBI_API_SECRET", ""),
                "base_url": "https://api.huobi.pro",
                "rate_limit": 100,  # 每分钟请求数
                "timeout": 10,
                "enabled": False,
            },
        }
        
        # 如果配置文件存在，加载并合并
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self._merge_config(default_config, file_config)
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_file}: {str(e)}")
        
        return default_config
    
    def _merge_config(self, base: Dict[str, Any], update: Dict[str, Any]):
        """递归合并配置"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get_exchange_config(self, exchange: str) -> Dict[str, Any]:
        """
        获取指定交易所的配置
        
        Args:
            exchange: 交易所名称
            
        Returns:
            交易所配置
        """
        return self.config.get(exchange, {})
    
    def is_exchange_enabled(self, exchange: str) -> bool:
        """
        检查交易所是否启用
        
        Args:
            exchange: 交易所名称
            
        Returns:
            是否启用
        """
        config = self.get_exchange_config(exchange)
        return config.get("enabled", False)
    
    def get_enabled_exchanges(self) -> list:
        """
        获取启用的交易所列表
        
        Returns:
            启用的交易所名称列表
        """
        return [name for name, config in self.config.items() if config.get("enabled", False)]
    
    def get_api_credentials(self, exchange: str) -> Dict[str, str]:
        """
        获取API凭证
        
        Args:
            exchange: 交易所名称
            
        Returns:
            API凭证字典
        """
        config = self.get_exchange_config(exchange)
        
        credentials = {
            "api_key": config.get("api_key", ""),
            "api_secret": config.get("api_secret", ""),
        }
        
        # 某些交易所需要额外的凭证
        if exchange in ["coinbase", "okx"]:
            credentials["passphrase"] = config.get("passphrase", "")
        
        return credentials
    
    def get_api_url(self, exchange: str, use_testnet: bool = False) -> str:
        """
        获取API URL
        
        Args:
            exchange: 交易所名称
            use_testnet: 是否使用测试网络
            
        Returns:
            API URL
        """
        config = self.get_exchange_config(exchange)
        
        if use_testnet and "testnet_url" in config:
            return config["testnet_url"]
        elif use_testnet and "sandbox_url" in config:
            return config["sandbox_url"]
        else:
            return config.get("base_url", "")
    
    def get_rate_limit(self, exchange: str) -> int:
        """
        获取速率限制
        
        Args:
            exchange: 交易所名称
            
        Returns:
            速率限制
        """
        config = self.get_exchange_config(exchange)
        return config.get("rate_limit", 10)
    
    def get_timeout(self, exchange: str) -> int:
        """
        获取超时时间
        
        Args:
            exchange: 交易所名称
            
        Returns:
            超时时间（秒）
        """
        config = self.get_exchange_config(exchange)
        return config.get("timeout", 10)
    
    def update_config(self, exchange: str, updates: Dict[str, Any]):
        """
        更新交易所配置
        
        Args:
            exchange: 交易所名称
            updates: 更新的配置
        """
        if exchange in self.config:
            self.config[exchange].update(updates)
            self._save_config()
        else:
            logger.warning(f"Exchange {exchange} not found in config")
    
    def enable_exchange(self, exchange: str):
        """启用交易所"""
        self.update_config(exchange, {"enabled": True})
    
    def disable_exchange(self, exchange: str):
        """禁用交易所"""
        self.update_config(exchange, {"enabled": False})
    
    def set_testnet_mode(self, exchange: str, testnet: bool):
        """设置测试网络模式"""
        self.update_config(exchange, {"testnet": testnet})
    
    def _save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"Config saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {str(e)}")
    
    def validate_config(self, exchange: str) -> bool:
        """
        验证交易所配置
        
        Args:
            exchange: 交易所名称
            
        Returns:
            配置是否有效
        """
        config = self.get_exchange_config(exchange)
        
        # 检查必需的配置项
        required_fields = ["api_key", "api_secret", "enabled"]
        for field in required_fields:
            if field not in config or not config[field]:
                logger.warning(f"Missing required field '{field}' for {exchange}")
                return False
        
        # 检查某些交易所的额外字段
        if exchange in ["coinbase", "okx"]:
            if "passphrase" not in config or not config["passphrase"]:
                logger.warning(f"Missing passphrase for {exchange}")
                return False
        
        return True
    
    def get_exchange_features(self, exchange: str) -> Dict[str, Any]:
        """
        获取交易所功能特性
        
        Args:
            exchange: 交易所名称
            
        Returns:
            功能特性字典
        """
        features = {
            "binance": {
                "spot_trading": True,
                "futures_trading": True,
                "margin_trading": True,
                "staking": True,
                "savings": True,
                "api_v3": True,
                "websocket": True,
                "testnet": True,
            },
            "coinbase": {
                "spot_trading": True,
                "futures_trading": False,
                "margin_trading": False,
                "staking": True,
                "savings": False,
                "api_v2": True,
                "websocket": True,
                "sandbox": True,
            },
            "ftx": {
                "spot_trading": True,
                "futures_trading": True,
                "margin_trading": True,
                "staking": False,
                "savings": False,
                "api_v1": True,
                "websocket": True,
                "testnet": False,
            },
            "okx": {
                "spot_trading": True,
                "futures_trading": True,
                "margin_trading": True,
                "staking": True,
                "savings": True,
                "api_v5": True,
                "websocket": True,
                "demo": True,
            },
            "huobi": {
                "spot_trading": True,
                "futures_trading": True,
                "margin_trading": True,
                "staking": True,
                "savings": True,
                "api_v2": True,
                "websocket": True,
                "testnet": False,
            },
        }
        
        return features.get(exchange, {})
    
    def get_supported_symbols(self, exchange: str) -> list:
        """
        获取交易所支持的主要交易对
        
        Args:
            exchange: 交易所名称
            
        Returns:
            支持的交易对列表
        """
        # 这里返回主要加密货币交易对
        common_symbols = [
            "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "ADA/USDT",
            "DOT/USDT", "MATIC/USDT", "AVAX/USDT", "LINK/USDT", "UNI/USDT",
            "BTC/USD", "ETH/USD", "BNB/USD", "SOL/USD", "ADA/USD",
        ]
        
        # 根据交易所特性调整
        exchange_features = self.get_exchange_features(exchange)
        if not exchange_features.get("futures_trading"):
            # 移除期货交易对
            common_symbols = [s for s in common_symbols if not s.endswith("PERP")]
        
        return common_symbols
    
    def get_exchange_info(self, exchange: str) -> Dict[str, Any]:
        """
        获取交易所信息
        
        Args:
            exchange: 交易所名称
            
        Returns:
            交易所信息
        """
        config = self.get_exchange_config(exchange)
        features = self.get_exchange_features(exchange)
        
        return {
            "name": exchange.capitalize(),
            "enabled": config.get("enabled", False),
            "testnet": config.get("testnet", False),
            "features": features,
            "rate_limit": config.get("rate_limit", 10),
            "timeout": config.get("timeout", 10),
            "has_credentials": bool(config.get("api_key") and config.get("api_secret")),
            "validation_passed": self.validate_config(exchange),
        }