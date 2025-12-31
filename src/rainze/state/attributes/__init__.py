"""
属性管理器模块
Attribute Manager Module

导出属性管理器相关的类。
Exports attribute manager related classes.
"""

from __future__ import annotations

from .affinity import AffinityConfig, AffinityManager
from .base import AttributeConfig, AttributeManager
from .energy import EnergyConfig, EnergyManager

__all__: list[str] = [
    # 基类 / Base classes
    "AttributeConfig",
    "AttributeManager",
    # 能量管理 / Energy management
    "EnergyConfig",
    "EnergyManager",
    # 好感度管理 / Affinity management
    "AffinityConfig",
    "AffinityManager",
]
