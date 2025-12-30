"""
动画核心数据模型
Animation Core Data Models

本模块定义动画系统的基础数据结构。
This module defines fundamental data structures for the animation system.

包含：
- AnimationState: 动画状态机状态
- AnimationFrame: 单帧动画数据
- BlendMode: 图层混合模式

Reference:
    - PRD §0.14: 动画系统架构
    - MOD: .github/prds/modules/MOD-Animation.md §3.1

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict

from PySide6.QtGui import QPixmap


class AnimationState(Enum):
    """
    动画状态机状态
    Animation state machine states

    定义桌宠动画系统可能处于的各种状态。
    Defines various states the pet animation system can be in.

    Attributes:
        IDLE: 待机状态，播放呼吸等微动 / Idle state with breathing animation
        TALKING: 说话中，启用口型同步 / Talking with lip sync enabled
        REACTING: 表情反应中 / Showing expression reaction
        ACTING: 执行动作中 / Performing action animation
        TRANSITIONING: 状态过渡中 / Transitioning between states
        SLEEPING: 睡眠状态 / Sleep state

    Example:
        >>> state = AnimationState.IDLE
        >>> if state == AnimationState.TALKING:
        ...     enable_lipsync()
    """

    IDLE = auto()  # 待机 / Idle
    TALKING = auto()  # 说话中 / Talking
    REACTING = auto()  # 表情反应 / Reacting
    ACTING = auto()  # 执行动作 / Acting
    TRANSITIONING = auto()  # 状态过渡 / Transitioning
    SLEEPING = auto()  # 睡眠状态 / Sleeping


class BlendMode(Enum):
    """
    图层混合模式
    Layer blend modes

    定义动画层如何与下层合成。
    Defines how animation layers composite with layers below.

    Attributes:
        NORMAL: 正常覆盖，不透明区域完全替换 / Normal overlay
        OVERLAY: 叠加混合，用于特效 / Overlay blend for effects
        ADDITIVE: 加法混合，用于发光效果 / Additive blend for glow

    Example:
        >>> layer.blend_mode = BlendMode.ADDITIVE
    """

    NORMAL = auto()  # 正常覆盖 / Normal overlay
    OVERLAY = auto()  # 叠加混合 / Overlay blend
    ADDITIVE = auto()  # 加法混合 / Additive blend


@dataclass
class AnimationFrame:
    """
    动画帧数据
    Animation frame data

    存储单帧动画的所有相关信息。
    Stores all information related to a single animation frame.

    Attributes:
        pixmap: 帧图像 / Frame image (QPixmap)
        duration_ms: 帧持续时间（毫秒）/ Frame duration in milliseconds
        metadata: 附加元数据 / Additional metadata (anchor points, etc.)

    Example:
        >>> frame = AnimationFrame(
        ...     pixmap=QPixmap("frame_001.png"),
        ...     duration_ms=33,  # ~30 FPS
        ...     metadata={"anchor": (128, 256)}
        ... )

    Reference:
        PRD §0.14: 动画帧规格
    """

    pixmap: QPixmap
    duration_ms: int = 33  # 默认 ~30 FPS / Default ~30 FPS
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        验证帧数据
        Validate frame data
        """
        # 确保持续时间为正数
        # Ensure duration is positive
        if self.duration_ms <= 0:
            self.duration_ms = 33

    @property
    def is_valid(self) -> bool:
        """
        检查帧是否有效
        Check if frame is valid

        Returns:
            True 如果 pixmap 不为空 / True if pixmap is not null
        """
        return not self.pixmap.isNull()

    def get_anchor(self) -> tuple[int, int]:
        """
        获取锚点位置
        Get anchor point position

        Returns:
            锚点坐标 (x, y)，默认 (0, 0) / Anchor coordinates, default (0, 0)
        """
        anchor = self.metadata.get("anchor")
        if isinstance(anchor, (list, tuple)) and len(anchor) >= 2:
            return (int(anchor[0]), int(anchor[1]))
        return (0, 0)

    def with_duration(self, duration_ms: int) -> "AnimationFrame":
        """
        创建具有不同持续时间的帧副本
        Create a copy of frame with different duration

        Args:
            duration_ms: 新的持续时间 / New duration in milliseconds

        Returns:
            新的 AnimationFrame 实例 / New AnimationFrame instance
        """
        return AnimationFrame(
            pixmap=self.pixmap,
            duration_ms=duration_ms,
            metadata=self.metadata.copy(),
        )


@dataclass
class FrameMetrics:
    """
    帧性能指标
    Frame performance metrics

    用于监控动画系统性能。
    Used for monitoring animation system performance.

    Attributes:
        render_time_ms: 渲染耗时 / Render time in ms
        frame_index: 帧索引 / Frame index
        dropped: 是否丢帧 / Whether frame was dropped
    """

    render_time_ms: float = 0.0
    frame_index: int = 0
    dropped: bool = False
