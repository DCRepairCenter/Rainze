"""
AI 模块
AI Module

本模块提供 Rainze 的 AI 服务层，包含：
This module provides Rainze's AI service layer, including:

- **LLM 客户端**: 统一的 LLM API 调用接口 / LLM Client: Unified LLM API interface
- **响应生成**: 三层响应策略 (Tier1/2/3) / Generation: Three-tier response strategy
- **配置模型**: Pydantic 配置验证 / Schemas: Pydantic config validation

Reference:
    - PRD §0.3: 混合响应策略
    - MOD-AI.md: AI 模块设计文档

Exports / 导出:
    - 异常类 / Exceptions:
        - AIError, LLMTimeoutError, LLMRateLimitError, LLMAPIError
        - PromptBuildError, EmbeddingError, AllFallbacksFailedError, GenerationError
    - 配置类 / Config:
        - AIConfig, APIConfig, GenerationConfig
    - LLM 客户端 / LLM Client:
        - LLMClient, LLMRequest, LLMResponse, LLMProvider, LLMClientFactory
        - AnthropicClient
    - 响应生成 / Generation:
        - GeneratedResponse, ResponseGenerator
        - Tier1TemplateGenerator, Tier2RuleGenerator, Tier3LLMGenerator

Example:
    >>> from rainze.ai import (
    ...     LLMClientFactory, LLMProvider, LLMRequest,
    ...     Tier3LLMGenerator, GeneratedResponse
    ... )
    >>>
    >>> # 创建 LLM 客户端 / Create LLM client
    >>> client = LLMClientFactory.create(
    ...     provider=LLMProvider.ANTHROPIC,
    ...     api_key="your-api-key"
    ... )
    >>>
    >>> # 创建 Tier3 生成器 / Create Tier3 generator
    >>> generator = Tier3LLMGenerator(client)
    >>>
    >>> # 生成响应 / Generate response
    >>> response = await generator.generate(
    ...     scene_type="conversation",
    ...     context={},
    ...     user_input="你好！"
    ... )
    >>> print(response.text)

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

# 异常类 / Exceptions
from rainze.ai.exceptions import (
    AIError,
    AllFallbacksFailedError,
    EmbeddingError,
    GenerationError,
    LLMAPIError,
    LLMRateLimitError,
    LLMTimeoutError,
    PromptBuildError,
)

# 响应生成 / Response Generation
from rainze.ai.generation import (
    GeneratedResponse,
    ResponseGenerator,
    Tier1TemplateGenerator,
    Tier2RuleGenerator,
    Tier3LLMGenerator,
)

# LLM 客户端 / LLM Client
from rainze.ai.llm import (
    LLMClient,
    LLMClientFactory,
    LLMProvider,
    LLMRequest,
    LLMResponse,
)
from rainze.ai.llm.providers import AnthropicClient

# 配置类 / Configuration classes
from rainze.ai.schemas import (
    AIConfig,
    APIConfig,
    EmbeddingConfig,
    FallbackAPIConfig,
    GenerationConfig,
    PromptConfig,
    RateLimitsConfig,
    ResponseCacheConfig,
)

__all__: list[str] = [
    # 异常 / Exceptions
    "AIError",
    "LLMTimeoutError",
    "LLMRateLimitError",
    "LLMAPIError",
    "PromptBuildError",
    "EmbeddingError",
    "AllFallbacksFailedError",
    "GenerationError",
    # 配置 / Config
    "AIConfig",
    "APIConfig",
    "FallbackAPIConfig",
    "RateLimitsConfig",
    "GenerationConfig",
    "EmbeddingConfig",
    "ResponseCacheConfig",
    "PromptConfig",
    # LLM 客户端 / LLM Client
    "LLMClient",
    "LLMRequest",
    "LLMResponse",
    "LLMProvider",
    "LLMClientFactory",
    "AnthropicClient",
    # 响应生成 / Generation
    "GeneratedResponse",
    "ResponseGenerator",
    "Tier1TemplateGenerator",
    "Tier2RuleGenerator",
    "Tier3LLMGenerator",
]

# 模块版本 / Module version
__version__ = "0.1.0"
