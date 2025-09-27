"""
LLM service connector for news analysis integration
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import hashlib
import aiohttp

from ..models.base import NewsArticle


class LLMProvider(Enum):
    """LLM服务提供商枚举"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    MOCK = "mock"


@dataclass
class LLMConfig:
    """LLM配置"""
    provider: LLMProvider = LLMProvider.MOCK
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 2000
    temperature: float = 0.3
    timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0
    enable_cache: bool = True
    cache_ttl: int = 3600  # 1 hour

    # OpenAI specific
    openai_organization: Optional[str] = None

    # Anthropic specific
    anthropic_version: str = "2023-06-01"

    # Local model specific
    local_endpoint: Optional[str] = None


@dataclass
class LLMMessage:
    """LLM消息"""
    role: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    usage: Dict[str, Any]
    model: str
    provider: LLMProvider
    response_time: float
    cached: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMError:
    """LLM错误"""
    error_type: str
    error_message: str
    provider: LLMProvider
    retry_count: int
    timestamp: float


class LLMProviderInterface(ABC):
    """LLM提供商接口"""

    @abstractmethod
    async def generate_response(self, messages: List[LLMMessage], config: LLMConfig) -> LLMResponse:
        """生成响应"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass


class OpenAIProvider(LLMProviderInterface):
    """OpenAI提供商实现"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.base_url = config.base_url or "https://api.openai.com/v1"

    async def generate_response(self, messages: List[LLMMessage], config: LLMConfig) -> LLMResponse:
        """生成响应"""
        start_time = time.time()

        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }

        if config.openai_organization:
            headers["OpenAI-Organization"] = config.openai_organization

        # 转换消息格式
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        payload = {
            "model": config.model,
            "messages": openai_messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature
        }

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.timeout)) as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        choice = data["choices"][0]

                        usage = {
                            "prompt_tokens": data["usage"]["prompt_tokens"],
                            "completion_tokens": data["usage"]["completion_tokens"],
                            "total_tokens": data["usage"]["total_tokens"]
                        }

                        return LLMResponse(
                            content=choice["message"]["content"],
                            usage=usage,
                            model=config.model,
                            provider=LLMProvider.OPENAI,
                            response_time=time.time() - start_time,
                            metadata={"finish_reason": choice.get("finish_reason")}
                        )
                    else:
                        error_data = await response.json()
                        raise Exception(f"OpenAI API error: {error_data.get('error', {}).get('message', 'Unknown error')}")

        except Exception as e:
            self.logger.error(f"OpenAI API call failed: {str(e)}")
            raise

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            headers = {"Authorization": f"Bearer {self.config.api_key}"}
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/models", headers=headers) as response:
                    return response.status == 200
        except Exception:
            return False


class AnthropicProvider(LLMProviderInterface):
    """Anthropic提供商实现"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.base_url = config.base_url or "https://api.anthropic.com"

    async def generate_response(self, messages: List[LLMMessage], config: LLMConfig) -> LLMResponse:
        """生成响应"""
        start_time = time.time()

        headers = {
            "x-api-key": config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": config.anthropic_version
        }

        # Anthropic使用不同的消息格式
        system_messages = [msg.content for msg in messages if msg.role == "system"]
        user_messages = [msg for msg in messages if msg.role != "system"]

        if len(user_messages) == 0:
            raise ValueError("No user messages found")

        # 构建对话历史
        messages_array = []
        for msg in user_messages:
            if msg.role == "user":
                messages_array.append({"role": "user", "content": msg.content})
            elif msg.role == "assistant":
                messages_array.append({"role": "assistant", "content": msg.content})

        payload = {
            "model": config.model,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "messages": messages_array
        }

        if system_messages:
            payload["system"] = system_messages[0]

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.timeout)) as session:
                async with session.post(
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=payload
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        content = data["content"][0]["text"]

                        usage = {
                            "input_tokens": data.get("usage", {}).get("input_tokens", 0),
                            "output_tokens": data.get("usage", {}).get("output_tokens", 0)
                        }

                        return LLMResponse(
                            content=content,
                            usage=usage,
                            model=config.model,
                            provider=LLMProvider.ANTHROPIC,
                            response_time=time.time() - start_time,
                            metadata={"stop_reason": data.get("stop_reason")}
                        )
                    else:
                        error_data = await response.json()
                        raise Exception(f"Anthropic API error: {error_data.get('error', {}).get('message', 'Unknown error')}")

        except Exception as e:
            self.logger.error(f"Anthropic API call failed: {str(e)}")
            raise

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            headers = {"x-api-key": self.config.api_key}
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/messages", headers=headers) as response:
                    return response.status == 200
        except Exception:
            return False


class MockProvider(LLMProviderInterface):
    """Mock提供商用于测试"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    async def generate_response(self, messages: List[LLMMessage], config: LLMConfig) -> LLMResponse:
        """生成模拟响应"""
        start_time = time.time()

        # 模拟处理延迟
        await asyncio.sleep(0.1)

        # 获取用户消息
        user_messages = [msg for msg in messages if msg.role == "user"]
        if not user_messages:
            raise ValueError("No user messages found")

        last_message = user_messages[-1].content

        # 生成基于消息类型的模拟响应
        if "summarize" in last_message.lower():
            mock_response = "This is a mock summary of the news article. The key points have been extracted and presented in a concise format."
        elif "sentiment" in last_message.lower():
            mock_response = '{"sentiment": "neutral", "confidence": 0.75, "explanation": "The article presents balanced information without strong emotional bias."}'
        elif "extract" in last_message.lower() and "entity" in last_message.lower():
            mock_response = '{"entities": [{"type": "organization", "name": "Bitcoin"}, {"type": "person", "name": "Elon Musk"}]}'
        else:
            mock_response = "This is a mock response from the LLM service."

        return LLMResponse(
            content=mock_response,
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            model=config.model,
            provider=LLMProvider.MOCK,
            response_time=time.time() - start_time
        )

    async def health_check(self) -> bool:
        """健康检查"""
        return True


class CacheManager:
    """缓存管理器"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.cache = {}
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}

    def _generate_cache_key(self, messages: List[LLMMessage], config: LLMConfig) -> str:
        """生成缓存键"""
        # 将消息序列化为字符串
        messages_str = json.dumps([
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ], sort_keys=True)

        # 包含配置参数
        config_str = f"{config.model}_{config.max_tokens}_{config.temperature:.2f}"

        # 生成哈希键
        key = hashlib.md5(f"{messages_str}_{config_str}".encode()).hexdigest()
        return key

    def get(self, messages: List[LLMMessage], config: LLMConfig) -> Optional[LLMResponse]:
        """获取缓存响应"""
        if not self.config.enable_cache:
            return None

        key = self._generate_cache_key(messages, config)

        if key in self.cache:
            cached_data = self.cache[key]

            # 检查是否过期
            if time.time() - cached_data["timestamp"] < self.config.cache_ttl:
                self.stats["hits"] += 1
                self.logger.debug(f"Cache hit for key: {key}")
                return cached_data["response"]
            else:
                # 过期，删除
                del self.cache[key]
                self.stats["evictions"] += 1

        self.stats["misses"] += 1
        return None

    def set(self, messages: List[LLMMessage], config: LLMConfig, response: LLMResponse):
        """设置缓存"""
        if not self.config.enable_cache:
            return

        key = self._generate_cache_key(messages, config)

        # 标记为缓存响应
        cached_response = LLMResponse(
            content=response.content,
            usage=response.usage,
            model=response.model,
            provider=response.provider,
            response_time=response.response_time,
            cached=True,
            metadata=response.metadata.copy()
        )

        self.cache[key] = {
            "response": cached_response,
            "timestamp": time.time()
        }

        # 限制缓存大小
        if len(self.cache) > 1000:
            # 删除最旧的条目
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]
            self.stats["evictions"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            "cache_size": len(self.cache),
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": hit_rate,
            "evictions": self.stats["evictions"]
        }

    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}
        self.logger.info("Cache cleared")


class LLMConnector:
    """LLM连接器主类"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        # 初始化提供商
        self.provider = self._init_provider()

        # 初始化缓存
        self.cache = CacheManager(config)

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens_used": 0,
            "average_response_time": 0.0
        }

    def _init_provider(self) -> LLMProviderInterface:
        """初始化提供商"""
        if self.config.provider == LLMProvider.OPENAI:
            return OpenAIProvider(self.config)
        elif self.config.provider == LLMProvider.ANTHROPIC:
            return AnthropicProvider(self.config)
        elif self.config.provider == LLMProvider.LOCAL:
            # TODO: 实现本地模型提供商
            raise NotImplementedError("Local provider not implemented yet")
        else:
            return MockProvider(self.config)

    async def generate_response(self, messages: List[LLMMessage], config: Optional[LLMConfig] = None) -> LLMResponse:
        """生成响应"""
        config = config or self.config
        self.stats["total_requests"] += 1

        # 检查缓存
        cached_response = self.cache.get(messages, config)
        if cached_response:
            return cached_response

        # 重试逻辑
        last_error = None
        for attempt in range(config.retry_attempts):
            try:
                response = await self.provider.generate_response(messages, config)

                # 缓存响应
                self.cache.set(messages, config, response)

                # 更新统计
                self.stats["successful_requests"] += 1
                self.stats["total_tokens_used"] += response.usage.get("total_tokens", 0)

                # 更新平均响应时间
                total_time = self.stats["average_response_time"] * (self.stats["successful_requests"] - 1)
                total_time += response.response_time
                self.stats["average_response_time"] = total_time / self.stats["successful_requests"]

                return response

            except Exception as e:
                last_error = e
                self.logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")

                if attempt < config.retry_attempts - 1:
                    await asyncio.sleep(config.retry_delay * (2 ** attempt))  # 指数退避

        # 所有尝试都失败
        self.stats["failed_requests"] += 1
        error = LLMError(
            error_type="request_failed",
            error_message=str(last_error),
            provider=config.provider,
            retry_count=config.retry_attempts,
            timestamp=time.time()
        )
        self.logger.error(f"LLM request failed after {config.retry_attempts} attempts: {error}")
        raise error

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        provider_healthy = await self.provider.health_check()

        return {
            "provider": self.config.provider.value,
            "healthy": provider_healthy,
            "cache_stats": self.cache.get_stats(),
            "request_stats": self.stats
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "provider": self.config.provider.value,
            "model": self.config.model,
            "stats": self.stats,
            "cache_stats": self.cache.get_stats()
        }

    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        self.logger.info("LLM cache cleared")

    def update_config(self, config: LLMConfig):
        """更新配置"""
        self.config = config
        self.provider = self._init_provider()
        self.cache = CacheManager(config)
        self.logger.info("LLM connector configuration updated")

    async def close(self):
        """关闭连接器"""
        self.logger.info("LLM connector closed")