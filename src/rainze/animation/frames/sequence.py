"""
帧序列
Frame Sequence

本模块提供动画帧序列的管理功能。
This module provides animation frame sequence management.

帧序列负责：
- 存储帧数据
- 计算总时长
- 提供帧访问接口

Reference:
    - MOD: .github/prds/modules/MOD-Animation.md §3

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, List, Optional

from PySide6.QtGui import QPixmap

from rainze.animation.models import AnimationFrame


@dataclass
class FrameSequence:
    """
    帧序列
    Frame Sequence

    管理一组动画帧，提供顺序访问和时间查询功能。
    Manages a collection of animation frames with sequential access
    and time-based queries.

    Attributes:
        name: 序列名称 / Sequence name
        frames: 帧列表 / List of frames
        loop: 是否循环播放 / Whether to loop
        anchor: 锚点位置 / Anchor point position

    Example:
        >>> seq = FrameSequence(name="idle", loop=True)
        >>> seq.add_frame(AnimationFrame(pixmap=img1, duration_ms=100))
        >>> seq.add_frame(AnimationFrame(pixmap=img2, duration_ms=100))
        >>> print(seq.total_duration_ms)  # 200
        >>> frame = seq.get_frame_at_time(150)  # Returns img2

    Reference:
        PRD §0.14: 动画帧规格
    """

    name: str = ""
    frames: List[AnimationFrame] = field(default_factory=list)
    loop: bool = True
    anchor: tuple[int, int] = (0, 0)

    # 缓存 / Cache
    _total_duration_cache: Optional[int] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """
        初始化后处理
        Post-initialization processing
        """
        # 清除缓存以确保正确计算
        # Clear cache to ensure correct calculation
        self._total_duration_cache = None

    # ==================== 属性 / Properties ====================

    @property
    def total_duration_ms(self) -> int:
        """
        获取总时长
        Get total duration

        Returns:
            所有帧时长之和（毫秒）/ Sum of all frame durations in ms
        """
        if self._total_duration_cache is None:
            self._total_duration_cache = sum(f.duration_ms for f in self.frames)
        return self._total_duration_cache

    @property
    def frame_count(self) -> int:
        """
        获取帧数
        Get frame count

        Returns:
            帧数量 / Number of frames
        """
        return len(self.frames)

    @property
    def is_empty(self) -> bool:
        """
        检查是否为空
        Check if empty

        Returns:
            True 如果没有帧 / True if no frames
        """
        return len(self.frames) == 0

    # ==================== 帧操作 / Frame Operations ====================

    def add_frame(self, frame: AnimationFrame) -> None:
        """
        添加帧
        Add frame

        Args:
            frame: 要添加的帧 / Frame to add
        """
        self.frames.append(frame)
        # 清除缓存 / Invalidate cache
        self._total_duration_cache = None

    def add_frames(self, frames: List[AnimationFrame]) -> None:
        """
        批量添加帧
        Add multiple frames

        Args:
            frames: 帧列表 / List of frames to add
        """
        self.frames.extend(frames)
        # 清除缓存 / Invalidate cache
        self._total_duration_cache = None

    def get_frame(self, index: int) -> Optional[AnimationFrame]:
        """
        按索引获取帧
        Get frame by index

        Args:
            index: 帧索引 / Frame index

        Returns:
            帧对象，索引无效返回 None / Frame or None if invalid index
        """
        if 0 <= index < len(self.frames):
            return self.frames[index]
        return None

    def get_frame_at_time(self, elapsed_ms: int) -> Optional[AnimationFrame]:
        """
        根据时间获取帧
        Get frame at specific time

        Args:
            elapsed_ms: 经过的毫秒数 / Elapsed milliseconds

        Returns:
            该时间点应显示的帧 / Frame to display at that time
        """
        if self.is_empty:
            return None

        total = self.total_duration_ms
        if total == 0:
            return self.frames[0] if self.frames else None

        # 处理循环 / Handle looping
        if self.loop and elapsed_ms >= total:
            elapsed_ms = elapsed_ms % total

        # 查找帧 / Find frame
        accumulated = 0
        for frame in self.frames:
            accumulated += frame.duration_ms
            if elapsed_ms < accumulated:
                return frame

        # 返回最后一帧（非循环且超时）
        # Return last frame (non-looping and past end)
        return self.frames[-1] if self.frames else None

    def get_frame_index_at_time(self, elapsed_ms: int) -> int:
        """
        根据时间获取帧索引
        Get frame index at specific time

        Args:
            elapsed_ms: 经过的毫秒数 / Elapsed milliseconds

        Returns:
            帧索引，空序列返回 -1 / Frame index, -1 if empty
        """
        if self.is_empty:
            return -1

        total = self.total_duration_ms
        if total == 0:
            return 0

        # 处理循环 / Handle looping
        if self.loop and elapsed_ms >= total:
            elapsed_ms = elapsed_ms % total

        # 查找帧索引 / Find frame index
        accumulated = 0
        for i, frame in enumerate(self.frames):
            accumulated += frame.duration_ms
            if elapsed_ms < accumulated:
                return i

        return len(self.frames) - 1

    def get_pixmap_at_time(self, elapsed_ms: int) -> Optional[QPixmap]:
        """
        根据时间获取 QPixmap
        Get QPixmap at specific time

        这是一个便捷方法，直接返回 pixmap。
        Convenience method that returns pixmap directly.

        Args:
            elapsed_ms: 经过的毫秒数 / Elapsed milliseconds

        Returns:
            该时间点的 QPixmap / QPixmap at that time
        """
        frame = self.get_frame_at_time(elapsed_ms)
        return frame.pixmap if frame else None

    def clear(self) -> None:
        """
        清空所有帧
        Clear all frames
        """
        self.frames.clear()
        self._total_duration_cache = None

    # ==================== 迭代 / Iteration ====================

    def __iter__(self) -> Iterator[AnimationFrame]:
        """
        迭代帧
        Iterate over frames
        """
        return iter(self.frames)

    def __len__(self) -> int:
        """
        获取帧数
        Get frame count
        """
        return len(self.frames)

    def __getitem__(self, index: int) -> AnimationFrame:
        """
        索引访问
        Index access
        """
        return self.frames[index]

    # ==================== 工厂方法 / Factory Methods ====================

    @classmethod
    def from_pixmaps(
        cls,
        pixmaps: List[QPixmap],
        duration_ms: int = 33,
        name: str = "",
        loop: bool = True,
    ) -> "FrameSequence":
        """
        从 QPixmap 列表创建帧序列
        Create frame sequence from QPixmap list

        Args:
            pixmaps: QPixmap 列表 / List of QPixmaps
            duration_ms: 每帧持续时间 / Duration per frame in ms
            name: 序列名称 / Sequence name
            loop: 是否循环 / Whether to loop

        Returns:
            新的帧序列 / New frame sequence
        """
        frames = [AnimationFrame(pixmap=pm, duration_ms=duration_ms) for pm in pixmaps]
        return cls(name=name, frames=frames, loop=loop)

    def __repr__(self) -> str:
        """
        字符串表示
        String representation
        """
        return (
            f"<FrameSequence "
            f"name={self.name!r} "
            f"frames={len(self.frames)} "
            f"duration={self.total_duration_ms}ms "
            f"loop={self.loop}>"
        )
