"""
帧动画处理模块
Frame Animation Processing Module

本模块提供帧序列和帧播放器功能。
This module provides frame sequence and frame player functionality.

Exports / 导出:
- FrameSequence: 帧序列管理 / Frame sequence management
- FramePlayer: 帧播放器 / Frame player with timing

Reference:
    - MOD: .github/prds/modules/MOD-Animation.md §2

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from .player import FramePlayer
from .sequence import FrameSequence

__all__ = [
    "FrameSequence",
    "FramePlayer",
]
