"""
动画数据模型
Animation Data Models

本模块定义动画系统使用的数据结构。
This module defines data structures used by the animation system.

Exports / 导出:
- AnimationState: 动画状态枚举 / Animation state enum
- AnimationFrame: 动画帧数据类 / Animation frame dataclass
- BlendMode: 图层混合模式 / Layer blend mode

Reference:
    - MOD: .github/prds/modules/MOD-Animation.md §3.1

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from .animation import AnimationFrame, AnimationState, BlendMode

__all__ = [
    "AnimationState",
    "AnimationFrame",
    "BlendMode",
]
