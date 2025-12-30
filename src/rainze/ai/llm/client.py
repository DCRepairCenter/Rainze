"""
LLM 客户端抽象层
LLM Client Abstraction Layer

本模块定义 LLM 客户端的抽象接口和数据结构。
This module defines LLM client abstract interface and data structures.

Reference:
    - PRD §0.3: 混合响应策略
    - MOD-AI.md §3.3: LLMClient

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from rainze.ai.schemas import APIConfig


class LLMProvider(Enum):
    """
    LLM 提供商枚举
    LLM Provider Enumeration

    支持的 LLM 服务提供商。
    Supported LLM service providers.
    """

    ANTHROPIC = "anthropic"
    OPENAI = "openai"


@dataclass
class LLMRequest:
    """
    LLM 请求数据结构
    LLM Request Data Structure

    封装发送给 LLM API 的请求参数。
    Encapsulates parameters sent to LLM API.

    Attributes:
        system: 系统提示词 / System prompt
        messages: 消息列表 / Message list
        model: 模型名称 / Model name
        temperature: 温度参数 / Temperature parameter
        max_tokens: 最大输出 Token 数 / Max output tokens
        timeout_seconds: 超时时间（秒）/ Timeout in seconds
        stop_sequences: 停止序列 / Stop sequences
    """

    system: str
    messages: List[Dict[str, str]]
    model: str
    temperature: float = 0.8
    max_tokens: int = 150
    timeout_seconds: float = 30.0
    stop_sequences: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """
        验证请求参数
        Validate request parameters
        """
        # 确保温度在有效范围内 / Ensure temperature is in valid range
        self.temperature = max(0.0, min(2.0, self.temperature))
        # 确保 max_tokens 为正数 / Ensure max_tokens is positive
        self.max_tokens = max(1, self.max_tokens)
        # 确保超时为正数 / Ensure timeout is positive
        self.timeout_seconds = max(1.0, self.timeout_seconds)


@dataclass
class LLMResponse:
    """
    LLM 响应数据结构
    LLM Response Data Structure

    封装从 LLM API 接收的响应。
    Encapsulates response received from LLM API.

    Attributes:
        content: 生成的文本内容 / Generated text content
        model: 实际使用的模型 / Model actually used
        usage: Token 使用统计 / Token usage statistics
        finish_reason: 完成原因 / Finish reason
        latency_ms: 响应延迟（毫秒）/ Response latency in ms
    """

    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"
    latency_ms: float = 0.0

    @property
    def input_tokens(self) -> int:
        """
        获取输入 Token 数
        Get input token count
        """
        return self.usage.get("input_tokens", 0)

    @property
    def output_tokens(self) -> int:
        """
        获取输出 Token 数
        Get output token count
        """
        return self.usage.get("output_tokens", 0)

    @property
    def total_tokens(self) -> int:
        """
        获取总 Token 数
        Get total token count
        """
        return self.input_tokens + self.output_tokens


class LLMClient(ABC):
    """
    LLM 客户端抽象基类
    LLM Client Abstract Base Class

    定义统一的 LLM API 调用接口，所有具体提供商实现必须继承此类。
    Defines unified LLM API interface, all provider implementations must inherit.

    Subclasses / 子类:
        - AnthropicClient: Anthropic Claude API
        - OpenAIClient: OpenAI GPT API (future)
    """

    @property
    @abstractmethod
    def provider(self) -> LLMProvider:
        """
        获取提供商类型
        Get provider type

        Returns:
            提供商枚举值 / Provider enum value
        """
        ...

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """
        检查客户端是否可用
        Check if client is available

        Returns:
            是否可用 / Whether available
        """
        ...

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        生成响应（非流式）
        Generate response (non-streaming)

        Args:
            request: LLM 请求 / LLM request

        Returns:
            LLM 响应 / LLM response

        Raises:
            LLMTimeoutError: 请求超时 / Request timeout
            LLMRateLimitError: 达到速率限制 / Rate limit reached
            LLMAPIError: API 返回错误 / API returned error
        """
        ...

    @abstractmethod
    async def generate_stream(
        self,
        request: LLMRequest,
    ) -> AsyncGenerator[str, None]:
        """
        流式生成响应
        Generate response with streaming

        Args:
            request: LLM 请求 / LLM request

        Yields:
            响应文本片段 / Response text chunks

        Raises:
            LLMTimeoutError: 请求超时 / Request timeout
            LLMRateLimitError: 达到速率限制 / Rate limit reached
            LLMAPIError: API 返回错误 / API returned error
        """
        # Abstract method stub - must yield to make it a generator
        # 抽象方法存根 - 必须 yield 以使其成为生成器
        yield ""  # pragma: no cover

    async def close(self) -> None:
        """
        关闭客户端连接
        Close client connection

        子类可重写以释放资源。
        Subclasses may override to release resources.
        """
        pass


class LLMClientFactory:
    """
    LLM 客户端工厂
    LLM Client Factory

    根据配置创建对应的 LLM 客户端实例。
    Creates appropriate LLM client instance based on configuration.
    """

    @staticmethod
    def create(
        provider: LLMProvider,
        api_key: str,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> LLMClient:
        """
        创建 LLM 客户端
        Create LLM client

        Args:
            provider: 提供商类型 / Provider type
            api_key: API 密钥 / API key
            base_url: 自定义 API 地址 / Custom API URL
            default_model: 默认模型 / Default model
            timeout_seconds: 超时时间 / Timeout seconds

        Returns:
            LLM 客户端实例 / LLM client instance

        Raises:
            ValueError: 不支持的提供商 / Unsupported provider
        """
        # 延迟导入以避免循环依赖 / Lazy import to avoid circular dependency
        if provider == LLMProvider.ANTHROPIC:
            from rainze.ai.llm.providers.anthropic import AnthropicClient

            return AnthropicClient(
                api_key=api_key,
                base_url=base_url,
                default_model=default_model or "claude-sonnet-4-20250514",
                timeout_seconds=timeout_seconds or 30,
            )
        elif provider == LLMProvider.OPENAI:
            # TODO: 实现 OpenAI 客户端 / Implement OpenAI client
            raise NotImplementedError(
                "OpenAI client not yet implemented / OpenAI 客户端尚未实现"
            )
        else:
            raise ValueError(
                f"Unsupported provider: {provider} / 不支持的提供商: {provider}"
            )

    @staticmethod
    def from_config(config: "APIConfig") -> LLMClient:
        """
        从配置创建客户端
        Create client from configuration

        Args:
            config: API 配置 / API configuration

        Returns:
            LLM 客户端实例 / LLM client instance

        Raises:
            ValueError: 配置无效或 API 密钥未设置 / Invalid config or API key not set
        """
        import os

        # 从环境变量获取 API 密钥 / Get API key from environment
        api_key = os.environ.get(config.api_key_env, "")
        if not api_key:
            raise ValueError(
                f"API key not found in environment variable: {config.api_key_env} / "
                f"环境变量中未找到 API 密钥: {config.api_key_env}"
            )

        # 解析提供商 / Parse provider
        try:
            provider = LLMProvider(config.provider)
        except ValueError as e:
            raise ValueError(
                f"Unknown provider: {config.provider} / 未知提供商: {config.provider}"
            ) from e

        return LLMClientFactory.create(
            provider=provider,
            api_key=api_key,
            base_url=config.base_url,
            default_model=config.default_model,
            timeout_seconds=config.timeout_seconds,
        )
