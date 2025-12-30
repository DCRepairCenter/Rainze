"""
属性管理器基类
Attribute Manager Base Class

定义属性管理器的抽象基类和通用接口。
Defines abstract base class and common interface for attribute managers.

Reference:
    - MOD-State.md §3.4: 属性管理器
    - PRD §0.6a: 数值状态管理

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Generic, Optional, TypeVar

# 值类型泛型 / Value type generic
T = TypeVar("T", float, int)


@dataclass
class AttributeConfig:
    """
    属性配置基类
    Attribute configuration base class

    Attributes:
        max_value: 最大值 / Maximum value
        min_value: 最小值 / Minimum value
        initial_value: 初始值 / Initial value
    """

    max_value: float
    min_value: float
    initial_value: float


class AttributeManager(ABC, Generic[T]):
    """
    属性管理器抽象基类
    Attribute Manager Abstract Base Class

    定义数值属性（能量、饥饿度、好感度等）的通用管理接口。
    Defines common management interface for numerical attributes
    (energy, hunger, affinity, etc.)

    Reference:
        MOD-State.md §3.4: AttributeManager 接口定义
    """

    def __init__(
        self,
        max_value: T,
        min_value: T,
        initial_value: T,
        on_change: Optional[Callable[[T, T, str], None]] = None,
    ) -> None:
        """
        初始化属性管理器
        Initialize attribute manager

        Args:
            max_value: 最大值 / Maximum value
            min_value: 最小值 / Minimum value
            initial_value: 初始值 / Initial value
            on_change: 变化回调 (old, new, reason) / Change callback
        """
        self._max: T = max_value
        self._min: T = min_value
        self._value: T = self._clamp(initial_value)
        self._on_change: Optional[Callable[[T, T, str], None]] = on_change

    @property
    @abstractmethod
    def value(self) -> T:
        """
        获取当前值
        Get current value

        Returns:
            当前属性值 / Current attribute value
        """
        ...

    @abstractmethod
    def add(self, amount: T, reason: str) -> T:
        """
        增加值
        Add value

        Args:
            amount: 增加量 / Amount to add
            reason: 增加原因 / Reason for adding

        Returns:
            增加后的值 / Value after adding
        """
        ...

    @abstractmethod
    def subtract(self, amount: T, reason: str) -> T:
        """
        减少值
        Subtract value

        Args:
            amount: 减少量 / Amount to subtract
            reason: 减少原因 / Reason for subtracting

        Returns:
            减少后的值 / Value after subtracting
        """
        ...

    @abstractmethod
    def set(self, value: T, reason: str) -> None:
        """
        设置值
        Set value

        Args:
            value: 新值 / New value
            reason: 设置原因 / Reason for setting
        """
        ...

    def _clamp(self, value: T) -> T:
        """
        将值限制在有效范围内
        Clamp value to valid range

        Args:
            value: 原始值 / Original value

        Returns:
            限制后的值 / Clamped value
        """
        if value < self._min:
            return self._min
        if value > self._max:
            return self._max
        return value

    def _notify_change(self, old_value: T, new_value: T, reason: str) -> None:
        """
        通知值变化
        Notify value change

        Args:
            old_value: 旧值 / Old value
            new_value: 新值 / New value
            reason: 变化原因 / Change reason
        """
        if self._on_change is not None and old_value != new_value:
            self._on_change(old_value, new_value, reason)

    @property
    def max_value(self) -> T:
        """
        获取最大值
        Get maximum value
        """
        return self._max

    @property
    def min_value(self) -> T:
        """
        获取最小值
        Get minimum value
        """
        return self._min

    @property
    def percentage(self) -> float:
        """
        获取当前值占最大值的百分比
        Get current value as percentage of maximum

        Returns:
            百分比 [0.0, 1.0] / Percentage
        """
        if self._max == self._min:
            return 1.0
        return float(self._value - self._min) / float(self._max - self._min)
