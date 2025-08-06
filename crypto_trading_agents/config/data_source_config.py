"""
数据源配置管理
"""

import os
from typing import Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)

class DataSourceConfig:
    """数据源配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化数据源配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file or "data_source_config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        # 默认配置
        default_config = {
            "price_data": {
                "binance": {
                    "api_key": os.getenv("BINANCE_API_KEY", ""),
                    "api_secret": os.getenv("BINANCE_API_SECRET", ""),
                    "enabled": True,
                    "priority": 1,
                    "rate_limit": 1200,
                },
                "coinbase": {
                    "api_key": os.getenv("COINBASE_API_KEY", ""),
                    "api_secret": os.getenv("COINBASE_API_SECRET", ""),
                    "passphrase": os.getenv("COINBASE_PASSPHRASE", ""),
                    "enabled": False,
                    "priority": 2,
                    "rate_limit": 10,
                },
                "coingecko": {
                    "api_key": os.getenv("COINGECKO_API_KEY", ""),
                    "demo_mode": os.getenv("COINGECKO_DEMO_MODE", "true").lower() == "true",
                    "enabled": True,
                    "priority": 3,
                    "rate_limit": 50,
                },
                "coinmarketcap": {
                    "api_key": os.getenv("COINMARKETCAP_API_KEY", ""),
                    "enabled": False,
                    "priority": 4,
                    "rate_limit": 333,
                },
            },
            "onchain_data": {
                "glassnode": {
                    "api_key": os.getenv("GLASSNODE_API_KEY", ""),
                    "enabled": False,
                    "priority": 1,
                    "rate_limit": 100,
                },
                "intotheblock": {
                    "api_key": os.getenv("INTOTHEBLOCK_API_KEY", ""),
                    "enabled": False,
                    "priority": 2,
                    "rate_limit": 60,
                },
                "nansen": {
                    "api_key": os.getenv("NANSEN_API_KEY", ""),
                    "enabled": False,
                    "priority": 3,
                    "rate_limit": 60,
                },
                "chainalysis": {
                    "api_key": os.getenv("CHAINALYSIS_API_KEY", ""),
                    "enabled": False,
                    "priority": 4,
                    "rate_limit": 120,
                },
            },
            "defi_data": {
                "defillama": {
                    "api_key": os.getenv("DEFILLAMA_API_KEY", ""),
                    "enabled": True,
                    "priority": 1,
                    "rate_limit": 100,
                },
                "debank": {
                    "api_key": os.getenv("DEBANK_API_KEY", ""),
                    "enabled": False,
                    "priority": 2,
                    "rate_limit": 100,
                },
                "zapper": {
                    "api_key": os.getenv("ZAPPER_API_KEY", ""),
                    "enabled": False,
                    "priority": 3,
                    "rate_limit": 60,
                },
            },
            "news_data": {
                "cryptopanic": {
                    "api_key": os.getenv("CRYPTOPANIC_API_KEY", ""),
                    "enabled": True,
                    "priority": 1,
                    "rate_limit": 100,
                },
                "coindesk": {
                    "api_key": "",
                    "enabled": True,
                    "priority": 2,
                    "rate_limit": 60,
                },
                "cointelegraph": {
                    "api_key": "",
                    "enabled": True,
                    "priority": 3,
                    "rate_limit": 60,
                },
            },
            "social_data": {
                "lunarcrush": {
                    "api_key": os.getenv("LUNARCRUSH_API_KEY", ""),
                    "enabled": False,
                    "priority": 1,
                    "rate_limit": 120,
                },
                "santiment": {
                    "api_key": os.getenv("SANTIMENT_API_KEY", ""),
                    "enabled": False,
                    "priority": 2,
                    "rate_limit": 60,
                },
                "glassnode_social": {
                    "api_key": os.getenv("GLASSNODE_API_KEY", ""),
                    "enabled": False,
                    "priority": 3,
                    "rate_limit": 50,
                },
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
    
    def get_data_source_config(self, category: str, source: str) -> Dict[str, Any]:
        """
        获取数据源配置
        
        Args:
            category: 数据类别
            source: 数据源名称
            
        Returns:
            数据源配置
        """
        return self.config.get(category, {}).get(source, {})
    
    def is_data_source_enabled(self, category: str, source: str) -> bool:
        """
        检查数据源是否启用
        
        Args:
            category: 数据类别
            source: 数据源名称
            
        Returns:
            是否启用
        """
        config = self.get_data_source_config(category, source)
        return config.get("enabled", False)
    
    def get_enabled_sources(self, category: str) -> list:
        """
        获取指定类别的启用数据源
        
        Args:
            category: 数据类别
            
        Returns:
            启用的数据源列表（按优先级排序）
        """
        sources = []
        for source_name, config in self.config.get(category, {}).items():
            if config.get("enabled", False):
                sources.append((source_name, config.get("priority", 999)))
        
        # 按优先级排序
        sources.sort(key=lambda x: x[1])
        return [source[0] for source in sources]
    
    def get_data_source_credentials(self, category: str, source: str) -> Dict[str, str]:
        """
        获取数据源凭证
        
        Args:
            category: 数据类别
            source: 数据源名称
            
        Returns:
            凭证字典
        """
        config = self.get_data_source_config(category, source)
        credentials = {}
        
        # 常见凭证字段
        credential_fields = ["api_key", "api_secret", "passphrase"]
        for field in credential_fields:
            if field in config:
                credentials[field] = config[field]
        
        return credentials
    
    def get_rate_limit(self, category: str, source: str) -> int:
        """
        获取数据源速率限制
        
        Args:
            category: 数据类别
            source: 数据源名称
            
        Returns:
            速率限制
        """
        config = self.get_data_source_config(category, source)
        return config.get("rate_limit", 60)
    
    def get_fallback_sources(self, category: str) -> list:
        """
        获取备用数据源列表
        
        Args:
            category: 数据类别
            
        Returns:
            备用数据源列表
        """
        return self.get_enabled_sources(category)
    
    def update_data_source_config(self, category: str, source: str, updates: Dict[str, Any]):
        """
        更新数据源配置
        
        Args:
            category: 数据类别
            source: 数据源名称
            updates: 更新的配置
        """
        if category in self.config and source in self.config[category]:
            self.config[category][source].update(updates)
            self._save_config()
        else:
            logger.warning(f"Data source {source} in category {category} not found")
    
    def enable_data_source(self, category: str, source: str):
        """启用数据源"""
        self.update_data_source_config(category, source, {"enabled": True})
    
    def disable_data_source(self, category: str, source: str):
        """禁用数据源"""
        self.update_data_source_config(category, source, {"enabled": False})
    
    def set_priority(self, category: str, source: str, priority: int):
        """设置优先级"""
        self.update_data_source_config(category, source, {"priority": priority})
    
    def _save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"Data source config saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save data source config: {str(e)}")
    
    def validate_data_source_config(self, category: str, source: str) -> bool:
        """
        验证数据源配置
        
        Args:
            category: 数据类别
            source: 数据源名称
            
        Returns:
            配置是否有效
        """
        config = self.get_data_source_config(category, source)
        
        # 检查是否启用
        if not config.get("enabled", False):
            return False
        
        # 某些数据源需要API密钥
        sources_requiring_keys = [
            ("price_data", "binance"),
            ("price_data", "coinbase"),
            ("onchain_data", "glassnode"),
            ("social_data", "lunarcrush"),
        ]
        
        if (category, source) in sources_requiring_keys:
            if not config.get("api_key"):
                logger.warning(f"API key required for {category}/{source}")
                return False
        
        return True
    
    def get_data_source_info(self, category: str, source: str) -> Dict[str, Any]:
        """
        获取数据源信息
        
        Args:
            category: 数据类别
            source: 数据源名称
            
        Returns:
            数据源信息
        """
        config = self.get_data_source_config(category, source)
        
        return {
            "category": category,
            "source": source,
            "enabled": config.get("enabled", False),
            "priority": config.get("priority", 999),
            "rate_limit": config.get("rate_limit", 60),
            "has_credentials": bool(config.get("api_key")),
            "validation_passed": self.validate_data_source_config(category, source),
            "demo_mode": config.get("demo_mode", False),
        }
    
    def get_category_info(self, category: str) -> Dict[str, Any]:
        """
        获取数据类别信息
        
        Args:
            category: 数据类别
            
        Returns:
            类别信息
        """
        enabled_sources = self.get_enabled_sources(category)
        total_sources = len(self.config.get(category, {}))
        
        return {
            "category": category,
            "total_sources": total_sources,
            "enabled_sources": len(enabled_sources),
            "enabled_source_list": enabled_sources,
            "has_enabled_sources": len(enabled_sources) > 0,
        }
    
    def get_all_data_sources_status(self) -> Dict[str, Any]:
        """
        获取所有数据源状态
        
        Returns:
            所有数据源状态
        """
        status = {}
        
        for category, sources in self.config.items():
            status[category] = self.get_category_info(category)
            
            # 添加每个数据源的详细信息
            status[category]["sources"] = {}
            for source in sources:
                status[category]["sources"][source] = self.get_data_source_info(category, source)
        
        return status
    
    def get_recommended_sources(self, category: str) -> list:
        """
        获取推荐的数据源
        
        Args:
            category: 数据类别
            
        Returns:
            推荐的数据源列表
        """
        recommendations = {
            "price_data": ["binance", "coingecko", "coinmarketcap"],
            "onchain_data": ["glassnode", "intotheblock"],
            "defi_data": ["defillama", "debank"],
            "news_data": ["cryptopanic", "coindesk", "cointelegraph"],
            "social_data": ["lunarcrush", "santiment"],
        }
        
        return recommendations.get(category, [])
    
    def get_data_source_costs(self) -> Dict[str, Any]:
        """
        获取数据源成本信息
        
        Returns:
            成本信息字典
        """
        # 这里提供大致的成本信息，实际成本可能因使用量而异
        cost_info = {
            "price_data": {
                "binance": "Free (API)",
                "coinbase": "Free (API)",
                "coingecko": "Free tier / $10-100/month paid",
                "coinmarketcap": "Free tier / $100-1000/month paid",
            },
            "onchain_data": {
                "glassnode": "$29-799/month",
                "intotheblock": "Custom pricing",
                "nansen": "$1500-5000/month",
                "chainalysis": "Enterprise pricing",
            },
            "defi_data": {
                "defillama": "Free",
                "debank": "Free tier / Pro plan available",
                "zapper": "Free (API)",
            },
            "news_data": {
                "cryptopanic": "Free API",
                "coindesk": "Free RSS",
                "cointelegraph": "Free RSS",
            },
            "social_data": {
                "lunarcrush": "$29-399/month",
                "santiment": "$49-999/month",
                "glassnode_social": "Included with Glassnode",
            },
        }
        
        return cost_info