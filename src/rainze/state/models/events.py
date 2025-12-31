"""
状态事件模型
State Event Models

定义状态变化相关的事件数据类。
Defines event dataclasses for state changes.

Reference:
    - MOD-State.md §4.1: 状态事件模型
    - PRD §0.6a: 状态变化通知

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from rainze.state.emotion.states import MoodState, MoodSubState


class StateChangeType(Enum):
    """
    状态变化类型
    State change types

    标识不同类型的状态变化事件。
    Identifies different types of state change events.
    """

    MOOD_CHANGED = "mood_changed"  # 情绪变化 / Mood changed
    ENERGY_CHANGED = "energy_changed"  # 能量变化 / Energy changed
    HUNGER_CHANGED = "hunger_changed"  # 饥饿度变化 / Hunger changed
    AFFINITY_CHANGED = "affinity_changed"  # 好感度变化 / Affinity changed
    COINS_CHANGED = "coins_changed"  # 金币变化 / Coins changed
    LEVEL_UP = "level_up"  # 等级提升 / Level up
    POSITION_CHANGED = "position_changed"  # 位置变化 / Position changed


@dataclass
class StateChangedEvent:
    """
    状态变化事件
    State changed event

    通用状态变化事件，包含变化类型、旧值、新值和原因。
    Generic state change event with change type, old/new values and reason.

    Attributes:
        change_type: 变化类型 / Change type
        old_value: 旧值 / Old value
        new_value: 新值 / New value
        reason: 变化原因 / Change reason
        timestamp: 时间戳 / Timestamp
        extra: 额外信息 / Extra information
    """

    change_type: StateChangeType
    old_value: Any
    new_value: Any
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)
    extra: Optional[dict[str, Any]] = None


@dataclass
class MoodTransitionEvent:
    """
    情绪转换事件
    Mood transition event

    记录情绪状态转换的详细信息。
    Records detailed information about mood state transitions.

    Attributes:
        from_state: 原状态 / From state
        to_state: 目标状态 / To state
        from_sub: 原子状态 / From sub-state
        to_sub: 目标子状态 / To sub-state
        trigger: 触发类型 / Trigger type ("rule" | "llm" | "decay" | "recovery")
        reason: 转换原因 / Transition reason
        timestamp: 时间戳 / Timestamp
    """

    from_state: MoodState
    to_state: MoodState
    from_sub: Optional[MoodSubState]
    to_sub: Optional[MoodSubState]
    trigger: str  # "rule" | "llm" | "decay" | "recovery"
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LevelUpEvent:
    """
    等级提升事件
    Level up event

    记录好感度等级提升的详细信息。
    Records detailed information about affinity level up.

    Attributes:
        attribute: 属性名 / Attribute name ("affinity")
        old_level: 旧等级 / Old level
        new_level: 新等级 / New level
        old_value: 旧值 / Old value
        new_value: 新值 / New value
        unlocks: 解锁内容 / Unlocked content
        timestamp: 时间戳 / Timestamp
    """

    attribute: str  # "affinity"
    old_level: int
    new_level: int
    old_value: int
    new_value: int
    unlocks: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EnergyChangedEvent:
    """
    能量变化事件
    Energy changed event

    专门记录能量变化，包含是否触发疲倦状态。
    Specifically records energy changes, including tiredness trigger.

    Attributes:
        old_value: 旧能量值 / Old energy value
        new_value: 新能量值 / New energy value
        delta: 变化量 / Delta
        reason: 变化原因 / Change reason
        triggered_tired: 是否触发疲倦 / Whether triggered tired state
        timestamp: 时间戳 / Timestamp
    """

    old_value: float
    new_value: float
    delta: float
    reason: str
    triggered_tired: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AffinityChangedEvent:
    """
    好感度变化事件
    Affinity changed event

    专门记录好感度变化，包含等级变化检测。
    Specifically records affinity changes, including level change detection.

    Attributes:
        old_value: 旧好感度值 / Old affinity value
        new_value: 新好感度值 / New affinity value
        delta: 变化量 / Delta
        reason: 变化原因 / Change reason
        old_level: 旧等级 / Old level
        new_level: 新等级 / New level
        level_changed: 等级是否变化 / Whether level changed
        timestamp: 时间戳 / Timestamp
    """

    old_value: int
    new_value: int
    delta: int
    reason: str
    old_level: int
    new_level: int
    level_changed: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
