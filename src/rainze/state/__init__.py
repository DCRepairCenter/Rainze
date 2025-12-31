"""
状态管理模块
State Management Module

提供桌宠状态管理功能，包括情绪、能量、好感度等。
Provides pet state management including emotion, energy, affinity, etc.

本模块是 Rainze 的核心模块之一，负责：
- 情绪状态机（5态+子态）
- 数值属性管理（能量、好感度）
- 状态同步与持久化

This module is one of Rainze's core modules, responsible for:
- Emotion state machine (5 states + sub-states)
- Numerical attribute management (energy, affinity)
- State sync and persistence

Reference:
    - PRD §0.6a: 状态管理
    - MOD-State.md: 模块设计文档

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

# 从 attributes 子模块导出 / Export from attributes submodule
from .attributes import (
    AffinityConfig,
    AffinityManager,
    AttributeManager,
    EnergyConfig,
    EnergyManager,
)

# 从 emotion 子模块导出 / Export from emotion submodule
from .emotion import (
    MOOD_SUB_STATE_MAP,
    STATE_PRIORITY,
    EmotionState,
    EmotionStateMachine,
    MoodState,
    MoodSubState,
)

# 从 manager 导出 / Export from manager
from .manager import StateConfig, StateManager, StateSnapshot

# 从 models 子模块导出 / Export from models submodule
from .models import (
    AffinityChangedEvent,
    EnergyChangedEvent,
    LevelUpEvent,
    MoodTransitionEvent,
    StateChangedEvent,
    StateChangeType,
)

__all__: list[str] = [
    # 主管理器 / Main manager
    "StateManager",
    "StateConfig",
    "StateSnapshot",
    # 情绪状态 / Emotion states
    "MoodState",
    "MoodSubState",
    "EmotionState",
    "EmotionStateMachine",
    "MOOD_SUB_STATE_MAP",
    "STATE_PRIORITY",
    # 属性管理 / Attribute management
    "AttributeManager",
    "EnergyConfig",
    "EnergyManager",
    "AffinityConfig",
    "AffinityManager",
    # 事件类型 / Event types
    "StateChangeType",
    "StateChangedEvent",
    "MoodTransitionEvent",
    "LevelUpEvent",
    "EnergyChangedEvent",
    "AffinityChangedEvent",
]
