"""
跨模块契约 - 共享类型定义
Cross-Module Contracts - Shared Type Definitions

重要 / IMPORTANT:
所有模块必须从此包导入公共类型，禁止重复定义！
All modules MUST import shared types from this package. NO duplicates!

Exports / 导出:
- EmotionTag: 情感标签 / Emotion tag
- SceneType: 场景类型 / Scene type
- ResponseTier: 响应层级 / Response tier
- InteractionRequest: 交互请求 / Interaction request
- InteractionResponse: 交互响应 / Interaction response
- IRustMemorySearch: Rust 记忆检索接口 / Rust memory search interface
- IRustSystemMonitor: Rust 系统监控接口 / Rust system monitor interface

Reference:
    - PRD §0.15: 跨模块契约
    - MOD-Core.md §11: 跨模块契约类设计

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from .emotion import EmotionTag
from .scene import (
    ResponseTier,
    SceneTierMapping,
    SceneType,
    get_scene_tier_table,
    invalidate_scene_tier_cache,
)
from .interaction import (
    InteractionRequest,
    InteractionResponse,
    InteractionSource,
)
from .ucm import (
    ITierHandler,
    IUnifiedContextManager,
)

# TODO: Rust bridge contracts 待实现
# from .rust_bridge import (
#     IRustMemorySearch,
#     IRustSystemMonitor,
#     IRustTextProcess,
# )

__all__: list[str] = [
    # Emotion contracts / 情感契约
    "EmotionTag",
    # Scene contracts / 场景契约
    "SceneType",
    "ResponseTier",
    "SceneTierMapping",
    "get_scene_tier_table",
    "invalidate_scene_tier_cache",
    # Interaction contracts / 交互契约
    "InteractionSource",
    "InteractionRequest",
    "InteractionResponse",
    # UCM contracts / UCM 契约
    "IUnifiedContextManager",
    "ITierHandler",
    # Rust bridge contracts / Rust 桥接契约 (TODO)
    # "IRustMemorySearch",
    # "IRustSystemMonitor",
    # "IRustTextProcess",
]
