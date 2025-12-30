"""
AI 模块异常定义
AI Module Exception Definitions

本模块定义 AI 服务相关的所有异常类。
This module defines all AI service related exception classes.

Reference:
    - PRD §0.3: 混合响应策略
    - MOD-AI.md §5: 异常定义

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from rainze.core.exceptions import RainzeError


class AIError(RainzeError):
    """
    AI 模块基础异常
    Base exception for AI module

    所有 AI 相关异常继承此类。
    All AI related exceptions inherit from this class.
    """

    def __init__(self, message: str) -> None:
        """
        初始化 AI 异常 / Initialize AI exception

        Args:
            message: 错误描述 / Error description
        """
        super().__init__(message, "AI_ERROR")


class LLMTimeoutError(AIError):
    """
    LLM 调用超时错误
    LLM call timeout error

    当 LLM API 调用超过指定时间未响应时抛出。
    Raised when LLM API call exceeds specified timeout.

    Attributes:
        timeout_seconds: 超时时间（秒）/ Timeout in seconds
    """

    def __init__(self, message: str, timeout_seconds: float = 0) -> None:
        """
        初始化超时异常 / Initialize timeout exception

        Args:
            message: 错误描述 / Error description
            timeout_seconds: 超时时间 / Timeout duration
        """
        super().__init__(message)
        self.code = "LLM_TIMEOUT"
        self.timeout_seconds = timeout_seconds


class LLMRateLimitError(AIError):
    """
    LLM 限流错误
    LLM rate limit error

    当达到 API 速率限制时抛出。
    Raised when API rate limit is reached.

    Attributes:
        retry_after: 建议重试时间（秒）/ Suggested retry time in seconds
    """

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        """
        初始化限流异常 / Initialize rate limit exception

        Args:
            message: 错误描述 / Error description
            retry_after: 建议重试等待时间 / Suggested retry wait time
        """
        super().__init__(message)
        self.code = "LLM_RATE_LIMIT"
        self.retry_after = retry_after


class LLMAPIError(AIError):
    """
    LLM API 错误
    LLM API error

    当 API 返回错误响应时抛出。
    Raised when API returns error response.

    Attributes:
        status_code: HTTP 状态码 / HTTP status code
        provider: 提供商名称 / Provider name
    """

    def __init__(
        self,
        message: str,
        status_code: int = 0,
        provider: str | None = None,
    ) -> None:
        """
        初始化 API 异常 / Initialize API exception

        Args:
            message: 错误描述 / Error description
            status_code: HTTP 状态码 / HTTP status code
            provider: 提供商名称 / Provider name
        """
        super().__init__(message)
        self.code = "LLM_API_ERROR"
        self.status_code = status_code
        self.provider = provider


class PromptBuildError(AIError):
    """
    Prompt 构建错误
    Prompt build error

    当 Prompt 构建过程中发生错误时抛出。
    Raised when error occurs during prompt building.

    Attributes:
        layer: 发生错误的层 / Layer where error occurred
    """

    def __init__(self, message: str, layer: str | None = None) -> None:
        """
        初始化 Prompt 构建异常 / Initialize prompt build exception

        Args:
            message: 错误描述 / Error description
            layer: 发生错误的层名称 / Layer name where error occurred
        """
        super().__init__(message)
        self.code = "PROMPT_BUILD_ERROR"
        self.layer = layer


class EmbeddingError(AIError):
    """
    向量化错误
    Embedding error

    当文本向量化过程中发生错误时抛出。
    Raised when error occurs during text embedding.
    """

    def __init__(self, message: str) -> None:
        """
        初始化向量化异常 / Initialize embedding exception

        Args:
            message: 错误描述 / Error description
        """
        super().__init__(message)
        self.code = "EMBEDDING_ERROR"


class AllFallbacksFailedError(AIError):
    """
    所有降级策略失败错误
    All fallback strategies failed error

    当所有降级策略都失败时抛出，这是最后的错误状态。
    Raised when all fallback strategies have failed.

    Attributes:
        original_error: 原始错误 / Original error that triggered fallback
        attempted_levels: 已尝试的降级级别 / Attempted fallback levels
    """

    def __init__(
        self,
        message: str,
        original_error: Exception | None = None,
        attempted_levels: list[str] | None = None,
    ) -> None:
        """
        初始化降级失败异常 / Initialize fallback failed exception

        Args:
            message: 错误描述 / Error description
            original_error: 触发降级的原始错误 / Original error that triggered fallback
            attempted_levels: 已尝试的降级级别列表 / List of attempted fallback levels
        """
        super().__init__(message)
        self.code = "ALL_FALLBACKS_FAILED"
        self.original_error = original_error
        self.attempted_levels = attempted_levels or []


class GenerationError(AIError):
    """
    响应生成错误
    Response generation error

    当响应生成过程中发生错误时抛出。
    Raised when error occurs during response generation.

    Attributes:
        tier: 发生错误的响应层级 / Response tier where error occurred
    """

    def __init__(self, message: str, tier: str | None = None) -> None:
        """
        初始化生成异常 / Initialize generation exception

        Args:
            message: 错误描述 / Error description
            tier: 发生错误的层级 / Tier where error occurred
        """
        super().__init__(message)
        self.code = "GENERATION_ERROR"
        self.tier = tier
