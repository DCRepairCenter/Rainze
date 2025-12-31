"""
情绪状态模块
Emotion State Module

导出情绪状态相关的类和枚举。
Exports emotion state related classes and enums.
"""

from __future__ import annotations

from .state_machine import EmotionStateMachine
from .states import (
    MOOD_SUB_STATE_MAP,
    STATE_PRIORITY,
    EmotionState,
    MoodState,
    MoodSubState,
    get_priority,
    is_sub_state_valid,
)

__all__: list[str] = [
    "MoodState",
    "MoodSubState",
    "EmotionState",
    "MOOD_SUB_STATE_MAP",
    "STATE_PRIORITY",
    "get_priority",
    "is_sub_state_valid",
    "EmotionStateMachine",
]
