"""
能量管理器
Energy Manager

管理桌宠的能量值，包括消耗、恢复和衰减逻辑。
Manages pet's energy value, including consumption, recovery and decay.

Reference:
    - MOD-State.md §3.4: EnergyManager
    - PRD §0.6a: 能量系统

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from .base import AttributeManager


@dataclass
class EnergyConfig:
    """
    能量配置
    Energy configuration

    Attributes:
        max_value: 最大能量值 / Maximum energy
        min_value: 最小能量值 / Minimum energy
        initial_value: 初始能量值 / Initial energy
        decay_per_hour: 每小时衰减量 / Hourly decay
        sleep_recovery_per_hour: 睡眠每小时恢复量 / Sleep recovery per hour
        low_threshold: 低能量阈值 / Low energy threshold
        critical_threshold: 极低能量阈值 / Critical energy threshold
    """

    max_value: float = 100.0
    min_value: float = 0.0
    initial_value: float = 80.0
    decay_per_hour: float = 2.0
    sleep_recovery_per_hour: float = 20.0
    low_threshold: float = 30.0
    critical_threshold: float = 20.0


class EnergyManager(AttributeManager[float]):
    """
    能量管理器
    Energy Manager

    管理桌宠的能量值（0-100）。
    Manages pet's energy value (0-100).

    - 消耗：长时间运行、频繁互动
    - 恢复：睡眠模式、用户关闭应用

    - Consumption: Long running, frequent interactions
    - Recovery: Sleep mode, user closes app

    Reference:
        MOD-State.md §3.4: EnergyManager
    """

    def __init__(
        self,
        config: Optional[EnergyConfig] = None,
        on_change: Optional[Callable[[float, float, str], None]] = None,
    ) -> None:
        """
        初始化能量管理器
        Initialize energy manager

        Args:
            config: 能量配置 / Energy configuration
            on_change: 变化回调 / Change callback
        """
        self._config = config or EnergyConfig()
        super().__init__(
            max_value=self._config.max_value,
            min_value=self._config.min_value,
            initial_value=self._config.initial_value,
            on_change=on_change,
        )
        self._last_decay_time = datetime.now()

    @property
    def value(self) -> float:
        """
        获取当前能量值
        Get current energy value

        Returns:
            当前能量 (0-100) / Current energy
        """
        return self._value

    @property
    def is_low(self) -> bool:
        """
        是否低能量
        Whether low energy

        Returns:
            是否低于低能量阈值 / Whether below low threshold
        """
        return self._value < self._config.low_threshold

    @property
    def is_critical(self) -> bool:
        """
        是否极低能量
        Whether critical low energy

        触发不可覆盖的 Tired 状态。
        Triggers uncoverridable Tired state.

        Returns:
            是否低于极低阈值 / Whether below critical threshold
        """
        return self._value < self._config.critical_threshold

    def add(self, amount: float, reason: str) -> float:
        """
        增加能量
        Add energy

        Args:
            amount: 增加量 / Amount to add
            reason: 增加原因 / Reason

        Returns:
            增加后的能量值 / Energy after adding
        """
        if amount < 0:
            return self.subtract(-amount, reason)

        old_value = self._value
        self._value = self._clamp(self._value + amount)
        self._notify_change(old_value, self._value, reason)
        return self._value

    def subtract(self, amount: float, reason: str) -> float:
        """
        消耗能量
        Consume energy

        Args:
            amount: 消耗量 / Amount to subtract
            reason: 消耗原因 / Reason

        Returns:
            消耗后的能量值 / Energy after subtracting
        """
        if amount < 0:
            return self.add(-amount, reason)

        old_value = self._value
        self._value = self._clamp(self._value - amount)
        self._notify_change(old_value, self._value, reason)
        return self._value

    def set(self, value: float, reason: str) -> None:
        """
        设置能量值
        Set energy value

        Args:
            value: 新能量值 / New energy value
            reason: 设置原因 / Reason
        """
        old_value = self._value
        self._value = self._clamp(value)
        self._notify_change(old_value, self._value, reason)

    def apply_hourly_decay(self) -> float:
        """
        应用每小时衰减
        Apply hourly decay

        基于配置的每小时衰减量减少能量。
        Reduce energy based on configured hourly decay.

        Returns:
            衰减后的能量值 / Energy after decay
        """
        now = datetime.now()
        hours_elapsed = (now - self._last_decay_time).total_seconds() / 3600.0

        if hours_elapsed >= 1.0:
            decay_amount = self._config.decay_per_hour * hours_elapsed
            self._last_decay_time = now
            return self.subtract(decay_amount, "hourly_decay")

        return self._value

    def apply_sleep_recovery(self, hours: float) -> float:
        """
        应用睡眠恢复
        Apply sleep recovery

        Args:
            hours: 睡眠时长（小时）/ Sleep duration in hours

        Returns:
            恢复后的能量值 / Energy after recovery
        """
        recovery_amount = self._config.sleep_recovery_per_hour * hours
        return self.add(recovery_amount, f"sleep_recovery:{hours:.1f}h")

    def apply_interaction_cost(self, interaction_type: str) -> float:
        """
        应用交互消耗
        Apply interaction cost

        不同类型的交互消耗不同能量。
        Different interaction types consume different energy.

        Args:
            interaction_type: 交互类型 / Interaction type

        Returns:
            消耗后的能量值 / Energy after cost
        """
        # 交互消耗映射 / Interaction cost mapping
        cost_map: dict[str, float] = {
            "chat": 1.0,  # 对话 / Chat
            "tool_use": 2.0,  # 工具使用 / Tool use
            "animation": 0.5,  # 动画 / Animation
            "idle": 0.1,  # 闲置 / Idle
        }
        cost = cost_map.get(interaction_type, 1.0)
        return self.subtract(cost, f"interaction:{interaction_type}")

    def get_status(self) -> str:
        """
        获取能量状态描述
        Get energy status description

        Returns:
            状态描述字符串 / Status description string
        """
        if self.is_critical:
            return "exhausted"  # 精疲力竭 / Exhausted
        elif self.is_low:
            return "tired"  # 疲倦 / Tired
        elif self._value >= 80:
            return "energetic"  # 精力充沛 / Energetic
        else:
            return "normal"  # 正常 / Normal

    def to_dict(self) -> dict[str, float]:
        """
        转换为字典
        Convert to dictionary

        Returns:
            能量状态字典 / Energy state dictionary
        """
        return {
            "value": self._value,
            "max": self._max,
            "min": self._min,
            "percentage": self.percentage,
        }
