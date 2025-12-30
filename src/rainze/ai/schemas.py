"""
AI 模块配置 Schema
AI Module Configuration Schemas

本模块定义 AI 服务的所有 Pydantic 配置模型。
This module defines all Pydantic configuration models for AI services.

Reference:
    - PRD §0.3: 混合响应策略
    - MOD-AI.md §4: 配置 Schema

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class APIConfig(BaseModel):
    """
    API 配置
    API Configuration

    定义 LLM API 连接参数。
    Defines LLM API connection parameters.

    Attributes:
        provider: 提供商名称 / Provider name
        base_url: 自定义 API 地址 / Custom API URL
        api_key_env: API 密钥环境变量名 / API key env var name
        default_model: 默认模型 / Default model
        timeout_seconds: 超时时间（秒）/ Timeout in seconds
    """

    provider: str = "anthropic"
    base_url: Optional[str] = None
    api_key_env: str = "ANTHROPIC_API_KEY"
    default_model: str = "claude-sonnet-4-20250514"
    timeout_seconds: int = Field(default=30, ge=5)


class FallbackAPIConfig(BaseModel):
    """
    备用 API 配置
    Fallback API Configuration

    定义主 API 失败时的备用 API 参数。
    Defines fallback API parameters when primary fails.

    Attributes:
        enable: 是否启用 / Whether enabled
        provider: 提供商名称 / Provider name
        api_key_env: API 密钥环境变量名 / API key env var name
        default_model: 默认模型 / Default model
        trigger_on: 触发条件列表 / Trigger conditions
    """

    enable: bool = False
    provider: str = "openai"
    api_key_env: str = "OPENAI_API_KEY"
    default_model: str = "gpt-4o-mini"
    trigger_on: List[str] = Field(
        default_factory=lambda: ["timeout", "rate_limit", "server_error"]
    )


class RateLimitsConfig(BaseModel):
    """
    速率限制配置
    Rate Limits Configuration

    定义 API 调用速率限制。
    Defines API call rate limits.

    Attributes:
        requests_per_minute: 每分钟请求数 / Requests per minute
        requests_per_hour: 每小时请求数 / Requests per hour
        tokens_per_day: 每日 Token 数 / Tokens per day
        enable_queue: 是否启用队列 / Whether to enable queue
        queue_max_size: 队列最大大小 / Max queue size
    """

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    tokens_per_day: int = 500000
    enable_queue: bool = True
    queue_max_size: int = 10


class GenerationConfig(BaseModel):
    """
    生成配置
    Generation Configuration

    定义响应生成参数。
    Defines response generation parameters.

    Attributes:
        default_temperature: 默认温度 / Default temperature
        default_max_tokens: 默认最大 Token 数 / Default max tokens
        tier3_timeout_seconds: Tier3 超时时间 / Tier3 timeout
        retry_attempts: 重试次数 / Retry attempts
    """

    default_temperature: float = Field(default=0.8, ge=0, le=2)
    default_max_tokens: int = Field(default=150, ge=10)
    tier3_timeout_seconds: int = Field(default=3, ge=1)
    retry_attempts: int = Field(default=2, ge=0)


class EmbeddingConfig(BaseModel):
    """
    Embedding 配置
    Embedding Configuration

    定义向量化服务参数。
    Defines embedding service parameters.

    Attributes:
        provider: 提供商 / Provider
        model: 模型名称 / Model name
        dimension: 向量维度 / Vector dimension
        batch_size: 批处理大小 / Batch size
        enable_local_fallback: 是否启用本地降级 / Enable local fallback
        local_model: 本地模型 / Local model
    """

    provider: str = "openai"
    model: str = "text-embedding-3-small"
    dimension: int = 768
    batch_size: int = 32
    enable_local_fallback: bool = True
    local_model: str = "sentence-transformers/all-MiniLM-L6-v2"


class ResponseCacheConfig(BaseModel):
    """
    响应缓存配置
    Response Cache Configuration

    定义响应缓存参数。
    Defines response cache parameters.

    Attributes:
        enable: 是否启用 / Whether enabled
        max_entries: 最大条目数 / Max entries
        similarity_threshold: 相似度阈值 / Similarity threshold
        ttl_days: 过期天数 / TTL in days
    """

    enable: bool = True
    max_entries: int = 100
    similarity_threshold: float = 0.8
    ttl_days: int = 7


class PromptConfig(BaseModel):
    """
    Prompt 配置
    Prompt Configuration

    定义 Prompt 构建参数。
    Defines prompt building parameters.

    Attributes:
        mode: Prompt 模式 (lite/standard/deep) / Prompt mode
        memory_index_count: 记忆索引数量 / Memory index count
        memory_fulltext_count: 记忆全文数量 / Memory fulltext count
        conversation_history_turns: 对话历史轮数 / Conversation history turns
    """

    mode: str = Field(default="standard", pattern="^(lite|standard|deep)$")
    memory_index_count: int = 30
    memory_fulltext_count: int = 3
    conversation_history_turns: int = 10


class AIConfig(BaseModel):
    """
    AI 模块总配置
    AI Module Master Configuration

    对应 config/api_settings.json 文件。
    Corresponds to config/api_settings.json file.

    Attributes:
        primary_api: 主 API 配置 / Primary API config
        fallback_api: 备用 API 配置 / Fallback API config
        rate_limits: 速率限制配置 / Rate limits config
        generation: 生成配置 / Generation config
        embedding: Embedding 配置 / Embedding config
        response_cache: 响应缓存配置 / Response cache config
        prompt: Prompt 配置 / Prompt config
    """

    primary_api: APIConfig = Field(default_factory=APIConfig)
    fallback_api: FallbackAPIConfig = Field(default_factory=FallbackAPIConfig)
    rate_limits: RateLimitsConfig = Field(default_factory=RateLimitsConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    response_cache: ResponseCacheConfig = Field(default_factory=ResponseCacheConfig)
    prompt: PromptConfig = Field(default_factory=PromptConfig)
