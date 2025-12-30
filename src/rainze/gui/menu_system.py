"""
右键菜单系统
Right-Click Menu System

本模块提供桌宠右键菜单的管理，支持动态菜单项和子菜单。
This module provides pet's right-click menu management with dynamic items and submenus.

Reference:
    - MOD: .github/prds/modules/MOD-GUI.md §3.5
    - PRD: 第一部分 §16 程序快速启动器, §17 网站快捷访问

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Optional

from PySide6.QtCore import QObject, QPoint, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu

if TYPE_CHECKING:
    from rainze.core import EventBus

__all__ = ["MenuItem", "MenuSystem"]


@dataclass
class MenuItem:
    """
    菜单项配置
    Menu item configuration

    表示单个菜单项的数据结构，支持子菜单。
    Represents a single menu item data structure, supports submenus.

    Attributes:
        id: 菜单项唯一标识 / Menu item unique identifier
        text: 显示文本 / Display text
        icon: 图标路径（可选）/ Icon path (optional)
        shortcut: 快捷键（可选）/ Shortcut key (optional)
        callback: 点击回调函数（可选）/ Click callback (optional)
        enabled: 是否启用 / Whether enabled
        visible: 是否可见 / Whether visible
        children: 子菜单项列表 / Child menu items
        separator_after: 是否在此项后添加分隔线 / Add separator after this item
    """

    id: str
    text: str
    icon: Optional[str] = None
    shortcut: Optional[str] = None
    callback: Optional[Callable[[], None]] = None
    enabled: bool = True
    visible: bool = True
    children: list["MenuItem"] = field(default_factory=list)
    separator_after: bool = False


class MenuSystem(QObject):
    """
    右键菜单系统
    Right-Click Menu System

    管理桌宠右键菜单，支持动态菜单项和子菜单结构。
    Manages pet's context menu with dynamic items and submenu structures.

    Attributes:
        _menu: 主菜单实例 / Main menu instance
        _menu_items: 注册的菜单项（按 ID 映射）/ Registered menu items (by ID)
        _actions: QAction 映射（按 ID 映射）/ QAction mapping (by ID)
        _dynamic_providers: 动态子菜单提供函数 / Dynamic submenu providers
        _event_bus: 事件总线引用 / Event bus reference

    Signals:
        menu_shown: 菜单显示时发射 / Emitted when menu shown
        menu_hidden: 菜单隐藏时发射 / Emitted when menu hidden
        action_triggered: 菜单项被触发时发射 (item_id) / Emitted when action triggered

    Example:
        >>> menu_system = MenuSystem(event_bus)
        >>> menu_system.setup_default_menu()
        >>> menu_system.show_at(QPoint(100, 100))
    """

    # 信号定义 / Signal definitions
    menu_shown: Signal = Signal()
    menu_hidden: Signal = Signal()
    action_triggered: Signal = Signal(str)

    def __init__(
        self,
        event_bus: Optional["EventBus"] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        """
        初始化菜单系统
        Initialize menu system

        Args:
            event_bus: 事件总线实例 / Event bus instance
            parent: 父对象 / Parent object
        """
        super().__init__(parent)

        # 内部状态 / Internal state
        self._event_bus = event_bus
        self._menu: Optional[QMenu] = None
        self._menu_items: dict[str, MenuItem] = {}
        self._actions: dict[str, QAction] = {}
        self._dynamic_providers: dict[str, Callable[[], list[MenuItem]]] = {}

        # 有序列表，保持菜单项顺序 / Ordered list to maintain item order
        self._item_order: list[str] = []

    def setup_default_menu(self) -> None:
        """
        设置默认菜单结构
        Setup default menu structure

        创建标准菜单项，包括聊天、背包、日程等。
        Creates standard menu items including chat, backpack, schedule, etc.

        Reference:
            MOD-GUI.md §3.5: 默认菜单结构
        """
        # 清除现有菜单项 / Clear existing items
        self._menu_items.clear()
        self._item_order.clear()
        self._actions.clear()

        # 定义默认菜单项 / Define default menu items
        default_items = [
            # 主功能区 / Main features
            MenuItem(id="chat", text="聊天"),
            MenuItem(id="backpack", text="背包"),
            MenuItem(id="schedule", text="日程管理"),
            # 带子菜单的项 / Items with submenus
            MenuItem(
                id="butler_services",
                text="管家服务",
                children=[
                    MenuItem(id="butler_app_launcher", text="程序启动器"),
                    MenuItem(id="butler_file_manager", text="文件管理"),
                    MenuItem(id="butler_system_info", text="系统信息"),
                ],
            ),
            MenuItem(
                id="bookmarks",
                text="书签",
                children=[
                    MenuItem(id="bookmarks_add", text="添加书签"),
                    MenuItem(id="bookmarks_manage", text="管理书签"),
                ],
            ),
            MenuItem(
                id="games",
                text="小游戏",
                separator_after=True,
                children=[
                    MenuItem(id="games_guess_number", text="猜数字"),
                    MenuItem(id="games_rock_paper_scissors", text="石头剪刀布"),
                ],
            ),
            # 记录功能区 / Record features
            MenuItem(id="history", text="历史记录"),
            MenuItem(id="quick_note", text="记一笔"),
            MenuItem(
                id="observation_diary",
                text="生成观察日记",
                separator_after=True,
            ),
            # 设置区 / Settings
            MenuItem(id="user_profile", text="用户档案"),
            MenuItem(id="settings", text="设置"),
            MenuItem(
                id="help",
                text="帮助",
                separator_after=True,
            ),
            # 退出 / Exit
            MenuItem(id="quit", text="退出"),
        ]

        # 注册所有默认菜单项 / Register all default items
        for item in default_items:
            self.register_item(item)

    def register_item(self, item: MenuItem) -> None:
        """
        注册菜单项
        Register menu item

        将菜单项添加到菜单系统中。
        Adds a menu item to the menu system.

        Args:
            item: 菜单项配置 / Menu item configuration
        """
        self._menu_items[item.id] = item

        # 维护顺序 / Maintain order
        if item.id not in self._item_order:
            self._item_order.append(item.id)

        # 递归注册子菜单项 / Recursively register children
        for child in item.children:
            self._menu_items[child.id] = child

    def unregister_item(self, item_id: str) -> None:
        """
        注销菜单项
        Unregister menu item

        从菜单系统中移除菜单项。
        Removes a menu item from the menu system.

        Args:
            item_id: 菜单项 ID / Menu item ID
        """
        if item_id in self._menu_items:
            del self._menu_items[item_id]

        if item_id in self._item_order:
            self._item_order.remove(item_id)

        if item_id in self._actions:
            del self._actions[item_id]

    def update_item(
        self,
        item_id: str,
        *,
        text: Optional[str] = None,
        enabled: Optional[bool] = None,
        visible: Optional[bool] = None,
    ) -> None:
        """
        更新菜单项属性
        Update menu item properties

        动态修改已注册菜单项的属性。
        Dynamically modifies properties of a registered menu item.

        Args:
            item_id: 菜单项 ID / Menu item ID
            text: 新显示文本（可选）/ New display text (optional)
            enabled: 是否启用（可选）/ Whether enabled (optional)
            visible: 是否可见（可选）/ Whether visible (optional)
        """
        if item_id not in self._menu_items:
            return

        item = self._menu_items[item_id]

        if text is not None:
            # 创建新的 MenuItem 以更新（dataclass 是不可变的默认行为）
            # Create new MenuItem to update (dataclass immutability)
            self._menu_items[item_id] = MenuItem(
                id=item.id,
                text=text,
                icon=item.icon,
                shortcut=item.shortcut,
                callback=item.callback,
                enabled=enabled if enabled is not None else item.enabled,
                visible=visible if visible is not None else item.visible,
                children=item.children,
                separator_after=item.separator_after,
            )
        else:
            # 只更新 enabled/visible
            # Only update enabled/visible
            self._menu_items[item_id] = MenuItem(
                id=item.id,
                text=item.text,
                icon=item.icon,
                shortcut=item.shortcut,
                callback=item.callback,
                enabled=enabled if enabled is not None else item.enabled,
                visible=visible if visible is not None else item.visible,
                children=item.children,
                separator_after=item.separator_after,
            )

        # 同步更新 QAction（如果存在）
        # Sync update QAction if exists
        if item_id in self._actions:
            action = self._actions[item_id]
            if text is not None:
                action.setText(text)
            if enabled is not None:
                action.setEnabled(enabled)
            if visible is not None:
                action.setVisible(visible)

    def add_dynamic_submenu(
        self,
        parent_id: str,
        submenu_id: str,
        text: str,
        items_provider: Callable[[], list[MenuItem]],
    ) -> None:
        """
        添加动态子菜单
        Add dynamic submenu

        注册一个在显示时动态生成子项的子菜单。
        Registers a submenu that dynamically generates items when displayed.

        Args:
            parent_id: 父菜单项 ID / Parent menu item ID
            submenu_id: 子菜单 ID / Submenu ID
            text: 子菜单显示文本 / Submenu display text
            items_provider: 子菜单项提供函数（显示时调用）/ Item provider function

        Example:
            >>> def get_recent_files() -> list[MenuItem]:
            ...     return [MenuItem(id=f"file_{i}", text=f) for i in range(5)]
            >>> menu_system.add_dynamic_submenu(
            ...     "history", "recent_files", "最近文件", get_recent_files
            ... )
        """
        # 保存动态提供函数 / Save dynamic provider
        self._dynamic_providers[submenu_id] = items_provider

        # 创建占位菜单项 / Create placeholder menu item
        placeholder = MenuItem(
            id=submenu_id,
            text=text,
            children=[],  # 子项将在显示时动态生成 / Children generated at display time
        )

        # 尝试添加到父菜单项 / Try to add to parent item
        if parent_id in self._menu_items:
            parent = self._menu_items[parent_id]
            # 更新父菜单的 children 列表
            # Update parent's children list
            updated_children = list(parent.children) + [placeholder]
            self._menu_items[parent_id] = MenuItem(
                id=parent.id,
                text=parent.text,
                icon=parent.icon,
                shortcut=parent.shortcut,
                callback=parent.callback,
                enabled=parent.enabled,
                visible=parent.visible,
                children=updated_children,
                separator_after=parent.separator_after,
            )
        else:
            # 如果父菜单不存在，作为顶级菜单项注册
            # If parent doesn't exist, register as top-level item
            self.register_item(placeholder)

    def show_at(self, position: QPoint) -> None:
        """
        在指定位置显示菜单
        Show menu at specified position

        构建并显示右键菜单。
        Builds and displays the context menu.

        Args:
            position: 显示位置（屏幕坐标）/ Display position (screen coordinates)
        """
        # 构建菜单 / Build menu
        self._menu = self._build_menu()

        # 连接隐藏信号 / Connect hidden signal
        self._menu.aboutToHide.connect(self._on_menu_hidden)

        # 发射显示信号 / Emit shown signal
        self.menu_shown.emit()

        # 显示菜单 / Show menu
        self._menu.exec(position)

    def _build_menu(self) -> QMenu:
        """
        构建菜单
        Build menu

        根据注册的菜单项构建 QMenu。
        Builds QMenu from registered menu items.

        Returns:
            构建好的 QMenu / Built QMenu
        """
        menu = QMenu()

        # 按顺序构建菜单项 / Build items in order
        for item_id in self._item_order:
            if item_id not in self._menu_items:
                continue

            item = self._menu_items[item_id]
            if not item.visible:
                continue

            self._build_menu_item(menu, item)

        return menu

    def _build_menu_item(
        self,
        menu: QMenu,
        item: MenuItem,
    ) -> Optional[QAction]:
        """
        构建单个菜单项
        Build single menu item

        递归构建菜单项和子菜单。
        Recursively builds menu item and submenus.

        Args:
            menu: 父菜单 / Parent menu
            item: 菜单项配置 / Menu item configuration

        Returns:
            创建的 QAction，子菜单返回 None / Created QAction, None for submenu
        """
        # 检查是否有动态子菜单 / Check for dynamic submenu
        if item.id in self._dynamic_providers:
            # 获取动态子项 / Get dynamic children
            provider = self._dynamic_providers[item.id]
            dynamic_children = provider()
            # 更新子项 / Update children
            item = MenuItem(
                id=item.id,
                text=item.text,
                icon=item.icon,
                shortcut=item.shortcut,
                callback=item.callback,
                enabled=item.enabled,
                visible=item.visible,
                children=dynamic_children,
                separator_after=item.separator_after,
            )

        # 如果有子菜单，创建子菜单 / If has children, create submenu
        if item.children:
            submenu = QMenu(item.text, menu)

            # 设置图标（如果有）/ Set icon if exists
            if item.icon:
                submenu.setIcon(QIcon(item.icon))

            # 递归构建子项 / Recursively build children
            for child in item.children:
                if child.visible:
                    self._build_menu_item(submenu, child)

            menu.addMenu(submenu)

            # 添加分隔线 / Add separator
            if item.separator_after:
                menu.addSeparator()

            return None

        # 创建 QAction / Create QAction
        action = QAction(item.text, menu)

        # 设置图标 / Set icon
        if item.icon:
            action.setIcon(QIcon(item.icon))

        # 设置快捷键 / Set shortcut
        if item.shortcut:
            action.setShortcut(item.shortcut)

        # 设置启用状态 / Set enabled state
        action.setEnabled(item.enabled)

        # 连接触发信号 / Connect triggered signal
        action.triggered.connect(
            lambda checked=False, item_id=item.id: self._on_action_triggered(item_id)
        )

        # 保存 QAction 引用 / Save QAction reference
        self._actions[item.id] = action

        menu.addAction(action)

        # 添加分隔线 / Add separator
        if item.separator_after:
            menu.addSeparator()

        return action

    def _on_action_triggered(self, item_id: str) -> None:
        """
        菜单项触发处理
        Menu action triggered handler

        调用菜单项的回调函数并发射信号。
        Calls menu item callback and emits signal.

        Args:
            item_id: 触发的菜单项 ID / Triggered menu item ID
        """
        # 发射信号 / Emit signal
        self.action_triggered.emit(item_id)

        # 调用回调函数（如果有）/ Call callback if exists
        if item_id in self._menu_items:
            item = self._menu_items[item_id]
            if item.callback:
                item.callback()

    def _on_menu_hidden(self) -> None:
        """
        菜单隐藏处理
        Menu hidden handler

        清理菜单资源并发射隐藏信号。
        Cleans up menu resources and emits hidden signal.
        """
        self.menu_hidden.emit()
