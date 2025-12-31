"""
透明窗口基类
Transparent Widget Base Class

本模块提供透明无边框窗口的基础实现。
This module provides base implementation for transparent frameless windows.

Reference:
    - MOD: .github/prds/modules/MOD-GUI.md §3.1
    - TECH: .github/techstacks/TECH-Rainze.md §3.3

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication, QWidget

if TYPE_CHECKING:
    pass

__all__ = ["TransparentWidget"]


class TransparentWidget(QWidget):
    """
    透明无边框窗口基类
    Transparent Frameless Widget Base Class

    提供透明背景、无边框窗口的基础实现。
    Provides base implementation for transparent frameless windows.

    Attributes:
        _drag_position: 拖拽起始位置 / Drag start position
        _is_dragging: 是否正在拖拽 / Whether dragging
        _enable_drag: 是否启用拖拽 / Whether drag is enabled
        _stay_on_top: 是否始终置顶 / Whether stay on top

    Signals:
        drag_started: 开始拖拽信号 / Drag started signal
        drag_ended: 结束拖拽信号 (final_position) / Drag ended signal
        position_changed: 位置变化信号 (new_position) / Position changed signal
    """

    # 信号定义 / Signal definitions
    drag_started: Signal = Signal()
    drag_ended: Signal = Signal(QPoint)
    position_changed: Signal = Signal(QPoint)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        enable_drag: bool = True,
        stay_on_top: bool = True,
        enable_transparency: bool = True,
    ) -> None:
        """
        初始化透明窗口
        Initialize transparent window

        Args:
            parent: 父窗口 / Parent widget
            enable_drag: 是否启用拖拽，默认 True / Enable drag, default True
            stay_on_top: 是否始终置顶，默认 True / Stay on top, default True
            enable_transparency: 是否启用透明，默认 True / Enable transparency
        """
        super().__init__(parent)

        # 内部状态 / Internal state
        self._drag_position: Optional[QPoint] = None
        self._is_dragging: bool = False
        self._enable_drag: bool = enable_drag
        self._stay_on_top: bool = stay_on_top

        # 设置窗口属性 / Setup window attributes
        self.setup_window_flags(stay_on_top)
        if enable_transparency:
            self.setup_transparency()

    def setup_window_flags(self, stay_on_top: bool) -> None:
        """
        设置窗口标志
        Setup window flags

        配置: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        Config: Frameless + StayOnTop + Tool

        Args:
            stay_on_top: 是否置顶 / Whether stay on top
        """
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool

        if stay_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint

        self.setWindowFlags(flags)

    def setup_transparency(self) -> None:
        """
        设置透明背景
        Setup transparent background

        配置: Qt.WA_TranslucentBackground
        """
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_mouse_passthrough(self, enable: bool) -> None:
        """
        设置鼠标穿透
        Set mouse passthrough

        Args:
            enable: 是否启用穿透 / Whether enable passthrough
        """
        self.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            enable,
        )

    def set_drag_enabled(self, enable: bool) -> None:
        """
        设置是否启用拖拽
        Set whether drag is enabled

        Args:
            enable: 是否启用 / Whether enabled
        """
        self._enable_drag = enable

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        鼠标按下事件处理
        Mouse press event handler

        记录拖拽起始位置，发射 drag_started 信号。
        Record drag start position, emit drag_started signal.
        """
        if event.button() == Qt.MouseButton.LeftButton and self._enable_drag:
            self._is_dragging = True
            self._drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            self.drag_started.emit()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """
        鼠标移动事件处理
        Mouse move event handler

        计算偏移量，移动窗口，发射 position_changed 信号。
        Calculate offset, move window, emit position_changed signal.
        """
        if self._is_dragging and self._drag_position is not None:
            new_pos = event.globalPosition().toPoint() - self._drag_position
            self.move(new_pos)
            self.position_changed.emit(new_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """
        鼠标释放事件处理
        Mouse release event handler

        结束拖拽，发射 drag_ended 信号。
        End drag, emit drag_ended signal.
        """
        if event.button() == Qt.MouseButton.LeftButton and self._is_dragging:
            self._is_dragging = False
            final_pos = self.pos()

            # 检查边缘吸附 / Check edge snap
            snapped_pos = self.snap_to_edge(final_pos)
            if snapped_pos != final_pos:
                self.move(snapped_pos)
                final_pos = snapped_pos

            self.drag_ended.emit(final_pos)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def snap_to_edge(self, position: QPoint, threshold: int = 50) -> QPoint:
        """
        边缘吸附计算
        Edge snap calculation

        Args:
            position: 当前位置 / Current position
            threshold: 吸附阈值 (像素) / Snap threshold in pixels

        Returns:
            吸附后的位置 / Position after snapping
        """
        screen = self.get_screen_geometry()
        x, y = position.x(), position.y()
        w, h = self.width(), self.height()

        # 左边缘吸附 / Left edge snap
        if x < threshold:
            x = 0

        # 右边缘吸附 / Right edge snap
        if x + w > screen.width() - threshold:
            x = screen.width() - w

        # 上边缘吸附 / Top edge snap
        if y < threshold:
            y = 0

        # 下边缘吸附 / Bottom edge snap
        if y + h > screen.height() - threshold:
            y = screen.height() - h

        return QPoint(x, y)

    def get_screen_geometry(self) -> QRect:
        """
        获取当前屏幕几何信息
        Get current screen geometry

        Returns:
            屏幕矩形区域 / Screen rectangle
        """
        screen = QApplication.primaryScreen()
        if screen:
            return screen.availableGeometry()
        # 回退到默认值 / Fallback to default
        from PySide6.QtCore import QRect

        return QRect(0, 0, 1920, 1080)

    def center_on_screen(self) -> None:
        """
        将窗口居中到屏幕
        Center window on screen
        """
        screen = self.get_screen_geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def move_to_corner(self, corner: str = "bottom_right") -> None:
        """
        移动到屏幕角落
        Move to screen corner

        Args:
            corner: 角落位置 / Corner position
                    "top_left", "top_right", "bottom_left", "bottom_right"
        """
        screen = self.get_screen_geometry()
        margin = 20  # 边距 / Margin

        if corner == "top_left":
            x, y = margin, margin
        elif corner == "top_right":
            x = screen.width() - self.width() - margin
            y = margin
        elif corner == "bottom_left":
            x = margin
            y = screen.height() - self.height() - margin
        else:  # bottom_right
            x = screen.width() - self.width() - margin
            y = screen.height() - self.height() - margin

        self.move(x, y)
