"""
Anthropic Claude API 客户端
Anthropic Claude API Client

本模块实现 Anthropic Claude API 的调用。
This module implements Anthropic Claude API calls.

Reference:
    - PRD §0.3: 混合响应策略
    - MOD-AI.md §3.3: LLMClient
    - https://docs.anthropic.com/claude/reference/messages_post

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import time
from collections.abc import AsyncGenerator
from typing import Any, Dict, Optional

import httpx

from rainze.ai.exceptions import (
    LLMAPIError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from rainze.ai.llm.client import (
    LLMClient,
    LLMProvider,
    LLMRequest,
    LLMResponse,
)

# Anthropic API 常量 / Anthropic API Constants
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_API_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-4-20250514"


class AnthropicClient(LLMClient):
    """
    Anthropic Claude API 客户端
    Anthropic Claude API Client

    使用 httpx 实现异步 HTTP 请求。
    Implements async HTTP requests using httpx.

    Attributes:
        _api_key: API 密钥 / API key
        _base_url: API 基础 URL / API base URL
        _default_model: 默认模型 / Default model
        _timeout: 默认超时时间 / Default timeout
        _client: httpx 异步客户端 / httpx async client
    """

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        default_model: str = DEFAULT_MODEL,
        timeout_seconds: int = 30,
    ) -> None:
        """
        初始化 Anthropic 客户端
        Initialize Anthropic client

        Args:
            api_key: Anthropic API 密钥 / Anthropic API key
            base_url: 自定义 API 地址 / Custom API URL
            default_model: 默认模型名称 / Default model name
            timeout_seconds: 默认超时时间（秒）/ Default timeout in seconds
        """
        self._api_key = api_key
        self._base_url = base_url or ANTHROPIC_API_URL
        self._default_model = default_model
        self._timeout = timeout_seconds
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def provider(self) -> LLMProvider:
        """
        获取提供商类型
        Get provider type
        """
        return LLMProvider.ANTHROPIC

    @property
    def is_available(self) -> bool:
        """
        检查客户端是否可用
        Check if client is available
        """
        return bool(self._api_key)

    async def _get_client(self) -> httpx.AsyncClient:
        """
        获取或创建 HTTP 客户端
        Get or create HTTP client

        Returns:
            httpx 异步客户端 / httpx async client
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": ANTHROPIC_API_VERSION,
                    "content-type": "application/json",
                },
            )
        return self._client

    def _build_request_body(self, request: LLMRequest) -> Dict[str, Any]:
        """
        构建请求体
        Build request body

        Args:
            request: LLM 请求 / LLM request

        Returns:
            API 请求体字典 / API request body dict
        """
        # 使用请求中的模型或默认模型 / Use model from request or default
        model = request.model or self._default_model

        body: Dict[str, Any] = {
            "model": model,
            "max_tokens": request.max_tokens,
            "messages": request.messages,
        }

        # 添加系统提示词 / Add system prompt
        if request.system:
            body["system"] = request.system

        # 添加温度 / Add temperature
        if request.temperature != 1.0:
            body["temperature"] = request.temperature

        # 添加停止序列 / Add stop sequences
        if request.stop_sequences:
            body["stop_sequences"] = request.stop_sequences

        return body

    def _parse_response(
        self,
        response_data: Dict[str, Any],
        latency_ms: float,
    ) -> LLMResponse:
        """
        解析 API 响应
        Parse API response

        Args:
            response_data: API 响应数据 / API response data
            latency_ms: 请求延迟 / Request latency

        Returns:
            LLM 响应对象 / LLM response object
        """
        # 提取内容 / Extract content
        content_blocks = response_data.get("content", [])
        content = ""
        for block in content_blocks:
            if block.get("type") == "text":
                content += block.get("text", "")

        # 提取 usage / Extract usage
        usage_data = response_data.get("usage", {})
        usage = {
            "input_tokens": usage_data.get("input_tokens", 0),
            "output_tokens": usage_data.get("output_tokens", 0),
        }

        return LLMResponse(
            content=content,
            model=response_data.get("model", ""),
            usage=usage,
            finish_reason=response_data.get("stop_reason", "stop"),
            latency_ms=latency_ms,
        )

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
        client = await self._get_client()
        body = self._build_request_body(request)

        start_time = time.perf_counter()

        try:
            # 设置请求特定的超时 / Set request-specific timeout
            timeout = httpx.Timeout(request.timeout_seconds)

            response = await client.post(
                self._base_url,
                json=body,
                timeout=timeout,
            )

            latency_ms = (time.perf_counter() - start_time) * 1000

            # 处理错误响应 / Handle error responses
            if response.status_code == 429:
                # 速率限制 / Rate limit
                retry_after = response.headers.get("retry-after")
                raise LLMRateLimitError(
                    "Rate limit exceeded / 超过速率限制",
                    retry_after=float(retry_after) if retry_after else None,
                )

            if response.status_code >= 400:
                # 其他错误 / Other errors
                error_data = response.json() if response.content else {}
                error_message = error_data.get("error", {}).get(
                    "message", "Unknown error"
                )
                raise LLMAPIError(
                    f"API error: {error_message} / API 错误: {error_message}",
                    status_code=response.status_code,
                    provider="anthropic",
                )

            # 解析成功响应 / Parse successful response
            response_data = response.json()
            return self._parse_response(response_data, latency_ms)

        except httpx.TimeoutException as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            raise LLMTimeoutError(
                f"Request timed out after {request.timeout_seconds}s / "
                f"请求在 {request.timeout_seconds} 秒后超时",
                timeout_seconds=request.timeout_seconds,
            ) from e

        except httpx.HTTPStatusError as e:
            raise LLMAPIError(
                f"HTTP error: {e} / HTTP 错误: {e}",
                status_code=e.response.status_code if e.response else 0,
                provider="anthropic",
            ) from e

        except (LLMTimeoutError, LLMRateLimitError, LLMAPIError):
            # 重新抛出我们自己的异常 / Re-raise our own exceptions
            raise

        except Exception as e:
            raise LLMAPIError(
                f"Unexpected error: {e} / 意外错误: {e}",
                status_code=0,
                provider="anthropic",
            ) from e

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
        client = await self._get_client()
        body = self._build_request_body(request)
        body["stream"] = True

        try:
            timeout = httpx.Timeout(request.timeout_seconds)

            async with client.stream(
                "POST",
                self._base_url,
                json=body,
                timeout=timeout,
            ) as response:
                # 检查状态码 / Check status code
                if response.status_code == 429:
                    retry_after = response.headers.get("retry-after")
                    raise LLMRateLimitError(
                        "Rate limit exceeded / 超过速率限制",
                        retry_after=float(retry_after) if retry_after else None,
                    )

                if response.status_code >= 400:
                    # 读取错误响应 / Read error response
                    await response.aread()
                    error_data = response.json() if response.content else {}
                    error_message = error_data.get("error", {}).get(
                        "message", "Unknown error"
                    )
                    raise LLMAPIError(
                        f"API error: {error_message} / API 错误: {error_message}",
                        status_code=response.status_code,
                        provider="anthropic",
                    )

                # 解析 SSE 流 / Parse SSE stream
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    data_str = line[6:]  # 移除 "data: " 前缀 / Remove "data: " prefix
                    if data_str == "[DONE]":
                        break

                    try:
                        import json

                        data = json.loads(data_str)
                        event_type = data.get("type", "")

                        # 提取文本增量 / Extract text delta
                        if event_type == "content_block_delta":
                            delta = data.get("delta", {})
                            if delta.get("type") == "text_delta":
                                text = delta.get("text", "")
                                if text:
                                    yield text

                    except (ValueError, KeyError):
                        # 忽略解析错误 / Ignore parse errors
                        continue

        except httpx.TimeoutException as e:
            raise LLMTimeoutError(
                f"Stream timed out after {request.timeout_seconds}s / "
                f"流在 {request.timeout_seconds} 秒后超时",
                timeout_seconds=request.timeout_seconds,
            ) from e

        except (LLMTimeoutError, LLMRateLimitError, LLMAPIError):
            raise

        except Exception as e:
            raise LLMAPIError(
                f"Stream error: {e} / 流错误: {e}",
                status_code=0,
                provider="anthropic",
            ) from e

    async def close(self) -> None:
        """
        关闭客户端连接
        Close client connection
        """
        if self._client is not None:
            await self._client.aclose()
            self._client = None
