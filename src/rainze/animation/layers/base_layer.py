"""
动画层抽象基类
Animation Layer Abstract Base Class

本模块定义所有动画层的通用接口。
This module defines the common interface for all animation layers.

所有动画层（Base, Idle, Expression, Action, Effect, LipSync）
都必须继承此基类并实现抽象方法。
All animation layers must inherit from this base class and implement
abstract methods.

Reference:
    - PRD §0.14: 6层动画架构
    - MOD: .github/prds/modules/MOD-Animation.md §3.2

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from PySide6.QtGui import QPixmap

from rainze.animation.models import BlendMode


class AnimationLayer(ABC):
    """
    动画层抽象基类
    Animation layer abstract base class

    提供动画层的通用功能：
    - 帧序列管理
    - 播放控制
    - 混合模式设置

    Provides common functionality for animation layers:
    - Frame sequence management
    - Playback control
    - Blend mode configuration

    Attributes:
        _name: 层名称 / Layer name
        _index: 层索引 (0-5) / Layer index
        _visible: 是否可见 / Visibility flag
        _blend_mode: 混合模式 / Blend mode

    Example:
        >>> class IdleLayer(AnimationLayer):
        ...     def get_current_frame(self) -> Optional[QPixmap]:
        ...         return self._current_pixmap
        ...
        ...     def update(self, delta_ms: int) -> None:
        ...         self._elapsed += delta_ms
        ...
        ...     def reset(self) -> None:
        ...         self._elapsed = 0

    Reference:
        PRD §0.14: 动画层规范
    """

    def __init__(
        self,
        name: str,
        index: int,
        blend_mode: BlendMode = BlendMode.NORMAL,
    ) -> None:
        """
        初始化动画层
        Initialize animation layer

        Args:
            name: 层名称 / Layer name (e.g., "Base", "Idle", "Expression")
            index: 层索引 / Layer index (0-5, higher = on top)
            blend_mode: 混合模式 / Blend mode for compositing
        """
        # 层标识 / Layer identity
        self._name: str = name
        self._index: int = index

        # 渲染属性 / Rendering properties
        self._visible: bool = True
        self._blend_mode: BlendMode = blend_mode
        self._opacity: float = 1.0

        # 播放状态 / Playback state
        self._paused: bool = False
        self._elapsed_ms: int = 0

    # ==================== 属性 / Properties ====================

    @property
    def name(self) -> str:
        """
        获取层名称
        Get layer name

        Returns:
            层名称字符串 / Layer name string
        """
        return self._name

    @property
    def index(self) -> int:
        """
        获取层索引
        Get layer index

        Returns:
            层索引 (0-5) / Layer index
        """
        return self._index

    @property
    def visible(self) -> bool:
        """
        获取可见性
        Get visibility

        Returns:
            是否可见 / Whether layer is visible
        """
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        """
        设置可见性
        Set visibility

        Args:
            value: 是否可见 / Whether to show layer
        """
        self._visible = value

    @property
    def blend_mode(self) -> BlendMode:
        """
        获取混合模式
        Get blend mode

        Returns:
            当前混合模式 / Current blend mode
        """
        return self._blend_mode

    @property
    def opacity(self) -> float:
        """
        获取不透明度
        Get opacity

        Returns:
            不透明度 (0.0-1.0) / Opacity value
        """
        return self._opacity

    @opacity.setter
    def opacity(self, value: float) -> None:
        """
        设置不透明度
        Set opacity

        Args:
            value: 不透明度 (0.0-1.0) / Opacity value
        """
        self._opacity = max(0.0, min(1.0, value))

    @property
    def paused(self) -> bool:
        """
        获取暂停状态
        Get paused state

        Returns:
            是否暂停 / Whether layer is paused
        """
        return self._paused

    # ==================== 抽象方法 / Abstract Methods ====================

    @abstractmethod
    def get_current_frame(self) -> Optional[QPixmap]:
        """
        获取当前帧图像
        Get current frame image

        子类必须实现此方法，返回当前应显示的帧。
        Subclasses must implement this method to return current frame.

        Returns:
            当前帧图像，无有效帧返回 None
            Current frame pixmap, None if no valid frame
        """
        ...

    @abstractmethod
    def update(self, delta_ms: int) -> None:
        """
        更新动画状态
        Update animation state

        子类必须实现此方法，根据时间推进动画。
        Subclasses must implement this to advance animation based on time.

        Args:
            delta_ms: 距上次更新的毫秒数 / Milliseconds since last update
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """
        重置到初始状态
        Reset to initial state

        子类必须实现此方法，将动画重置到起始位置。
        Subclasses must implement this to reset animation to start.
        """
        ...

    # ==================== 公共方法 / Public Methods ====================

    def set_blend_mode(self, mode: BlendMode) -> None:
        """
        设置混合模式
        Set blend mode

        Args:
            mode: 混合模式 / Blend mode to use
        """
        self._blend_mode = mode

    def pause(self) -> None:
        """
        暂停动画
        Pause animation
        """
        self._paused = True

    def resume(self) -> None:
        """
        恢复动画
        Resume animation
        """
        self._paused = False

    def tick(self, delta_ms: int) -> None:
        """
        推进动画时间（带暂停检查）
        Advance animation time (with pause check)

        这是 update() 的包装器，会自动检查暂停状态。
        This is a wrapper for update() that checks pause state.

        Args:
            delta_ms: 距上次更新的毫秒数 / Milliseconds since last update
        """
        if not self._paused:
            self.update(delta_ms)

    def __repr__(self) -> str:
        """
        字符串表示
        String representation
        """
        return (
            f"<{self.__class__.__name__} "
            f"name={self._name!r} "
            f"index={self._index} "
            f"visible={self._visible}>"
        )
