"""
情绪状态定义
Emotion State Definitions

本模块定义主情绪状态和子情绪状态枚举。
This module defines main mood states and sub-mood state enums.

Reference:
    - PRD §0.6a: 情绪状态定义
    - MOD-State.md §3.2: EmotionStateMachine

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class MoodState(Enum):
    """
    主情绪状态
    Main mood states

    定义桌宠的5种基本情绪状态。
    Defines 5 basic emotional states for the desktop pet.

    Reference:
        PRD §0.6a: 5态情绪系统
    """

    HAPPY = "happy"
    NORMAL = "normal"
    TIRED = "tired"
    SAD = "sad"
    ANXIOUS = "anxious"


class MoodSubState(Enum):
    """
    子情绪状态
    Sub-mood states

    每种主情绪可有对应的子状态，用于更细腻的情感表达。
    Each main mood can have sub-states for more nuanced expression.

    Reference:
        MOD-State.md §3.2: 子状态定义
    """

    # Happy 子状态 / Happy sub-states
    EXCITED = "excited"  # 兴奋 / Excited
    CONTENT = "content"  # 满足 / Content

    # Normal 子状态 / Normal sub-states
    RELAXED = "relaxed"  # 放松 / Relaxed
    FOCUSED = "focused"  # 专注 / Focused

    # Tired 子状态 / Tired sub-states
    SLEEPY = "sleepy"  # 困倦 / Sleepy
    EXHAUSTED = "exhausted"  # 疲惫 / Exhausted

    # Sad 子状态 / Sad sub-states
    DISAPPOINTED = "disappointed"  # 失望 / Disappointed
    LONELY = "lonely"  # 孤独 / Lonely

    # Anxious 子状态 / Anxious sub-states
    WORRIED = "worried"  # 担忧 / Worried
    NERVOUS = "nervous"  # 紧张 / Nervous


# 主状态到子状态的映射 / Main state to sub-states mapping
MOOD_SUB_STATE_MAP: dict[MoodState, list[MoodSubState]] = {
    MoodState.HAPPY: [MoodSubState.EXCITED, MoodSubState.CONTENT],
    MoodState.NORMAL: [MoodSubState.RELAXED, MoodSubState.FOCUSED],
    MoodState.TIRED: [MoodSubState.SLEEPY, MoodSubState.EXHAUSTED],
    MoodState.SAD: [MoodSubState.DISAPPOINTED, MoodSubState.LONELY],
    MoodState.ANXIOUS: [MoodSubState.WORRIED, MoodSubState.NERVOUS],
}


# 状态优先级矩阵 / State priority matrix
# 高优先级状态不可被低优先级覆盖
# Higher priority states cannot be overridden by lower priority
STATE_PRIORITY: dict[str, int] = {
    "Sleeping": 100,  # 睡眠中 / Sleeping
    "Tired_LowEnergy": 90,  # 能量极低 / Very low energy
    "Anxious": 50,  # 焦虑 / Anxious
    "Sad": 40,  # 悲伤 / Sad
    "Tired_Night": 30,  # 夜间疲倦 / Night tiredness
    "Excited": 20,  # 兴奋 / Excited
    "Happy": 10,  # 开心 / Happy
    "Normal": 0,  # 正常（基准态）/ Normal (baseline)
}


@dataclass
class EmotionState:
    """
    情绪状态数据
    Emotion state data

    封装当前情绪的完整信息，包括主状态、子状态、强度和触发原因。
    Encapsulates complete emotion info including main state, sub-state,
    intensity and trigger reason.

    Attributes:
        main_state: 主情绪状态 / Main mood state
        sub_state: 子情绪状态（可选）/ Sub-mood state (optional)
        intensity: 情绪强度 [0.0, 1.0] / Emotion intensity
        entered_at: 进入此状态的时间 / Time when entered this state
        trigger_reason: 触发原因 / Trigger reason
    """

    main_state: MoodState
    sub_state: Optional[MoodSubState]
    intensity: float
    entered_at: datetime
    trigger_reason: str

    def __post_init__(self) -> None:
        """
        验证并修正数据
        Validate and correct data
        """
        # 确保强度在有效范围内 / Ensure intensity is in valid range
        self.intensity = max(0.0, min(1.0, self.intensity))

        # 验证子状态与主状态匹配 / Validate sub-state matches main state
        if self.sub_state is not None:
            valid_sub_states = MOOD_SUB_STATE_MAP.get(self.main_state, [])
            if self.sub_state not in valid_sub_states:
                self.sub_state = None


def get_priority(state: MoodState, energy: float = 100.0, hour: int = 12) -> int:
    """
    获取状态优先级
    Get state priority

    根据当前状态和上下文计算优先级值。
    Calculate priority value based on current state and context.

    Args:
        state: 情绪状态 / Mood state
        energy: 当前能量值 / Current energy value
        hour: 当前小时 / Current hour

    Returns:
        优先级值，越高越不可覆盖 / Priority value, higher = less overridable
    """
    # 检查特殊条件 / Check special conditions
    if state == MoodState.TIRED:
        if energy < 20:
            return STATE_PRIORITY["Tired_LowEnergy"]
        if hour >= 23 or hour < 6:
            return STATE_PRIORITY["Tired_Night"]
        return STATE_PRIORITY.get(state.value.capitalize(), 0)

    # 标准优先级查找 / Standard priority lookup
    return STATE_PRIORITY.get(state.value.capitalize(), 0)


def is_sub_state_valid(main: MoodState, sub: MoodSubState) -> bool:
    """
    验证子状态是否与主状态匹配
    Validate if sub-state matches main state

    Args:
        main: 主情绪状态 / Main mood state
        sub: 子情绪状态 / Sub-mood state

    Returns:
        是否匹配 / Whether they match
    """
    valid_subs = MOOD_SUB_STATE_MAP.get(main, [])
    return sub in valid_subs
