"""
帧播放器
Frame Player

本模块提供帧播放控制和时序管理。
This module provides frame playback control and timing management.

帧播放器负责：
- 跟踪播放时间
- 计算当前帧
- 处理循环和停止
- 发出播放完成信号

Reference:
    - MOD: .github/prds/modules/MOD-Animation.md §3

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Callable, Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPixmap

from rainze.animation.frames.sequence import FrameSequence


class PlaybackState(Enum):
    """
    播放状态
    Playback state

    Attributes:
        STOPPED: 停止 / Stopped
        PLAYING: 播放中 / Playing
        PAUSED: 暂停 / Paused
    """

    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()


class FramePlayer(QObject):
    """
    帧播放器
    Frame Player

    控制帧序列的播放，处理时序和循环。
    Controls playback of frame sequences with timing and looping.

    Signals:
        frame_changed: 帧变化时发出 / Emitted when frame changes
        playback_finished: 播放完成时发出 / Emitted when playback finishes
        loop_completed: 循环完成时发出 / Emitted when a loop completes

    Attributes:
        _sequence: 当前帧序列 / Current frame sequence
        _state: 播放状态 / Playback state
        _elapsed_ms: 已播放时间 / Elapsed playback time
        _current_frame_index: 当前帧索引 / Current frame index
        _playback_speed: 播放速度倍率 / Playback speed multiplier

    Example:
        >>> player = FramePlayer()
        >>> player.set_sequence(idle_sequence)
        >>> player.frame_changed.connect(on_frame_changed)
        >>> player.play()
        >>> # In update loop:
        >>> player.update(delta_ms)

    Reference:
        PRD §0.14: 动画播放控制
    """

    # Qt 信号 / Qt Signals
    frame_changed = Signal(QPixmap, int)  # (pixmap, frame_index)
    playback_finished = Signal()
    loop_completed = Signal(int)  # loop_count

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """
        初始化帧播放器
        Initialize frame player

        Args:
            parent: 父 QObject / Parent QObject
        """
        super().__init__(parent)

        # 帧序列 / Frame sequence
        self._sequence: Optional[FrameSequence] = None

        # 播放状态 / Playback state
        self._state: PlaybackState = PlaybackState.STOPPED
        self._elapsed_ms: int = 0
        self._current_frame_index: int = -1
        self._loop_count: int = 0

        # 播放参数 / Playback parameters
        self._playback_speed: float = 1.0

        # 回调 / Callbacks
        self._on_complete: Optional[Callable[[], None]] = None

    # ==================== 属性 / Properties ====================

    @property
    def sequence(self) -> Optional[FrameSequence]:
        """
        获取当前帧序列
        Get current frame sequence

        Returns:
            当前帧序列或 None / Current sequence or None
        """
        return self._sequence

    @property
    def state(self) -> PlaybackState:
        """
        获取播放状态
        Get playback state

        Returns:
            当前播放状态 / Current playback state
        """
        return self._state

    @property
    def is_playing(self) -> bool:
        """
        检查是否正在播放
        Check if playing

        Returns:
            True 如果正在播放 / True if playing
        """
        return self._state == PlaybackState.PLAYING

    @property
    def is_paused(self) -> bool:
        """
        检查是否暂停
        Check if paused

        Returns:
            True 如果暂停 / True if paused
        """
        return self._state == PlaybackState.PAUSED

    @property
    def is_stopped(self) -> bool:
        """
        检查是否停止
        Check if stopped

        Returns:
            True 如果停止 / True if stopped
        """
        return self._state == PlaybackState.STOPPED

    @property
    def elapsed_ms(self) -> int:
        """
        获取已播放时间
        Get elapsed time

        Returns:
            已播放毫秒数 / Elapsed milliseconds
        """
        return self._elapsed_ms

    @property
    def current_frame_index(self) -> int:
        """
        获取当前帧索引
        Get current frame index

        Returns:
            当前帧索引，无效时返回 -1 / Current index, -1 if invalid
        """
        return self._current_frame_index

    @property
    def playback_speed(self) -> float:
        """
        获取播放速度
        Get playback speed

        Returns:
            播放速度倍率 / Playback speed multiplier
        """
        return self._playback_speed

    @playback_speed.setter
    def playback_speed(self, value: float) -> None:
        """
        设置播放速度
        Set playback speed

        Args:
            value: 播放速度倍率 (0.1-10.0) / Speed multiplier
        """
        self._playback_speed = max(0.1, min(10.0, value))

    @property
    def loop_count(self) -> int:
        """
        获取循环次数
        Get loop count

        Returns:
            已完成的循环次数 / Number of completed loops
        """
        return self._loop_count

    @property
    def progress(self) -> float:
        """
        获取播放进度
        Get playback progress

        Returns:
            播放进度 (0.0-1.0) / Playback progress
        """
        if not self._sequence or self._sequence.total_duration_ms == 0:
            return 0.0
        return min(1.0, self._elapsed_ms / self._sequence.total_duration_ms)

    # ==================== 控制方法 / Control Methods ====================

    def set_sequence(
        self,
        sequence: FrameSequence,
        auto_play: bool = False,
    ) -> None:
        """
        设置帧序列
        Set frame sequence

        Args:
            sequence: 要播放的帧序列 / Frame sequence to play
            auto_play: 是否自动开始播放 / Whether to auto-start
        """
        self._sequence = sequence
        self._elapsed_ms = 0
        self._current_frame_index = -1
        self._loop_count = 0
        self._state = PlaybackState.STOPPED

        if auto_play:
            self.play()

    def play(self, on_complete: Optional[Callable[[], None]] = None) -> None:
        """
        开始播放
        Start playback

        Args:
            on_complete: 播放完成回调（仅非循环时触发）
                         Completion callback (only for non-looping)
        """
        if not self._sequence or self._sequence.is_empty:
            return

        self._on_complete = on_complete
        self._state = PlaybackState.PLAYING

        # 如果从停止状态开始，重置时间
        # Reset time if starting from stopped
        if self._elapsed_ms == 0:
            self._loop_count = 0

        # 触发首帧 / Emit first frame
        self._update_current_frame()

    def pause(self) -> None:
        """
        暂停播放
        Pause playback
        """
        if self._state == PlaybackState.PLAYING:
            self._state = PlaybackState.PAUSED

    def resume(self) -> None:
        """
        恢复播放
        Resume playback
        """
        if self._state == PlaybackState.PAUSED:
            self._state = PlaybackState.PLAYING

    def stop(self) -> None:
        """
        停止播放
        Stop playback
        """
        self._state = PlaybackState.STOPPED
        self._elapsed_ms = 0
        self._current_frame_index = -1
        self._loop_count = 0
        self._on_complete = None

    def seek(self, time_ms: int) -> None:
        """
        跳转到指定时间
        Seek to specific time

        Args:
            time_ms: 目标时间（毫秒）/ Target time in ms
        """
        if not self._sequence:
            return

        self._elapsed_ms = max(0, time_ms)
        self._update_current_frame()

    def seek_to_frame(self, frame_index: int) -> None:
        """
        跳转到指定帧
        Seek to specific frame

        Args:
            frame_index: 目标帧索引 / Target frame index
        """
        if not self._sequence or frame_index < 0:
            return

        # 计算帧开始时间 / Calculate frame start time
        time_ms = 0
        for i, frame in enumerate(self._sequence.frames):
            if i >= frame_index:
                break
            time_ms += frame.duration_ms

        self._elapsed_ms = time_ms
        self._update_current_frame()

    # ==================== 更新方法 / Update Methods ====================

    def update(self, delta_ms: int) -> None:
        """
        更新播放器状态
        Update player state

        每帧调用此方法以推进动画。
        Call this method each frame to advance animation.

        Args:
            delta_ms: 距上次更新的毫秒数 / Milliseconds since last update
        """
        if self._state != PlaybackState.PLAYING or not self._sequence:
            return

        # 应用播放速度 / Apply playback speed
        adjusted_delta = int(delta_ms * self._playback_speed)
        self._elapsed_ms += adjusted_delta

        # 检查是否需要循环或结束
        # Check if need to loop or end
        total_duration = self._sequence.total_duration_ms
        if total_duration > 0 and self._elapsed_ms >= total_duration:
            if self._sequence.loop:
                # 循环播放 / Loop playback
                self._loop_count += 1
                self._elapsed_ms = self._elapsed_ms % total_duration
                self.loop_completed.emit(self._loop_count)
            else:
                # 播放完成 / Playback finished
                self._elapsed_ms = total_duration
                self._state = PlaybackState.STOPPED
                self.playback_finished.emit()

                # 触发完成回调 / Trigger completion callback
                if self._on_complete:
                    callback = self._on_complete
                    self._on_complete = None
                    callback()
                return

        # 更新当前帧 / Update current frame
        self._update_current_frame()

    def _update_current_frame(self) -> None:
        """
        更新当前帧（内部方法）
        Update current frame (internal method)
        """
        if not self._sequence:
            return

        new_index = self._sequence.get_frame_index_at_time(self._elapsed_ms)
        if new_index != self._current_frame_index:
            self._current_frame_index = new_index
            frame = self._sequence.get_frame(new_index)
            if frame and frame.is_valid:
                self.frame_changed.emit(frame.pixmap, new_index)

    # ==================== 便捷方法 / Convenience Methods ====================

    def get_current_pixmap(self) -> Optional[QPixmap]:
        """
        获取当前帧图像
        Get current frame pixmap

        Returns:
            当前帧 QPixmap 或 None / Current QPixmap or None
        """
        if not self._sequence:
            return None
        return self._sequence.get_pixmap_at_time(self._elapsed_ms)

    def __repr__(self) -> str:
        """
        字符串表示
        String representation
        """
        seq_name = self._sequence.name if self._sequence else "None"
        return (
            f"<FramePlayer "
            f"sequence={seq_name!r} "
            f"state={self._state.name} "
            f"elapsed={self._elapsed_ms}ms>"
        )
