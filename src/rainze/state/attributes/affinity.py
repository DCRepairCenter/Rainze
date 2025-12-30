"""
好感度管理器
Affinity Manager

管理桌宠与用户的好感度，包括等级系统和主动性乘数。
Manages affinity between pet and user, including level system and proactivity.

Reference:
    - MOD-State.md §3.4: AffinityManager
    - PRD §0.6a: 好感度系统

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from .base import AttributeManager


@dataclass
class AffinityConfig:
    """
    好感度配置
    Affinity configuration

    Attributes:
        max_value: 最大好感度 / Maximum affinity
        min_value: 最小好感度（下限保护）/ Minimum affinity (floor protection)
        initial_value: 初始好感度 / Initial affinity
        level_thresholds: 等级阈值列表 / Level thresholds
        level_names: 等级名称列表 / Level names
        proactivity_by_level: 各等级的主动性乘数 / Proactivity multiplier by level
    """

    max_value: int = 999
    min_value: int = 10  # 下限保护 / Floor protection
    initial_value: int = 50
    level_thresholds: list[int] = field(
        default_factory=lambda: [0, 25, 50, 75, 100]
    )
    level_names: list[str] = field(
        default_factory=lambda: ["陌生", "熟悉", "亲密", "挚爱", "羁绊"]
    )
    proactivity_by_level: dict[int, float] = field(
        default_factory=lambda: {1: 0.2, 2: 0.4, 3: 0.6, 4: 0.8, 5: 1.0}
    )


class AffinityManager(AttributeManager[int]):
    """
    好感度管理器
    Affinity Manager

    管理桌宠与用户的好感度（0-999）。
    Manages affinity between pet and user (0-999).

    等级系统 / Level system:
    - Lv.1 (0-24): 陌生 / Stranger
    - Lv.2 (25-49): 熟悉 / Familiar
    - Lv.3 (50-74): 亲密 / Close
    - Lv.4 (75-99): 挚爱 / Beloved
    - Lv.5 (100+): 羁绊 / Bonded

    Reference:
        MOD-State.md §3.4: AffinityManager
    """

    def __init__(
        self,
        config: Optional[AffinityConfig] = None,
        on_change: Optional[Callable[[int, int, str], None]] = None,
        on_level_up: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        """
        初始化好感度管理器
        Initialize affinity manager

        Args:
            config: 好感度配置 / Affinity configuration
            on_change: 变化回调 / Change callback
            on_level_up: 等级提升回调 / Level up callback
        """
        self._config = config or AffinityConfig()
        super().__init__(
            max_value=self._config.max_value,
            min_value=self._config.min_value,
            initial_value=self._config.initial_value,
            on_change=on_change,
        )
        self._on_level_up = on_level_up
        self._current_level = self._calculate_level(self._value)

    @property
    def value(self) -> int:
        """
        获取当前好感度值
        Get current affinity value

        Returns:
            当前好感度 (0-999) / Current affinity
        """
        return self._value

    @property
    def level(self) -> int:
        """
        获取当前等级
        Get current level

        Returns:
            等级 (1-5) / Level
        """
        return self._current_level

    @property
    def level_name(self) -> str:
        """
        获取当前等级名称
        Get current level name

        Returns:
            等级名称 / Level name
        """
        level_names = self._config.level_names
        idx = min(self._current_level - 1, len(level_names) - 1)
        return level_names[max(0, idx)]

    @property
    def proactivity_multiplier(self) -> float:
        """
        获取主动性乘数
        Get proactivity multiplier

        基于好感度等级调整桌宠的主动交互概率。
        Adjusts pet's proactive interaction probability based on level.

        Returns:
            主动性乘数 / Proactivity multiplier
        """
        return self._config.proactivity_by_level.get(self._current_level, 0.5)

    def add(self, amount: int, reason: str) -> int:
        """
        增加好感度
        Add affinity

        Args:
            amount: 增加量 / Amount to add
            reason: 增加原因 / Reason

        Returns:
            增加后的好感度值 / Affinity after adding
        """
        if amount < 0:
            return self.subtract(-amount, reason)

        old_value = self._value
        old_level = self._current_level

        self._value = self._clamp(self._value + amount)
        self._current_level = self._calculate_level(self._value)

        self._notify_change(old_value, self._value, reason)

        # 检查等级提升 / Check level up
        if self._current_level > old_level:
            self._notify_level_up(old_level, self._current_level)

        return self._value

    def subtract(self, amount: int, reason: str) -> int:
        """
        减少好感度
        Subtract affinity

        有下限保护，不会低于 min_value。
        Has floor protection, won't go below min_value.

        Args:
            amount: 减少量 / Amount to subtract
            reason: 减少原因 / Reason

        Returns:
            减少后的好感度值 / Affinity after subtracting
        """
        if amount < 0:
            return self.add(-amount, reason)

        old_value = self._value

        self._value = self._clamp(self._value - amount)
        self._current_level = self._calculate_level(self._value)

        self._notify_change(old_value, self._value, reason)

        # 等级降低不触发特殊事件 / Level down doesn't trigger special event
        return self._value

    def set(self, value: int, reason: str) -> None:
        """
        设置好感度值
        Set affinity value

        Args:
            value: 新好感度值 / New affinity value
            reason: 设置原因 / Reason
        """
        old_value = self._value
        old_level = self._current_level

        self._value = self._clamp(value)
        self._current_level = self._calculate_level(self._value)

        self._notify_change(old_value, self._value, reason)

        if self._current_level > old_level:
            self._notify_level_up(old_level, self._current_level)

    def check_level_up(self) -> Optional[int]:
        """
        检查等级提升
        Check level up

        Returns:
            新等级（如果提升），None 表示未提升 / New level if up, None otherwise
        """
        new_level = self._calculate_level(self._value)
        if new_level > self._current_level:
            self._current_level = new_level
            return new_level
        return None

    def get_progress_to_next_level(self) -> tuple[int, int]:
        """
        获取到下一等级的进度
        Get progress to next level

        Returns:
            (当前进度, 下一等级所需) / (current progress, required for next level)
        """
        thresholds = self._config.level_thresholds
        if self._current_level >= len(thresholds):
            # 已达最高等级 / Already at max level
            return self._value, self._value

        current_threshold = thresholds[self._current_level - 1]
        if self._current_level < len(thresholds):
            next_threshold = thresholds[self._current_level]
        else:
            next_threshold = self._value

        progress = self._value - current_threshold
        required = next_threshold - current_threshold

        return progress, required

    def apply_action_bonus(self, action: str) -> int:
        """
        应用行为加成
        Apply action bonus

        不同行为给予不同好感度加成。
        Different actions give different affinity bonuses.

        Args:
            action: 行为类型 / Action type

        Returns:
            增加后的好感度 / Affinity after bonus
        """
        # 行为加成映射 / Action bonus mapping
        bonus_map: dict[str, int] = {
            "chat": 2,  # 对话 / Chat
            "pet": 3,  # 抚摸 / Pet
            "feed": 5,  # 喂食 / Feed
            "play": 4,  # 玩耍 / Play
            "gift": 10,  # 送礼 / Gift
            "complete_task": 3,  # 完成任务 / Complete task
        }
        bonus = bonus_map.get(action, 1)
        return self.add(bonus, f"action:{action}")

    def get_unlocks_at_level(self, level: int) -> list[str]:
        """
        获取指定等级解锁的内容
        Get unlocks at specified level

        Args:
            level: 等级 / Level

        Returns:
            解锁内容列表 / List of unlocked content
        """
        # 等级解锁映射 / Level unlock mapping
        unlock_map: dict[int, list[str]] = {
            2: ["更多动画表情", "基础互动功能"],
            3: ["私密对话模式", "高级表情包"],
            4: ["特殊动画", "专属称呼"],
            5: ["羁绊特效", "隐藏内容"],
        }
        return unlock_map.get(level, [])

    def to_dict(self) -> dict[str, int | str | float]:
        """
        转换为字典
        Convert to dictionary

        Returns:
            好感度状态字典 / Affinity state dictionary
        """
        progress, required = self.get_progress_to_next_level()
        return {
            "value": self._value,
            "level": self._current_level,
            "level_name": self.level_name,
            "proactivity_multiplier": self.proactivity_multiplier,
            "progress_to_next": progress,
            "required_for_next": required,
        }

    def _calculate_level(self, value: int) -> int:
        """
        计算等级
        Calculate level

        Args:
            value: 好感度值 / Affinity value

        Returns:
            等级 / Level
        """
        thresholds = self._config.level_thresholds
        level = 1
        for i, threshold in enumerate(thresholds):
            if value >= threshold:
                level = i + 1
            else:
                break
        return min(level, len(thresholds))

    def _notify_level_up(self, old_level: int, new_level: int) -> None:
        """
        通知等级提升
        Notify level up

        Args:
            old_level: 旧等级 / Old level
            new_level: 新等级 / New level
        """
        if self._on_level_up is not None:
            self._on_level_up(old_level, new_level)
