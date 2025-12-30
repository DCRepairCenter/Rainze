"""
动画系统模块
Animation System Module

本模块提供 Rainze 桌宠的完整动画系统。
This module provides the complete animation system for Rainze desktop pet.

6层动画架构 / 6-Layer Animation Architecture:
- Layer 0: Base (基础层) - 角色主体、服装
- Layer 1: Idle (待机层) - 呼吸、微动
- Layer 2: Expression (表情层) - 眼睛、眉毛、嘴巴
- Layer 3: Action (动作层) - 肢体动作
- Layer 4: Effect (特效层) - 粒子效果
- Layer 5: LipSync (口型层) - 嘴型同步

Core Components / 核心组件:
- AnimationController: 动画主控制器
- AnimationLayer: 动画层抽象基类
- FrameSequence: 帧序列管理
- FramePlayer: 帧播放控制

Usage / 使用示例:
    >>> from rainze.animation import AnimationController, AnimationState
    >>> controller = AnimationController(event_bus, resource_path="assets")
    >>> await controller.initialize()
    >>> controller.frame_ready.connect(window.update_image)
    >>> controller.set_expression("happy", intensity=0.8)
    >>> controller.play_action("wave")

Reference:
    - PRD: .github/prds/PRD-Rainze.md §0.14
    - MOD: .github/prds/modules/MOD-Animation.md

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

# 主控制器 / Main controller
from .controller import AnimationController

# 帧处理 / Frame processing
from .frames import (
    FramePlayer,
    FrameSequence,
)

# 层基类 / Layer base class
from .layers import AnimationLayer

# 数据模型 / Data models
from .models import (
    AnimationFrame,
    AnimationState,
    BlendMode,
)

__all__ = [
    # 主控制器 / Main controller
    "AnimationController",
    # 数据模型 / Data models
    "AnimationState",
    "AnimationFrame",
    "BlendMode",
    # 帧处理 / Frame processing
    "FrameSequence",
    "FramePlayer",
    # 层基类 / Layer base
    "AnimationLayer",
]
