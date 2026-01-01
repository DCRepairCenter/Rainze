"""
系统托盘管理
System Tray Management

本模块提供系统托盘图标和菜单功能。
This module provides system tray icon and menu functionality.

Reference:
    - MOD: .github/prds/modules/MOD-GUI.md §3.3
    - PRD: 第一部分功能 系统托盘

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

if TYPE_CHECKING:
    from rainze.core import EventBus

__all__ = ["SystemTray"]


class SystemTray(QObject):
    """
    系统托盘管理器
    System Tray Manager

    管理系统托盘图标和菜单，提供快速操作入口。
    Manages system tray icon and menu, provides quick access.

    Attributes:
        _tray_icon: 系统托盘图标 / System tray icon
        _tray_menu: 托盘右键菜单 / Tray context menu
        _event_bus: 事件总线引用 / Event bus reference

    Signals:
        activated: 托盘图标被激活 (activation_reason) / Tray activated
        show_requested: 请求显示主窗口 / Show window requested
        hide_requested: 请求隐藏主窗口 / Hide window requested
        quit_requested: 请求退出程序 / Quit requested
    """

    # 信号定义 / Signal definitions
    activated: Signal = Signal(int)
    show_requested: Signal = Signal()
    hide_requested: Signal = Signal()
    quit_requested: Signal = Signal()

    def __init__(
        self,
        event_bus: Optional["EventBus"] = None,
        parent: Optional[QObject] = None,
        *,
        icon_path: Optional[Path] = None,
        app_name: str = "Rainze",
    ) -> None:
        """
        初始化系统托盘
        Initialize system tray

        Args:
            event_bus: 事件总线实例 / Event bus instance
            parent: 父对象 / Parent object
            icon_path: 图标文件路径 / Icon file path
            app_name: 应用名称 / Application name
        """
        super().__init__(parent)

        self._event_bus = event_bus
        self._app_name = app_name
        self._icon_path = icon_path or Path("./assets/ui/icons/tray_icon.png")

        # 托盘图标和菜单将在 setup 方法中初始化 / Tray icon and menu will be initialized in setup methods
        # 使用占位符避免 None，因为 setup 方法会立即调用
        # Use placeholders to avoid None since setup methods are called immediately
        self._tray_icon: QSystemTrayIcon = QSystemTrayIcon()
        self._tray_menu: QMenu = QMenu()

        # 菜单项 / Menu actions
        self._actions: dict[str, QAction] = {}

        # 是否窗口可见 / Whether window visible
        self._window_visible: bool = True

        # 设置托盘 / Setup tray
        self.setup_tray_icon()
        self.setup_tray_menu()

    def setup_tray_icon(self) -> None:
        """
        设置托盘图标
        Setup tray icon
        """
        self._tray_icon = QSystemTrayIcon(self)

        # 加载图标 / Load icon
        if self._icon_path.exists():
            icon = QIcon(str(self._icon_path))
        else:
            # 使用应用图标作为回退 / Fallback to app icon
            app = QApplication.instance()
            if app is not None and isinstance(app, QApplication):
                icon = app.windowIcon()
            else:
                icon = QIcon()
            if icon.isNull():
                # 创建默认图标 / Create default icon
                icon = QIcon()

        self._tray_icon.setIcon(icon)
        self._tray_icon.setToolTip(self._app_name)

        # 连接激活信号 / Connect activation signal
        self._tray_icon.activated.connect(self._on_activated)

    def setup_tray_menu(self) -> None:
        """
        设置托盘菜单
        Setup tray menu

        菜单项 / Menu items:
        - 显示/隐藏 / Show/Hide
        - 免打扰模式 / Do Not Disturb
        - 分隔线 / Separator
        - 设置 / Settings
        - 关于 / About
        - 分隔线 / Separator
        - 退出 / Quit
        """
        self._tray_menu = QMenu()

        # 显示/隐藏 / Show/Hide
        self._actions["toggle_visible"] = self.add_menu_action(
            "隐藏",
            self._on_toggle_visible,
        )

        # 免打扰 / Do Not Disturb
        action_dnd = self.add_menu_action(
            "免打扰模式",
            self._on_toggle_dnd,
        )
        action_dnd.setCheckable(True)
        self._actions["dnd"] = action_dnd

        self.add_separator()

        # 设置 / Settings
        self._actions["settings"] = self.add_menu_action(
            "设置",
            self._on_settings,
        )

        # 关于 / About
        self._actions["about"] = self.add_menu_action(
            "关于",
            self._on_about,
        )

        self.add_separator()

        # 退出 / Quit
        self._actions["quit"] = self.add_menu_action(
            "退出",
            self._on_quit,
        )

        # 设置菜单 / Set menu
        self._tray_icon.setContextMenu(self._tray_menu)

    def add_menu_action(
        self,
        text: str,
        callback: Callable[[], None],
        icon: Optional[QIcon] = None,
        shortcut: Optional[str] = None,
    ) -> QAction:
        """
        添加菜单项
        Add menu action

        Args:
            text: 菜单文本 / Menu text
            callback: 点击回调 / Click callback
            icon: 图标 (可选) / Icon (optional)
            shortcut: 快捷键 (可选) / Shortcut (optional)

        Returns:
            创建的 QAction / Created QAction
        """
        action = QAction(text, self._tray_menu)

        if icon:
            action.setIcon(icon)
        if shortcut:
            action.setShortcut(shortcut)

        action.triggered.connect(callback)
        self._tray_menu.addAction(action)

        return action

    def add_separator(self) -> None:
        """
        添加分隔线
        Add separator
        """
        self._tray_menu.addSeparator()

    def show_notification(
        self,
        title: str,
        message: str,
        icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
        duration_ms: int = 3000,
    ) -> None:
        """
        显示托盘通知
        Show tray notification

        Args:
            title: 通知标题 / Notification title
            message: 通知内容 / Notification message
            icon: 图标类型 / Icon type
            duration_ms: 显示时长 (毫秒) / Display duration in ms
        """
        if self._tray_icon:
            self._tray_icon.showMessage(title, message, icon, duration_ms)

    def set_icon(self, icon_path: str) -> None:
        """
        设置托盘图标
        Set tray icon

        Args:
            icon_path: 图标文件路径 / Icon file path
        """
        if self._tray_icon:
            self._tray_icon.setIcon(QIcon(icon_path))

    def set_tooltip(self, text: str) -> None:
        """
        设置托盘提示文本
        Set tray tooltip

        Args:
            text: 提示文本 / Tooltip text
        """
        if self._tray_icon:
            self._tray_icon.setToolTip(text)

    def update_toggle_text(self, is_visible: bool) -> None:
        """
        更新显示/隐藏菜单文本
        Update show/hide menu text

        Args:
            is_visible: 窗口是否可见 / Whether window is visible
        """
        self._window_visible = is_visible
        if "toggle_visible" in self._actions:
            self._actions["toggle_visible"].setText("隐藏" if is_visible else "显示")

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """
        托盘激活事件处理
        Tray activation handler

        - 单击: 显示/隐藏窗口 / Single click: Toggle window
        - 双击: 打开设置 / Double click: Open settings
        """
        self.activated.emit(reason.value)

        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # 单击 / Single click
            self._on_toggle_visible()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # 双击 / Double click
            self._on_settings()

    def _on_toggle_visible(self) -> None:
        """
        切换窗口可见性
        Toggle window visibility
        """
        if self._window_visible:
            self.hide_requested.emit()
        else:
            self.show_requested.emit()

    def _on_toggle_dnd(self) -> None:
        """
        切换免打扰模式
        Toggle Do Not Disturb mode
        """
        # TODO: 实现免打扰模式 / Implement DND mode
        pass

    def _on_settings(self) -> None:
        """
        打开设置
        Open settings
        """
        # TODO: 发送打开设置事件 / Emit open settings event
        pass

    def _on_about(self) -> None:
        """
        显示关于
        Show about
        """
        # TODO: 发送显示关于事件 / Emit show about event
        pass

    def _on_quit(self) -> None:
        """
        退出程序
        Quit application
        """
        self.quit_requested.emit()

    def show(self) -> None:
        """
        显示托盘图标
        Show tray icon
        """
        if self._tray_icon:
            self._tray_icon.show()

    def hide(self) -> None:
        """
        隐藏托盘图标
        Hide tray icon
        """
        if self._tray_icon:
            self._tray_icon.hide()

    def is_available(self) -> bool:
        """
        检查系统托盘是否可用
        Check if system tray is available

        Returns:
            是否可用 / Whether available
        """
        return QSystemTrayIcon.isSystemTrayAvailable()
