"""
UCM 接口契约
UCM Interface Contract

本模块定义统一上下文管理器 (UCM) 的接口契约。
This module defines the interface contract for Unified Context Manager.

Reference:
    - PRD §0.5a: 统一上下文管理器 (UCM)
    - MOD-Core.md §13: UCM 接口契约

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from .interaction import InteractionRequest, InteractionResponse


@runtime_checkable
class IUnifiedContextManager(Protocol):
    """
    统一上下文管理器接口契约
    Unified Context Manager Interface Contract

    所有用户交互必须通过此接口处理，确保:
    All user interactions MUST be processed through this interface to ensure:

    - 状态一致性 / State consistency
    - 记忆完整性 / Memory integrity
    - 可观测性追踪 / Observability tracing

    实现者 / Implementor: rainze.agent.context_manager.UnifiedContextManager
    """

    async def process_interaction(
        self,
        request: "InteractionRequest",
    ) -> "InteractionResponse":
        """
        处理交互的统一入口
        Unified entry point for processing interactions

        Args:
            request: 统一交互请求 / Unified interaction request

        Returns:
            统一交互响应 / Unified interaction response
        """
        ...

    async def get_context_summary(self) -> dict[str, object]:
        """
        获取当前上下文摘要（用于调试）
        Get current context summary (for debugging)

        Returns:
            上下文状态字典 / Context state dictionary
        """
        ...


@runtime_checkable
class ITierHandler(Protocol):
    """
    Tier 处理器接口契约
    Tier Handler Interface Contract

    每个 Tier 处理器必须实现此接口。
    Each tier handler must implement this interface.
    """

    @property
    def tier_name(self) -> str:
        """
        获取 Tier 名称
        Get tier name
        """
        ...

    async def handle(
        self,
        request: "InteractionRequest",
        context: dict[str, object],
    ) -> "InteractionResponse":
        """
        处理交互请求
        Handle interaction request

        Args:
            request: 交互请求 / Interaction request
            context: 上下文信息 / Context information

        Returns:
            交互响应 / Interaction response
        """
        ...

    def can_handle(
        self,
        request: "InteractionRequest",
    ) -> bool:
        """
        检查是否能处理此请求
        Check if can handle this request

        Args:
            request: 交互请求 / Interaction request

        Returns:
            是否能处理 / Whether can handle
        """
        ...
