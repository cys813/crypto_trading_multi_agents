"""
新闻源适配器基础接口和抽象类
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import asyncio
import aiohttp
from datetime import datetime

from ..models.base import (
    NewsArticle,
    NewsSourceConfig,
    HealthStatus,
    NewsQuery,
    NewsQueryResult,
    NewsSourceStatus,
    ConnectionInfo
)


class NewsSourceAdapter(ABC):
    """新闻源适配器抽象基类"""

    def __init__(self, config: NewsSourceConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self._connection_info: Optional[ConnectionInfo] = None
        self._health_status: Optional[HealthStatus] = None
        self._request_count = 0
        self._error_count = 0

    @property
    @abstractmethod
    def source_name(self) -> str:
        """返回新闻源名称"""
        pass

    @property
    @abstractmethod
    def adapter_type(self) -> str:
        """返回适配器类型"""
        pass

    @abstractmethod
    async def connect(self) -> bool:
        """建立连接"""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """断开连接"""
        pass

    @abstractmethod
    async def fetch_news(self, query: NewsQuery) -> NewsQueryResult:
        """获取新闻"""
        pass

    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """健康检查"""
        pass

    @abstractmethod
    async def get_latest_news(self, limit: int = 20) -> List[NewsArticle]:
        """获取最新新闻"""
        pass

    @abstractmethod
    async def search_news(self, keywords: List[str], limit: int = 50) -> List[NewsArticle]:
        """搜索新闻"""
        pass

    async def initialize(self) -> bool:
        """初始化适配器"""
        try:
            # 创建HTTP会话
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            headers = {
                'User-Agent': 'CryptoNewsAgent/1.0',
                **self.config.headers
            }

            if self.config.api_key:
                headers['Authorization'] = f'Bearer {self.config.api_key}'

            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )

            # 建立连接
            connection_success = await self.connect()

            if connection_success:
                self._connection_info = ConnectionInfo(
                    connection_id=f"{self.source_name}_{datetime.now().timestamp()}",
                    source_name=self.source_name,
                    created_at=datetime.now(),
                    last_used=datetime.now(),
                    is_active=True
                )

            return connection_success

        except Exception as e:
            self._error_count += 1
            print(f"初始化适配器失败: {e}")
            return False

    async def close(self) -> bool:
        """关闭适配器"""
        try:
            if self.session:
                await self.session.close()

            if self._connection_info:
                self._connection_info.is_active = False

            return await self.disconnect()

        except Exception as e:
            self._error_count += 1
            print(f"关闭适配器失败: {e}")
            return False

    async def _make_request(self, url: str, method: str = "GET", **kwargs) -> Optional[Dict[str, Any]]:
        """统一的HTTP请求方法"""
        if not self.session:
            raise RuntimeError("适配器未初始化")

        try:
            start_time = datetime.now()

            async with self.session.request(method, url, **kwargs) as response:
                response_time = (datetime.now() - start_time).total_seconds() * 1000

                if response.status == 200:
                    self._request_count += 1
                    if self._connection_info:
                        self._connection_info.last_used = datetime.now()
                        self._connection_info.request_count += 1

                    return await response.json()
                else:
                    self._error_count += 1
                    if self._connection_info:
                        self._connection_info.error_count += 1

                    error_msg = f"HTTP {response.status}: {await response.text()}"
                    print(f"请求失败: {error_msg}")
                    return None

        except asyncio.TimeoutError:
            self._error_count += 1
            print(f"请求超时: {url}")
            return None
        except Exception as e:
            self._error_count += 1
            print(f"请求异常: {e}")
            return None

    def get_connection_info(self) -> Optional[ConnectionInfo]:
        """获取连接信息"""
        return self._connection_info

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "source_name": self.source_name,
            "request_count": self._request_count,
            "error_count": self._error_count,
            "success_rate": (self._request_count - self._error_count) / max(self._request_count, 1),
            "is_connected": self._connection_info.is_active if self._connection_info else False
        }

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connection_info is not None and self._connection_info.is_active


class NewsSourceAdapterFactory:
    """新闻源适配器工厂"""

    _adapters: Dict[str, type] = {}

    @classmethod
    def register_adapter(cls, adapter_type: str, adapter_class: type):
        """注册适配器"""
        cls._adapters[adapter_type] = adapter_class

    @classmethod
    def create_adapter(cls, config: NewsSourceConfig) -> NewsSourceAdapter:
        """创建适配器实例"""
        if config.adapter_type not in cls._adapters:
            raise ValueError(f"不支持的适配器类型: {config.adapter_type}")

        adapter_class = cls._adapters[config.adapter_type]
        return adapter_class(config)

    @classmethod
    def get_available_adapters(cls) -> List[str]:
        """获取可用适配器列表"""
        return list(cls._adapters.keys())