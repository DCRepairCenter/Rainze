"""
桌宠主窗口
Pet Main Window

本模块提供桌宠的主显示窗口，集成动画渲染和交互。
This module provides pet's main display window with animation and interaction.

Reference:
    - MOD: .github/prds/modules/MOD-GUI.md §3.2
    - PRD: 第一部分 §12 基础物理与交互

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QContextMenuEvent, QMouseEvent, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .transparent_widget import TransparentWidget

if TYPE_CHECKING:
    from rainze.core import EventBus

__all__ = ["MainWindow", "DisplayMode"]


class DisplayMode:
    """
    显示模式枚举
    Display mode enumeration
    """

    FLOATING = "floating"  # 悬浮模式 / Floating mode
    TASKBAR_WALK = "taskbar_walk"  # 任务栏行走模式 / Taskbar walk mode


class MainWindow(TransparentWidget):
    """
    桌宠主窗口
    Pet Main Window

    管理桌宠的主显示窗口，整合动画渲染层和交互层。
    Manages pet's main display window, integrating animation and interaction.

    Attributes:
        _display_mode: 当前显示模式 / Current display mode
        _event_bus: 事件总线引用 / Event bus reference
        _pet_label: 桌宠图像标签 / Pet image label
        _current_frame: 当前帧图像 / Current frame pixmap

    Signals:
        display_mode_changed: 显示模式变化 (mode) / Display mode changed
        pet_clicked: 桌宠被点击 / Pet clicked
        pet_double_clicked: 桌宠被双击 / Pet double clicked
        pet_right_clicked: 桌宠被右键点击 (position) / Pet right clicked
    """

    # 信号定义 / Signal definitions
    display_mode_changed: Signal = Signal(str)
    pet_clicked: Signal = Signal()
    pet_double_clicked: Signal = Signal()
    pet_right_clicked: Signal = Signal(QPoint)

    def __init__(
        self,
        event_bus: Optional["EventBus"] = None,
        parent: Optional[QWidget] = None,
        *,
        default_size: tuple[int, int] = (200, 200),
        assets_dir: Optional[Path] = None,
    ) -> None:
        """
        初始化主窗口
        Initialize main window

        Args:
            event_bus: 事件总线实例 / Event bus instance
            parent: 父窗口 / Parent widget
            default_size: 默认大小 (width, height) / Default size
            assets_dir: 资源目录 / Assets directory
        """
        super().__init__(parent, enable_drag=True, stay_on_top=True)

        # 状态 / State
        self._event_bus = event_bus
        self._display_mode: str = DisplayMode.FLOATING
        self._assets_dir = assets_dir or Path("./assets")
        self._click_count: int = 0
        self._click_timer: QTimer = QTimer()
        self._click_timer.setSingleShot(True)
        self._click_timer.timeout.connect(self._on_click_timer)

        # UI 组件 / UI components
        self._pet_label: Optional[QLabel] = None
        self._current_frame: Optional[QPixmap] = None

        # 设置 UI / Setup UI
        self.setup_ui(default_size)

        # 加载初始帧 / Load initial frame
        self._load_initial_frame()

    def setup_ui(self, size: tuple[int, int]) -> None:
        """
        初始化 UI 组件
        Initialize UI components

        Args:
            size: 窗口大小 (width, height) / Window size
        """
        import logging
        logger = logging.getLogger(__name__)

        width, height = size
        self.setFixedSize(width, height)

        # 创建布局 / Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 创建桌宠图像标签 / Create pet image label
        self._pet_label = QLabel(self)
        self._pet_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pet_label.setScaledContents(True)
        # 确保标签背景透明 / Ensure label background is transparent
        self._pet_label.setStyleSheet("background: transparent;")
        layout.addWidget(self._pet_label)

        logger.info(f"MainWindow UI initialized: {width}x{height}")

    def _load_initial_frame(self) -> None:
        """
        加载初始帧图像
        Load initial frame image
        """
        import logging
        logger = logging.getLogger(__name__)

        # 尝试加载占位图 / Try to load placeholder
        frame_path = self._assets_dir / "animations" / "idle" / "default" / "frame_001.png"

        logger.info(f"Loading initial frame from: {frame_path}")
        logger.info(f"Path exists: {frame_path.exists()}")

        if frame_path.exists():
            pixmap = QPixmap(str(frame_path))
            logger.info(f"Pixmap loaded: null={pixmap.isNull()}, size={pixmap.width()}x{pixmap.height()}")
            if not pixmap.isNull():
                self.update_frame(pixmap)
                return

        # 如果没有图片，创建空白占位 / If no image, create blank placeholder
        logger.warning("No initial frame found, creating placeholder")
        self._create_placeholder_frame()

    def _create_placeholder_frame(self) -> None:
        """
        创建占位帧（当没有图片资源时）
        Create placeholder frame (when no image assets)
        """
        # 创建透明占位图 / Create transparent placeholder
        pixmap = QPixmap(self.width(), self.height())
        pixmap.fill(Qt.GlobalColor.transparent)
        self.update_frame(pixmap)

    def update_frame(self, pixmap: QPixmap) -> None:
        """
        更新动画帧
        Update animation frame

        由 AnimationController 调用，更新显示的图像。
        Called by AnimationController to update displayed image.

        Args:
            pixmap: 新的帧图像 / New frame pixmap
        """
        import logging
        logger = logging.getLogger(__name__)

        self._current_frame = pixmap
        if self._pet_label:
            logger.debug(f"Updating frame: {pixmap.width()}x{pixmap.height()}")
            self._pet_label.setPixmap(pixmap)

    def set_pet_size(self, width: int, height: int) -> None:
        """
        设置桌宠尺寸
        Set pet size

        Args:
            width: 宽度 / Width
            height: 高度 / Height
        """
        self.setFixedSize(width, height)

    def set_display_mode(self, mode: str) -> None:
        """
        切换显示模式
        Switch display mode

        Args:
            mode: DisplayMode.FLOATING 或 DisplayMode.TASKBAR_WALK
        """
        if mode == self._display_mode:
            return

        self._display_mode = mode
        self.display_mode_changed.emit(mode)

        # 根据模式调整行为 / Adjust behavior based on mode
        if mode == DisplayMode.TASKBAR_WALK:
            # 移动到任务栏上方 / Move to above taskbar
            screen = self.get_screen_geometry()
            x = self.x()
            y = screen.height() - self.height()
            self.move(x, y)

    def toggle_display_mode(self) -> None:
        """
        切换显示模式（在两种模式间切换）
        Toggle display mode (between two modes)
        """
        if self._display_mode == DisplayMode.FLOATING:
            self.set_display_mode(DisplayMode.TASKBAR_WALK)
        else:
            self.set_display_mode(DisplayMode.FLOATING)

    # === 交互事件 / Interaction Events ===

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        鼠标按下事件处理
        Mouse press event handler
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self._click_count += 1
            self._click_timer.start(300)  # 300ms 判断双击 / 300ms for double-click

        super().mousePressEvent(event)

    def _on_click_timer(self) -> None:
        """
        点击计时器超时处理
        Click timer timeout handler
        """
        if self._click_count == 1:
            self.pet_clicked.emit()
        elif self._click_count >= 2:
            self.pet_double_clicked.emit()
        self._click_count = 0

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """
        双击事件处理
        Double click event handler
        """
        if event.button() == Qt.MouseButton.LeftButton:
            # 取消单击计时器 / Cancel single click timer
            self._click_timer.stop()
            self._click_count = 0
            self.pet_double_clicked.emit()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """
        右键菜单事件处理
        Context menu event handler
        """
        self.pet_right_clicked.emit(event.globalPos())
        event.accept()

    # === 状态保存/恢复 / State Save/Restore ===

    def save_position(self) -> dict[str, int | str]:
        """
        保存窗口位置
        Save window position

        Returns:
            位置信息字典 / Position info dict
        """
        return {
            "x": self.x(),
            "y": self.y(),
            "mode": self._display_mode,
        }

    def restore_position(self, data: dict[str, int | str]) -> None:
        """
        恢复窗口位置
        Restore window position

        Args:
            data: save_position 返回的字典 / Dict from save_position
        """
        x_val = data.get("x", 0)
        y_val = data.get("y", 0)
        mode_val = data.get("mode", DisplayMode.FLOATING)

        # 类型转换确保正确类型 / Type conversion to ensure correct types
        x = int(x_val) if isinstance(x_val, int) else 0
        y = int(y_val) if isinstance(y_val, int) else 0
        mode = str(mode_val) if isinstance(mode_val, str) else DisplayMode.FLOATING

        self.move(x, y)
        self.set_display_mode(mode)
