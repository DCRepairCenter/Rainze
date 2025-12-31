"""
动画层模块
Animation Layers Module

本模块提供动画层的基类和各层实现。
This module provides base class and implementations for animation layers.

6层动画架构 / 6-Layer Animation Architecture:
- Layer 0: Base (基础层) - 角色主体、服装
- Layer 1: Idle (待机层) - 呼吸、微动
- Layer 2: Expression (表情层) - 眼睛、眉毛、嘴巴
- Layer 3: Action (动作层) - 肢体动作
- Layer 4: Effect (特效层) - 粒子效果
- Layer 5: LipSync (口型层) - 嘴型动画

Exports / 导出:
- AnimationLayer: 动画层抽象基类 / Animation layer abstract base class

Reference:
    - MOD: .github/prds/modules/MOD-Animation.md §1.2

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from .base_layer import AnimationLayer

__all__ = [
    "AnimationLayer",
]
