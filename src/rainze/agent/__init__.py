"""
Agent 模块 - 统一上下文管理与 Agent 自主循环
Agent Module - Unified Context Management and Agent Loop

本模块是 Rainze 的"大脑"，负责：
This module is Rainze's "brain", responsible for:

- 统一上下文管理 (UCM): 所有交互的单一入口
  Unified Context Management: Single entry point for all interactions
- 场景分类与路由: 判断交互类型并路由到正确处理器
  Scene classification and routing: Determine interaction type and route to handlers
- 响应层级处理: Tier1/2/3 分层响应策略
  Response tier handling: Tier1/2/3 layered response strategy

Usage / 使用方式:
    from rainze.agent import UnifiedContextManager, SceneClassifier
    from rainze.core.contracts import InteractionRequest, InteractionSource

    # 创建 UCM 实例 / Create UCM instance
    ucm = UnifiedContextManager(scene_classifier, tier_handlers)

    # 处理交互 / Process interaction
    request = InteractionRequest.create(
        source=InteractionSource.CHAT_INPUT,
        payload={"text": "你好呀"}
    )
    response = await ucm.process_interaction(request)

Reference:
    - PRD §0.5a: 统一上下文管理器 (UCM)
    - MOD-Agent.md: Agent 模块设计

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from .context_manager import (
    ClassifiedScene,
    InteractionContext,
    UnifiedContextManager,
)
from .scene_classifier import SceneClassifier
from .tier_handlers import (
    BaseTierHandler,
    Tier1TemplateHandler,
    Tier2RuleHandler,
    Tier3LLMHandler,
    TierHandlerRegistry,
)

__all__: list[str] = [
    # Context Manager / 上下文管理器
    "UnifiedContextManager",
    "InteractionContext",
    "ClassifiedScene",
    # Scene Classification / 场景分类
    "SceneClassifier",
    # Tier Handlers / 层级处理器
    "BaseTierHandler",
    "Tier1TemplateHandler",
    "Tier2RuleHandler",
    "Tier3LLMHandler",
    "TierHandlerRegistry",
]
