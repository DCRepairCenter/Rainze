"""
交互请求/响应契约
Interaction Request/Response Contract

本模块定义统一的交互请求和响应格式。
This module defines unified interaction request and response formats.

Reference:
    - PRD §0.5a: 统一上下文管理器 (UCM)
    - MOD-Core.md §11.3: InteractionRequest/Response

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from .emotion import EmotionTag


class InteractionSource(Enum):
    """
    交互来源枚举
    Interaction source enumeration

    所有用户交互必须标记来源。
    All user interactions must be labeled with source.
    """

    CHAT_INPUT = auto()  # 用户聊天输入 / User chat input
    PASSIVE_TRIGGER = auto()  # 点击/拖拽 / Click/drag
    SYSTEM_EVENT = auto()  # 系统事件 / System event
    TOOL_RESULT = auto()  # 工具执行结果 / Tool execution result
    PLUGIN_ACTION = auto()  # 插件行为 / Plugin action
    GAME_INTERACTION = auto()  # 游戏交互 / Game interaction
    PROACTIVE = auto()  # 主动行为 / Proactive behavior


@dataclass
class InteractionRequest:
    """
    统一交互请求格式
    Unified interaction request format

    所有交互必须封装为此格式，通过 UCM 处理。
    All interactions MUST be wrapped in this format, processed via UCM.

    Attributes:
        request_id: 唯一请求ID / Unique request ID
        source: 交互来源 / Interaction source
        timestamp: 请求时间 / Request timestamp
        payload: 请求数据 / Request payload
        trace_id: 可观测性追踪ID / Observability trace ID
    """

    request_id: str
    source: InteractionSource
    timestamp: datetime
    payload: Dict[str, Any]
    trace_id: Optional[str] = None

    @classmethod
    def create(
        cls,
        source: InteractionSource,
        payload: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> "InteractionRequest":
        """
        创建交互请求（自动生成 ID 和时间戳）
        Create interaction request (auto-generate ID and timestamp)

        Args:
            source: 交互来源 / Interaction source
            payload: 请求数据 / Request payload
            trace_id: 追踪ID / Trace ID

        Returns:
            新的交互请求 / New interaction request
        """
        import uuid

        return cls(
            request_id=uuid.uuid4().hex,
            source=source,
            timestamp=datetime.now(),
            payload=payload or {},
            trace_id=trace_id,
        )


@dataclass
class InteractionResponse:
    """
    统一交互响应格式
    Unified interaction response format

    Attributes:
        request_id: 对应请求ID / Corresponding request ID
        success: 是否成功 / Whether successful
        response_text: 响应文本 / Response text
        emotion: 情感标签 / Emotion tag
        state_changes: 状态变更记录 / State change records
        trace_spans: 追踪跨度列表 / Trace span list
        error_message: 错误消息（失败时）/ Error message (on failure)
    """

    request_id: str
    success: bool
    response_text: Optional[str] = None
    emotion: Optional["EmotionTag"] = None
    state_changes: Dict[str, Any] = field(default_factory=dict)
    trace_spans: List[str] = field(default_factory=list)
    error_message: Optional[str] = None

    @classmethod
    def success_response(
        cls,
        request_id: str,
        text: str,
        emotion: Optional["EmotionTag"] = None,
        state_changes: Optional[Dict[str, Any]] = None,
    ) -> "InteractionResponse":
        """
        创建成功响应
        Create success response

        Args:
            request_id: 请求ID / Request ID
            text: 响应文本 / Response text
            emotion: 情感标签 / Emotion tag
            state_changes: 状态变更 / State changes

        Returns:
            成功响应 / Success response
        """
        return cls(
            request_id=request_id,
            success=True,
            response_text=text,
            emotion=emotion,
            state_changes=state_changes or {},
        )

    @classmethod
    def error_response(
        cls,
        request_id: str,
        error: str,
    ) -> "InteractionResponse":
        """
        创建错误响应
        Create error response

        Args:
            request_id: 请求ID / Request ID
            error: 错误消息 / Error message

        Returns:
            错误响应 / Error response
        """
        return cls(
            request_id=request_id,
            success=False,
            error_message=error,
        )
