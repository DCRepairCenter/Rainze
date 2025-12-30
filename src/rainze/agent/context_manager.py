"""
统一上下文管理器 (UCM)
Unified Context Manager

本模块是 Rainze 所有用户交互的**唯一入口点**。
This module is the **single entry point** for all user interactions in Rainze.

核心职责 / Core Responsibilities:
- 统一入口: 所有交互（对话、游戏、工具、插件、系统事件）必须通过此模块
  Unified entry: All interactions must go through this module
- 状态一致性: 确保任何模块的状态变化都实时同步
  State consistency: Ensure state changes sync in real-time
- 记忆完整性: 游戏/插件/工具产生的交互同样写入记忆
  Memory integrity: Game/plugin/tool interactions are also written to memory
- 可观测性: 每个交互自动生成 trace_id 并记录 span
  Observability: Auto-generate trace_id and record spans

⚠️ 禁止其他模块绕过 UCM 直接处理用户交互！
DO NOT bypass UCM to handle user interactions directly!

Reference:
    - PRD §0.5a: 统一上下文管理器 (UCM)
    - MOD-Agent.md §3.1: UnifiedContextManager

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, Optional

# ⭐ 从 core.contracts 导入共享类型，禁止重复定义
# Import shared types from core.contracts, NO duplicates allowed
from rainze.core.contracts import (
    InteractionRequest,
    InteractionResponse,
    InteractionSource,
    ResponseTier,
    SceneTierMapping,
    SceneType,
)
from rainze.core.exceptions import RainzeError

from .scene_classifier import ClassificationResult, SceneClassifier
from .tier_handlers import TierHandlerRegistry, TierResponse

if TYPE_CHECKING:
    pass


# ========================================
# 异常定义 / Exception Definitions
# ========================================


class UCMError(RainzeError):
    """
    UCM 相关错误
    UCM related error

    当 UCM 处理交互失败时抛出。
    Raised when UCM fails to process interaction.
    """

    def __init__(self, message: str, request_id: Optional[str] = None) -> None:
        """
        初始化 UCM 错误
        Initialize UCM error

        Args:
            message: 错误消息 / Error message
            request_id: 关联的请求 ID / Associated request ID
        """
        code = "UCM_ERROR"
        if request_id:
            message = f"[{request_id}] {message}"
        super().__init__(message, code)
        self.request_id = request_id


class ClassificationError(UCMError):
    """
    场景分类错误
    Scene classification error
    """

    def __init__(self, message: str, request_id: Optional[str] = None) -> None:
        super().__init__(f"Classification failed: {message}", request_id)


class HandlerError(UCMError):
    """
    处理器执行错误
    Handler execution error
    """

    def __init__(
        self,
        message: str,
        tier: Optional[ResponseTier] = None,
        request_id: Optional[str] = None,
    ) -> None:
        tier_info = f" (Tier: {tier.name})" if tier else ""
        super().__init__(f"Handler failed{tier_info}: {message}", request_id)
        self.tier = tier


# ========================================
# 数据类定义 / Data Class Definitions
# ========================================


class MemoryWritePolicy(Enum):
    """
    记忆写入策略
    Memory write policy
    """

    FULL = auto()  # 完整记录 / Full record
    SUMMARY = auto()  # 摘要记录 / Summary record
    RESULT_ONLY = auto()  # 仅结果 / Result only
    NONE = auto()  # 不记录 / No record


@dataclass
class MemoryWriteConfig:
    """
    记忆写入配置
    Memory write configuration

    Attributes:
        policy: 写入策略 / Write policy
        default_importance: 默认重要度 [0, 1] / Default importance
        aggregate_enabled: 是否启用聚合 / Whether aggregation is enabled
        aggregate_template: 聚合模板 / Aggregation template
    """

    policy: MemoryWritePolicy
    default_importance: float
    aggregate_enabled: bool = False
    aggregate_template: Optional[str] = None


@dataclass
class InteractionContext:
    """
    交互上下文数据类
    Interaction context data class

    在 UCM 处理过程中使用的内部上下文。
    Internal context used during UCM processing.

    Attributes:
        interaction_id: 交互 ID / Interaction ID
        source: 交互来源 / Interaction source
        timestamp: 时间戳 / Timestamp
        trace_id: 追踪 ID / Trace ID
        user_input: 用户输入 / User input
        payload: 原始负载数据 / Original payload
        metadata: 元数据 / Metadata
        classification: 分类结果（处理后填充）/ Classification result (filled after processing)
        tier_response: 层级响应（处理后填充）/ Tier response (filled after processing)
    """

    interaction_id: str
    source: InteractionSource
    timestamp: datetime
    trace_id: str
    user_input: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 处理过程中填充 / Filled during processing
    classification: Optional[ClassificationResult] = None
    tier_response: Optional[TierResponse] = None


@dataclass
class ClassifiedScene:
    """
    已分类场景（对外暴露的简化版本）
    Classified scene (simplified version exposed externally)

    Attributes:
        scene_id: 场景 ID / Scene ID
        scene_type: 场景类型 / Scene type
        suggested_tier: 建议的响应层级 / Suggested response tier
        mapping: 完整配置 / Full configuration
    """

    scene_id: str
    scene_type: SceneType
    suggested_tier: ResponseTier
    mapping: SceneTierMapping


# 各交互类型的默认记忆写入策略
# Default memory write policies for each interaction type
DEFAULT_MEMORY_POLICIES: Dict[InteractionSource, MemoryWriteConfig] = {
    InteractionSource.CHAT_INPUT: MemoryWriteConfig(
        policy=MemoryWritePolicy.FULL,
        default_importance=0.6,
    ),
    InteractionSource.GAME_INTERACTION: MemoryWriteConfig(
        policy=MemoryWritePolicy.RESULT_ONLY,
        default_importance=0.3,
        aggregate_enabled=True,
        aggregate_template="今天和主人玩了{count}局{game_name}，赢了{win_count}局",
    ),
    InteractionSource.TOOL_RESULT: MemoryWriteConfig(
        policy=MemoryWritePolicy.SUMMARY,
        default_importance=0.5,
    ),
    InteractionSource.PLUGIN_ACTION: MemoryWriteConfig(
        policy=MemoryWritePolicy.SUMMARY,
        default_importance=0.4,
    ),
    InteractionSource.SYSTEM_EVENT: MemoryWriteConfig(
        policy=MemoryWritePolicy.SUMMARY,
        default_importance=0.5,
    ),
    InteractionSource.PASSIVE_TRIGGER: MemoryWriteConfig(
        policy=MemoryWritePolicy.NONE,
        default_importance=0.0,
    ),
    InteractionSource.PROACTIVE: MemoryWriteConfig(
        policy=MemoryWritePolicy.SUMMARY,
        default_importance=0.4,
    ),
}


# ========================================
# 主类 / Main Class
# ========================================


class UnifiedContextManager:
    """
    统一上下文管理器 (UCM)
    Unified Context Manager

    ⭐ 核心设计: 所有用户交互的**唯一入口点**
    Core design: The **single entry point** for all user interactions

    确保 / Ensures:
    - 状态一致性：任何模块的状态变化都实时同步
      State consistency: Any module's state changes sync in real-time
    - 记忆完整性：游戏/插件/工具产生的交互同样写入记忆
      Memory integrity: Game/plugin/tool interactions are also written to memory
    - 上下文共享：所有模块共享同一套用户画像和情绪状态
      Context sharing: All modules share same user profile and emotion state
    - 可观测性：每个交互自动生成 trace_id 并记录 span
      Observability: Auto-generate trace_id and record spans

    ⚠️ 禁止其他模块绕过 UCM 直接处理用户交互！
    DO NOT bypass UCM to handle user interactions directly!

    Attributes:
        _scene_classifier: 场景分类器 / Scene classifier
        _tier_handlers: 层级处理器注册表 / Tier handler registry
        _memory_policies: 记忆写入策略配置 / Memory write policy config
        _custom_handlers: 自定义交互处理器 / Custom interaction handlers
    """

    def __init__(
        self,
        scene_classifier: Optional[SceneClassifier] = None,
        tier_handlers: Optional[TierHandlerRegistry] = None,
    ) -> None:
        """
        初始化统一上下文管理器
        Initialize Unified Context Manager

        Args:
            scene_classifier: 场景分类器，默认创建新实例
                              Scene classifier, creates new instance by default
            tier_handlers: 层级处理器注册表，默认创建新实例
                           Tier handler registry, creates new instance by default
        """
        # 场景分类器 / Scene classifier
        self._scene_classifier = scene_classifier or SceneClassifier()

        # 层级处理器注册表 / Tier handler registry
        self._tier_handlers = tier_handlers or TierHandlerRegistry()

        # 记忆写入策略 / Memory write policies
        self._memory_policies: Dict[InteractionSource, MemoryWriteConfig] = (
            DEFAULT_MEMORY_POLICIES.copy()
        )

        # 自定义处理器映射（source -> handler）
        # Custom handler mapping (source -> handler)
        self._custom_handlers: Dict[
            InteractionSource,
            Callable[[InteractionContext], Awaitable[TierResponse]],
        ] = {}

        # 交互计数（用于统计）/ Interaction count (for statistics)
        self._interaction_count: int = 0

    async def process_interaction(
        self,
        request: InteractionRequest,
    ) -> InteractionResponse:
        """
        处理交互的统一入口
        Unified entry point for processing interactions

        ⭐ 所有类型的交互（对话、游戏、工具、插件、系统事件）
        都必须通过此方法处理，确保状态和记忆的一致性。

        All types of interactions must be processed through this method
        to ensure state and memory consistency.

        处理流程 / Processing flow:
        1. 创建内部上下文 / Create internal context
        2. 场景分类 / Scene classification
        3. 检索记忆（如需要）/ Retrieve memory (if needed)
        4. 路由到处理器 / Route to handler
        5. 后处理（状态更新、记忆写入）/ Post-process (state update, memory write)
        6. 返回响应 / Return response

        Args:
            request: 统一交互请求 / Unified interaction request

        Returns:
            InteractionResponse: 统一响应格式 / Unified response format

        Raises:
            UCMError: 交互处理失败时抛出 / Raised when processing fails

        Example:
            >>> request = InteractionRequest.create(
            ...     source=InteractionSource.CHAT_INPUT,
            ...     payload={"text": "今天天气怎么样？"}
            ... )
            >>> response = await ucm.process_interaction(request)
            >>> print(response.response_text)
        """
        # 更新计数 / Update count
        self._interaction_count += 1

        # 1. 创建内部上下文 / Create internal context
        context = self._create_context(request)

        # TODO: 实现可观测性后取消注释
        # Uncomment after observability is implemented
        # with Tracer.span("ucm.process", {"source": request.source.name}) as span:

        try:
            # 2. 场景分类 / Scene classification
            classification = await self._classify_scene(context)
            context.classification = classification
            # span.log("classified", {"scene": classification.scene_id})

            # 3. 检索记忆（如需要）/ Retrieve memory (if needed)
            memory_context = await self._retrieve_memory(context, classification)

            # 4. 路由到处理器 / Route to handler
            tier_response = await self._route_to_handler(
                context, classification, memory_context
            )
            context.tier_response = tier_response

            # 5. 后处理 / Post-process
            await self._post_process(context, tier_response)

            # 6. 构建并返回响应 / Build and return response
            return self._build_response(request, tier_response)

        except Exception as e:
            # 处理异常 / Handle exception
            return InteractionResponse.error_response(
                request_id=request.request_id,
                error=str(e),
            )

    async def get_context_summary(self) -> Dict[str, Any]:
        """
        获取上下文摘要
        Get context summary

        返回当前 UCM 的状态摘要，用于调试和监控。
        Return current UCM state summary for debugging and monitoring.

        Returns:
            Dict containing:
            - interaction_count: 已处理的交互数量
              Number of processed interactions
            - tier_handlers: 注册的层级处理器
              Registered tier handlers
            - memory_policies: 记忆写入策略
              Memory write policies
        """
        return {
            "interaction_count": self._interaction_count,
            "tier_handlers": [
                tier.name for tier in self._tier_handlers._handlers.keys()
            ],
            "memory_policies": {
                source.name: config.policy.name
                for source, config in self._memory_policies.items()
            },
            "custom_handlers": [source.name for source in self._custom_handlers.keys()],
        }

    # ========================================
    # 内部方法 / Internal Methods
    # ========================================

    def _create_context(self, request: InteractionRequest) -> InteractionContext:
        """
        创建内部上下文
        Create internal context

        Args:
            request: 交互请求 / Interaction request

        Returns:
            InteractionContext: 内部上下文 / Internal context
        """
        # 提取用户输入 / Extract user input
        user_input = request.payload.get("text") or request.payload.get("input")

        # 生成或使用已有的 trace_id / Generate or use existing trace_id
        trace_id = request.trace_id or uuid.uuid4().hex[:16]

        return InteractionContext(
            interaction_id=request.request_id,
            source=request.source,
            timestamp=request.timestamp,
            trace_id=trace_id,
            user_input=user_input,
            payload=request.payload,
        )

    async def _classify_scene(
        self,
        context: InteractionContext,
    ) -> ClassificationResult:
        """
        分类场景
        Classify scene

        Args:
            context: 内部上下文 / Internal context

        Returns:
            ClassificationResult: 分类结果 / Classification result
        """
        # 从 payload 提取事件类型 / Extract event type from payload
        event_type = context.payload.get("event_type")

        return self._scene_classifier.classify(
            source=context.source,
            event_type=event_type,
            user_input=context.user_input,
            context=context.payload,
        )

    async def _retrieve_memory(
        self,
        context: InteractionContext,
        classification: ClassificationResult,
    ) -> Dict[str, Any]:
        """
        检索记忆上下文
        Retrieve memory context

        根据场景配置决定是否检索记忆，以及检索策略。
        Decide whether and how to retrieve memory based on scene config.

        Args:
            context: 内部上下文 / Internal context
            classification: 分类结果 / Classification result

        Returns:
            记忆上下文数据 / Memory context data
        """
        memory_retrieval = classification.mapping.memory_retrieval

        if memory_retrieval == "none":
            return {}

        # TODO: 实现记忆检索后取消注释
        # Uncomment after memory retrieval is implemented
        #
        # if memory_retrieval == "facts_summary":
        #     return await self._memory_manager.get_facts_summary()
        # elif memory_retrieval == "full":
        #     return await self._memory_manager.get_full_context(
        #         query=context.user_input
        #     )

        return {}

    async def _route_to_handler(
        self,
        context: InteractionContext,
        classification: ClassificationResult,
        memory_context: Dict[str, Any],
    ) -> TierResponse:
        """
        路由到处理器
        Route to handler

        优先检查自定义处理器，然后使用层级处理器。
        Check custom handlers first, then use tier handlers.

        Args:
            context: 内部上下文 / Internal context
            classification: 分类结果 / Classification result
            memory_context: 记忆上下文 / Memory context

        Returns:
            TierResponse: 处理器响应 / Handler response
        """
        # 检查自定义处理器 / Check custom handler
        if context.source in self._custom_handlers:
            handler = self._custom_handlers[context.source]
            return await handler(context)

        # 构建处理器上下文 / Build handler context
        handler_context = {
            "memory_context": memory_context,
            "trace_id": context.trace_id,
            **context.payload,
        }

        # 创建临时请求对象 / Create temporary request object
        request = InteractionRequest(
            request_id=context.interaction_id,
            source=context.source,
            timestamp=context.timestamp,
            payload=context.payload,
            trace_id=context.trace_id,
        )

        # 使用层级处理器（带降级链）/ Use tier handler (with fallback chain)
        return await self._tier_handlers.handle_with_fallback(
            request=request,
            classification=classification,
            context=handler_context,
        )

    async def _post_process(
        self,
        context: InteractionContext,
        response: TierResponse,
    ) -> None:
        """
        后处理：记忆写入、状态更新、事件广播
        Post-process: memory write, state update, event broadcast

        Args:
            context: 内部上下文 / Internal context
            response: 处理器响应 / Handler response
        """
        # 获取记忆写入策略 / Get memory write policy
        policy_config = self._memory_policies.get(context.source)

        if policy_config and policy_config.policy != MemoryWritePolicy.NONE:
            # TODO: 实现记忆写入后取消注释
            # Uncomment after memory write is implemented
            #
            # await self._write_memory(context, response, policy_config)
            pass

        # TODO: 实现状态更新后取消注释
        # Uncomment after state update is implemented
        #
        # if response.emotion:
        #     await self._state_manager.update_emotion(response.emotion)

        # TODO: 实现事件广播后取消注释
        # Uncomment after event broadcast is implemented
        #
        # await self._event_bus.publish("interaction.completed", {
        #     "interaction_id": context.interaction_id,
        #     "source": context.source.name,
        #     "success": response.success,
        # })

    def _build_response(
        self,
        request: InteractionRequest,
        tier_response: TierResponse,
    ) -> InteractionResponse:
        """
        构建统一响应
        Build unified response

        Args:
            request: 原始请求 / Original request
            tier_response: 层级处理器响应 / Tier handler response

        Returns:
            InteractionResponse: 统一响应 / Unified response
        """
        if tier_response.success:
            return InteractionResponse.success_response(
                request_id=request.request_id,
                text=tier_response.text or "",
                emotion=tier_response.emotion,
                state_changes={
                    "tier_used": tier_response.tier_used.name
                    if tier_response.tier_used
                    else None,
                    "latency_ms": tier_response.latency_ms,
                    "fallback_used": tier_response.fallback_used,
                },
            )
        else:
            return InteractionResponse.error_response(
                request_id=request.request_id,
                error=tier_response.text or "Unknown error",
            )

    # ========================================
    # 公共配置方法 / Public Configuration Methods
    # ========================================

    def register_custom_handler(
        self,
        source: InteractionSource,
        handler: Callable[[InteractionContext], Awaitable[TierResponse]],
    ) -> None:
        """
        注册自定义交互处理器
        Register custom interaction handler

        用于特殊交互类型需要自定义处理逻辑的场景。
        For special interaction types that need custom processing logic.

        Args:
            source: 交互来源 / Interaction source
            handler: 异步处理函数 / Async handler function
        """
        self._custom_handlers[source] = handler

    def update_memory_policy(
        self,
        source: InteractionSource,
        config: MemoryWriteConfig,
    ) -> None:
        """
        更新记忆写入策略
        Update memory write policy

        Args:
            source: 交互来源 / Interaction source
            config: 新的配置 / New configuration
        """
        self._memory_policies[source] = config

    def get_scene_classifier(self) -> SceneClassifier:
        """
        获取场景分类器
        Get scene classifier

        Returns:
            场景分类器实例 / Scene classifier instance
        """
        return self._scene_classifier

    def get_tier_handlers(self) -> TierHandlerRegistry:
        """
        获取层级处理器注册表
        Get tier handler registry

        Returns:
            层级处理器注册表 / Tier handler registry
        """
        return self._tier_handlers
