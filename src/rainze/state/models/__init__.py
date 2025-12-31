"""
状态数据模型
State Data Models

导出状态事件相关的数据类。
Exports state event related dataclasses.
"""

from __future__ import annotations

from .events import (
    AffinityChangedEvent,
    EnergyChangedEvent,
    LevelUpEvent,
    MoodTransitionEvent,
    StateChangedEvent,
    StateChangeType,
)

__all__: list[str] = [
    "StateChangeType",
    "StateChangedEvent",
    "MoodTransitionEvent",
    "LevelUpEvent",
    "EnergyChangedEvent",
    "AffinityChangedEvent",
]
