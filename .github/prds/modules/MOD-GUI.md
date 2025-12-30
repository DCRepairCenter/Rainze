# MOD-GUI - GUI界面模块

> **模块版本**: v1.1.0  
> **创建时间**: 2025-12-30  
> **最后更新**: 2025-12-30  
> **关联PRD**: PRD-Rainze.md v3.1.0 第一部分 §12, §14, §0.14  
> **关联技术栈**: TECH-Rainze.md v1.0.1 §3.3  
> **模块层级**: 应用层 (Application Layer)  
> **优先级**: P0 (核心必需)  
> **依赖模块**: Core (含contracts), State, Animation  
> **AI辅助**: Claude Opus 4

---

## 1. 模块概述

### 1.1 职责定义

| 维度 | 说明 |
|------|------|
| **核心职责** | 提供桌宠GUI界面，包括透明无边框窗口、系统托盘、聊天气泡、菜单系统 |
| **技术栈** | PySide6 (Qt6)、asyncio、QPropertyAnimation |
| **对外接口** | MainWindow、SystemTray、ChatBubble、MenuSystem |
| **依赖模块** | Core (事件总线)、State (状态读取)、Animation (动画播放) |
| **被依赖于** | 所有需要UI展示的模块 |

### 1.2 PRD映射

| PRD章节 | 内容概要 | 本模块覆盖 |
|---------|----------|------------|
| 0.14 动画系统架构 | 6层动画系统 | GUI窗口与动画层集成 |
| 第一部分 §12 | 基础物理与交互 | 拖拽、边缘吸附、重力 |
| 第一部分 §26 | 彩蛋与隐藏指令 | 显示模式切换 |
| 技术栈 §3.3 | PySide6选型 | 透明窗口实现 |

---

## 2. 目录结构

```
src/rainze/gui/
├── __init__.py
├── main_window.py       # 主窗口管理
├── transparent_widget.py # 透明窗口基类
├── system_tray.py       # 系统托盘
├── chat_bubble.py       # 聊天气泡
├── menu_system.py       # 右键菜单系统
├── input_panel.py       # 输入面板
├── dialog/              # 对话框
│   ├── __init__.py
│   ├── base_dialog.py   # 对话框基类
│   ├── settings_dialog.py
│   ├── schedule_dialog.py
│   ├── backpack_dialog.py
│   ├── history_dialog.py
│   └── shop_dialog.py
├── widgets/             # 自定义控件
│   ├── __init__.py
│   ├── clickable_label.py
│   ├── progress_ring.py
│   └── hover_button.py
├── styles/              # 样式管理
│   ├── __init__.py
│   ├── theme_manager.py
│   └── qss/
│       ├── dark.qss
│       └── light.qss
└── resources/           # Qt资源
    ├── icons/
    └── fonts/
```

---

## 3. 核心类设计

### 3.1 TransparentWidget - 透明窗口基类

```python
"""透明无边框窗口基类

职责:
- 提供透明背景、无边框窗口的基础实现
- 处理窗口拖拽逻辑
- 管理窗口层级和置顶状态
- 支持鼠标穿透设置

PRD映射:
- 技术栈 §3.3: PySide6透明窗口配置
- 第一部分 §12: 基础物理与交互
"""

from typing import Optional
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QMouseEvent


class TransparentWidget(QWidget):
    """透明无边框窗口基类
    
    Attributes:
        _drag_position: 拖拽起始位置
        _is_dragging: 是否正在拖拽
        _enable_drag: 是否启用拖拽
        _stay_on_top: 是否始终置顶
    
    Signals:
        drag_started: 开始拖拽信号
        drag_ended: 结束拖拽信号(final_position)
        position_changed: 位置变化信号(new_position)
    """
    
    # 信号定义
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
        """初始化透明窗口
        
        Args:
            parent: 父窗口
            enable_drag: 是否启用拖拽，默认True
            stay_on_top: 是否始终置顶，默认True
            enable_transparency: 是否启用透明，默认True
        """
        ...
    
    def setup_window_flags(self, stay_on_top: bool) -> None:
        """设置窗口标志
        
        配置: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        
        Args:
            stay_on_top: 是否置顶
        """
        ...
    
    def setup_transparency(self) -> None:
        """设置透明背景
        
        配置: Qt.WA_TranslucentBackground
        """
        ...
    
    def set_mouse_passthrough(self, enable: bool) -> None:
        """设置鼠标穿透
        
        Args:
            enable: 是否启用穿透(Qt.WA_TransparentForMouseEvents)
        """
        ...
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """鼠标按下事件处理
        
        记录拖拽起始位置，发射drag_started信号
        """
        ...
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """鼠标移动事件处理
        
        计算偏移量，移动窗口，发射position_changed信号
        """
        ...
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """鼠标释放事件处理
        
        结束拖拽，发射drag_ended信号
        """
        ...
    
    def snap_to_edge(self, position: QPoint, threshold: int = 50) -> QPoint:
        """边缘吸附计算
        
        Args:
            position: 当前位置
            threshold: 吸附阈值(像素)
            
        Returns:
            吸附后的位置
        """
        ...
    
    def get_screen_geometry(self) -> "QRect":
        """获取当前屏幕几何信息
        
        Returns:
            屏幕矩形区域
        """
        ...
```

### 3.2 MainWindow - 主窗口

```python
"""桌宠主窗口

职责:
- 管理桌宠的主显示窗口
- 整合动画渲染层和交互层
- 处理显示模式切换(悬浮/任务栏)
- 管理边缘吸附和重力模拟

PRD映射:
- 第一部分 §12: 基础物理与交互
- 第一部分 §26: 显示模式切换
- 0.14 动画系统架构: 与动画层集成
"""

from typing import TYPE_CHECKING, Optional
from PySide6.QtCore import Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap

from .transparent_widget import TransparentWidget

if TYPE_CHECKING:
    from rainze.animation import AnimationController
    from rainze.core import EventBus


class DisplayMode:
    """显示模式枚举"""
    FLOATING = "floating"          # 悬浮模式
    TASKBAR_WALK = "taskbar_walk"  # 任务栏行走模式


class EdgePosition:
    """边缘位置枚举"""
    NONE = "none"
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"


class MainWindow(TransparentWidget):
    """桌宠主窗口
    
    Attributes:
        _display_mode: 当前显示模式
        _animation_controller: 动画控制器引用
        _event_bus: 事件总线引用
        _pet_label: 桌宠图像标签
        _edge_position: 当前吸附边缘
        _gravity_timer: 重力模拟定时器
        _walk_timer: 任务栏行走定时器
        
    Signals:
        display_mode_changed: 显示模式变化(mode)
        edge_snapped: 边缘吸附(edge_position)
        pet_clicked: 桌宠被点击
        pet_double_clicked: 桌宠被双击
        pet_right_clicked: 桌宠被右键点击(position)
    """
    
    display_mode_changed: Signal = Signal(str)
    edge_snapped: Signal = Signal(str)
    pet_clicked: Signal = Signal()
    pet_double_clicked: Signal = Signal()
    pet_right_clicked: Signal = Signal(object)  # QPoint
    
    def __init__(
        self,
        event_bus: "EventBus",
        animation_controller: "AnimationController",
        parent: Optional["QWidget"] = None,
    ) -> None:
        """初始化主窗口
        
        Args:
            event_bus: 事件总线实例
            animation_controller: 动画控制器实例
            parent: 父窗口
        """
        ...
    
    def setup_ui(self) -> None:
        """初始化UI组件
        
        创建桌宠图像标签，设置初始大小和位置
        """
        ...
    
    def setup_physics(self) -> None:
        """初始化物理系统
        
        配置重力定时器和边缘检测
        """
        ...
    
    def set_display_mode(self, mode: str) -> None:
        """切换显示模式
        
        Args:
            mode: DisplayMode.FLOATING 或 DisplayMode.TASKBAR_WALK
        """
        ...
    
    def toggle_display_mode(self) -> None:
        """切换显示模式(在两种模式间切换)"""
        ...
    
    # === 动画集成 ===
    
    def update_frame(self, pixmap: QPixmap) -> None:
        """更新动画帧
        
        由AnimationController调用，更新显示的图像
        
        Args:
            pixmap: 新的帧图像
        """
        ...
    
    def set_pet_size(self, width: int, height: int) -> None:
        """设置桌宠尺寸
        
        Args:
            width: 宽度
            height: 高度
        """
        ...
    
    # === 物理模拟 ===
    
    def _on_gravity_tick(self) -> None:
        """重力模拟tick
        
        悬浮模式下，如果不在边缘吸附状态，模拟下落到任务栏上方
        """
        ...
    
    def _start_fall_animation(self, target_y: int) -> None:
        """开始下落动画
        
        Args:
            target_y: 目标Y坐标
        """
        ...
    
    def _check_edge_snap(self, position: "QPoint") -> Optional[str]:
        """检查是否需要边缘吸附
        
        Args:
            position: 当前位置
            
        Returns:
            吸附的边缘位置，无需吸附返回None
        """
        ...
    
    def _apply_edge_snap(self, edge: str, position: "QPoint") -> "QPoint":
        """应用边缘吸附
        
        Args:
            edge: 边缘位置
            position: 当前位置
            
        Returns:
            吸附后的位置
        """
        ...
    
    # === 任务栏行走 ===
    
    def _start_taskbar_walk(self) -> None:
        """开始任务栏行走模式"""
        ...
    
    def _stop_taskbar_walk(self) -> None:
        """停止任务栏行走模式"""
        ...
    
    def _on_walk_tick(self) -> None:
        """行走tick
        
        随机决定是否移动，以及移动方向
        """
        ...
    
    # === 交互事件 ===
    
    def mouseDoubleClickEvent(self, event: "QMouseEvent") -> None:
        """双击事件处理"""
        ...
    
    def contextMenuEvent(self, event: "QContextMenuEvent") -> None:
        """右键菜单事件处理"""
        ...
    
    # === 拖拽覆盖 ===
    
    def mouseReleaseEvent(self, event: "QMouseEvent") -> None:
        """鼠标释放事件
        
        覆盖父类，处理边缘吸附和表情切换
        """
        ...
    
    def _on_drag_end(self, position: "QPoint") -> None:
        """拖拽结束处理
        
        检查边缘吸附，切换攀爬表情
        """
        ...
    
    # === 状态保存/恢复 ===
    
    def save_position(self) -> dict:
        """保存窗口位置
        
        Returns:
            位置信息字典 {"x": int, "y": int, "mode": str, "edge": str}
        """
        ...
    
    def restore_position(self, data: dict) -> None:
        """恢复窗口位置
        
        Args:
            data: save_position返回的字典
        """
        ...
```

### 3.3 SystemTray - 系统托盘

```python
"""系统托盘管理

职责:
- 管理系统托盘图标和菜单
- 提供快速操作入口
- 处理托盘事件(单击、双击)
- 支持托盘通知

PRD映射:
- 第一部分功能: 系统托盘快捷操作
"""

from typing import TYPE_CHECKING, Optional, Callable
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Signal, QObject

if TYPE_CHECKING:
    from rainze.core import EventBus


class SystemTray(QObject):
    """系统托盘管理器
    
    Attributes:
        _tray_icon: 系统托盘图标
        _tray_menu: 托盘右键菜单
        _event_bus: 事件总线引用
        
    Signals:
        activated: 托盘图标被激活(activation_reason)
        show_requested: 请求显示主窗口
        hide_requested: 请求隐藏主窗口
        quit_requested: 请求退出程序
    """
    
    activated: Signal = Signal(int)
    show_requested: Signal = Signal()
    hide_requested: Signal = Signal()
    quit_requested: Signal = Signal()
    
    def __init__(
        self,
        event_bus: "EventBus",
        parent: Optional[QObject] = None,
    ) -> None:
        """初始化系统托盘
        
        Args:
            event_bus: 事件总线实例
            parent: 父对象
        """
        ...
    
    def setup_tray_icon(self) -> None:
        """设置托盘图标"""
        ...
    
    def setup_tray_menu(self) -> None:
        """设置托盘菜单
        
        菜单项:
        - 显示/隐藏
        - 免打扰模式
        - 分隔线
        - 设置
        - 关于
        - 分隔线
        - 退出
        """
        ...
    
    def add_menu_action(
        self,
        text: str,
        callback: Callable[[], None],
        icon: Optional[QIcon] = None,
        shortcut: Optional[str] = None,
    ) -> QAction:
        """添加菜单项
        
        Args:
            text: 菜单文本
            callback: 点击回调
            icon: 图标(可选)
            shortcut: 快捷键(可选)
            
        Returns:
            创建的QAction
        """
        ...
    
    def add_separator(self) -> None:
        """添加分隔线"""
        ...
    
    def show_notification(
        self,
        title: str,
        message: str,
        icon: "QSystemTrayIcon.MessageIcon" = QSystemTrayIcon.Information,
        duration_ms: int = 3000,
    ) -> None:
        """显示托盘通知
        
        Args:
            title: 通知标题
            message: 通知内容
            icon: 图标类型
            duration_ms: 显示时长(毫秒)
        """
        ...
    
    def set_icon(self, icon_path: str) -> None:
        """设置托盘图标
        
        Args:
            icon_path: 图标文件路径
        """
        ...
    
    def set_tooltip(self, text: str) -> None:
        """设置托盘提示文本
        
        Args:
            text: 提示文本
        """
        ...
    
    def _on_activated(self, reason: "QSystemTrayIcon.ActivationReason") -> None:
        """托盘激活事件处理
        
        - 单击: 显示/隐藏窗口
        - 双击: 打开设置
        """
        ...
    
    def show(self) -> None:
        """显示托盘图标"""
        ...
    
    def hide(self) -> None:
        """隐藏托盘图标"""
        ...
```

### 3.4 ChatBubble - 聊天气泡

```python
"""聊天气泡组件

职责:
- 显示桌宠的对话文本
- 支持打字机效果
- 支持表情符号和富文本
- 自动调整大小和位置
- 支持反馈按钮(可选)

PRD映射:
- 0.11 用户反馈循环: 显式反馈按钮
- 0.3 混合响应策略: 文本显示
"""

from typing import TYPE_CHECKING, Optional, Callable
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Signal, QTimer, QPropertyAnimation, Qt
from PySide6.QtGui import QFont

if TYPE_CHECKING:
    from PySide6.QtCore import QPoint


class ChatBubble(QWidget):
    """聊天气泡组件
    
    Attributes:
        _text_label: 文本标签
        _like_button: 点赞按钮(可选)
        _dislike_button: 点踩按钮(可选)
        _typing_timer: 打字机效果定时器
        _auto_hide_timer: 自动隐藏定时器
        _current_text: 当前完整文本
        _displayed_chars: 已显示字符数
        
    Signals:
        typing_started: 开始打字效果
        typing_finished: 打字效果完成
        feedback_given: 用户给出反馈(is_positive)
        bubble_clicked: 气泡被点击
        hidden: 气泡隐藏
    """
    
    typing_started: Signal = Signal()
    typing_finished: Signal = Signal()
    feedback_given: Signal = Signal(bool)
    bubble_clicked: Signal = Signal()
    hidden: Signal = Signal()
    
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        show_feedback_buttons: bool = False,
        auto_hide_ms: int = 10000,
        typing_speed_ms: int = 50,
    ) -> None:
        """初始化聊天气泡
        
        Args:
            parent: 父窗口
            show_feedback_buttons: 是否显示反馈按钮
            auto_hide_ms: 自动隐藏时间(毫秒)，0表示不自动隐藏
            typing_speed_ms: 打字机效果速度(毫秒/字符)
        """
        ...
    
    def setup_ui(self) -> None:
        """初始化UI布局"""
        ...
    
    def setup_style(self) -> None:
        """设置气泡样式
        
        - 圆角背景
        - 半透明效果
        - 阴影效果
        """
        ...
    
    def show_text(
        self,
        text: str,
        *,
        use_typing_effect: bool = True,
        anchor_point: Optional["QPoint"] = None,
    ) -> None:
        """显示文本
        
        Args:
            text: 要显示的文本
            use_typing_effect: 是否使用打字机效果
            anchor_point: 锚点位置(气泡尾巴指向的点)
        """
        ...
    
    def _start_typing_effect(self, text: str) -> None:
        """开始打字机效果
        
        Args:
            text: 完整文本
        """
        ...
    
    def _on_typing_tick(self) -> None:
        """打字机效果tick"""
        ...
    
    def _finish_typing(self) -> None:
        """完成打字效果"""
        ...
    
    def skip_typing(self) -> None:
        """跳过打字效果，直接显示完整文本"""
        ...
    
    def update_position(self, anchor: "QPoint") -> None:
        """更新气泡位置
        
        根据锚点位置和屏幕边界调整气泡位置
        
        Args:
            anchor: 锚点位置
        """
        ...
    
    def set_auto_hide(self, duration_ms: int) -> None:
        """设置自动隐藏时间
        
        Args:
            duration_ms: 毫秒，0表示不自动隐藏
        """
        ...
    
    def _start_auto_hide_timer(self) -> None:
        """启动自动隐藏定时器"""
        ...
    
    def _on_auto_hide(self) -> None:
        """自动隐藏回调"""
        ...
    
    def _on_like_clicked(self) -> None:
        """点赞按钮点击"""
        ...
    
    def _on_dislike_clicked(self) -> None:
        """点踩按钮点击"""
        ...
    
    def fade_in(self, duration_ms: int = 200) -> None:
        """淡入动画
        
        Args:
            duration_ms: 动画时长
        """
        ...
    
    def fade_out(self, duration_ms: int = 200) -> None:
        """淡出动画
        
        Args:
            duration_ms: 动画时长
        """
        ...
    
    def clear(self) -> None:
        """清空文本并隐藏"""
        ...
```

### 3.5 MenuSystem - 右键菜单系统

```python
"""右键菜单系统

职责:
- 管理桌宠右键菜单
- 支持动态菜单项
- 支持子菜单
- 集成各功能入口

PRD映射:
- 第一部分多个功能: 右键菜单入口
- §16 程序快速启动器: 管家服务子菜单
- §17 网站快捷访问: 书签子菜单
"""

from typing import TYPE_CHECKING, Optional, List, Dict, Callable, Any
from dataclasses import dataclass, field
from PySide6.QtWidgets import QMenu, QAction
from PySide6.QtGui import QIcon
from PySide6.QtCore import Signal, QObject

if TYPE_CHECKING:
    from PySide6.QtCore import QPoint
    from rainze.core import EventBus


@dataclass
class MenuItem:
    """菜单项配置
    
    Attributes:
        id: 菜单项ID
        text: 显示文本
        icon: 图标路径(可选)
        shortcut: 快捷键(可选)
        callback: 点击回调(可选)
        enabled: 是否启用
        visible: 是否可见
        children: 子菜单项
        separator_after: 是否在后面添加分隔线
    """
    id: str
    text: str
    icon: Optional[str] = None
    shortcut: Optional[str] = None
    callback: Optional[Callable[[], None]] = None
    enabled: bool = True
    visible: bool = True
    children: List["MenuItem"] = field(default_factory=list)
    separator_after: bool = False


class MenuSystem(QObject):
    """右键菜单系统
    
    Attributes:
        _menu: 主菜单
        _menu_items: 注册的菜单项
        _actions: QAction映射
        _event_bus: 事件总线引用
        
    Signals:
        menu_shown: 菜单显示
        menu_hidden: 菜单隐藏
        action_triggered: 菜单项触发(item_id)
    """
    
    menu_shown: Signal = Signal()
    menu_hidden: Signal = Signal()
    action_triggered: Signal = Signal(str)
    
    def __init__(
        self,
        event_bus: "EventBus",
        parent: Optional[QObject] = None,
    ) -> None:
        """初始化菜单系统
        
        Args:
            event_bus: 事件总线实例
            parent: 父对象
        """
        ...
    
    def setup_default_menu(self) -> None:
        """设置默认菜单结构
        
        默认菜单:
        - 聊天
        - 背包
        - 日程管理
        - 管家服务 (子菜单)
        - 书签 (子菜单)
        - 小游戏 (子菜单)
        - 分隔线
        - 历史记录
        - 记一笔
        - 生成观察日记
        - 分隔线
        - 用户档案
        - 设置
        - 帮助
        - 分隔线
        - 退出
        """
        ...
    
    def register_item(self, item: MenuItem) -> None:
        """注册菜单项
        
        Args:
            item: 菜单项配置
        """
        ...
    
    def unregister_item(self, item_id: str) -> None:
        """注销菜单项
        
        Args:
            item_id: 菜单项ID
        """
        ...
    
    def update_item(
        self,
        item_id: str,
        *,
        text: Optional[str] = None,
        enabled: Optional[bool] = None,
        visible: Optional[bool] = None,
    ) -> None:
        """更新菜单项属性
        
        Args:
            item_id: 菜单项ID
            text: 新文本(可选)
            enabled: 是否启用(可选)
            visible: 是否可见(可选)
        """
        ...
    
    def add_dynamic_submenu(
        self,
        parent_id: str,
        submenu_id: str,
        text: str,
        items_provider: Callable[[], List[MenuItem]],
    ) -> None:
        """添加动态子菜单
        
        Args:
            parent_id: 父菜单项ID
            submenu_id: 子菜单ID
            text: 子菜单显示文本
            items_provider: 子菜单项提供函数(显示时调用)
        """
        ...
    
    def show_at(self, position: "QPoint") -> None:
        """在指定位置显示菜单
        
        Args:
            position: 显示位置(屏幕坐标)
        """
        ...
    
    def _build_menu(self) -> QMenu:
        """构建菜单
        
        Returns:
            构建好的QMenu
        """
        ...
    
    def _build_menu_item(
        self,
        menu: QMenu,
        item: MenuItem,
    ) -> Optional[QAction]:
        """构建单个菜单项
        
        Args:
            menu: 父菜单
            item: 菜单项配置
            
        Returns:
            创建的QAction，子菜单返回None
        """
        ...
    
    def _on_action_triggered(self, item_id: str) -> None:
        """菜单项触发处理
        
        Args:
            item_id: 触发的菜单项ID
        """
        ...
```

### 3.6 InputPanel - 输入面板

```python
"""输入面板组件

职责:
- 提供文本输入框
- 支持快捷键发送
- 支持输入历史
- 与聊天系统集成

PRD映射:
- 0.5b 用户主动对话场景: 输入框触发方式
"""

from typing import TYPE_CHECKING, Optional, List
from PySide6.QtWidgets import QWidget, QLineEdit, QPushButton, QHBoxLayout
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QKeyEvent

if TYPE_CHECKING:
    from rainze.core import EventBus


class InputPanel(QWidget):
    """输入面板
    
    Attributes:
        _input_field: 输入框
        _send_button: 发送按钮
        _history: 输入历史
        _history_index: 历史索引
        _event_bus: 事件总线引用
        
    Signals:
        message_submitted: 消息提交(text)
        input_changed: 输入内容变化(text)
        panel_shown: 面板显示
        panel_hidden: 面板隐藏
    """
    
    message_submitted: Signal = Signal(str)
    input_changed: Signal = Signal(str)
    panel_shown: Signal = Signal()
    panel_hidden: Signal = Signal()
    
    def __init__(
        self,
        event_bus: "EventBus",
        parent: Optional[QWidget] = None,
        *,
        max_history: int = 50,
    ) -> None:
        """初始化输入面板
        
        Args:
            event_bus: 事件总线实例
            parent: 父窗口
            max_history: 最大历史记录数
        """
        ...
    
    def setup_ui(self) -> None:
        """初始化UI布局"""
        ...
    
    def setup_style(self) -> None:
        """设置样式"""
        ...
    
    def set_placeholder(self, text: str) -> None:
        """设置占位文本
        
        Args:
            text: 占位文本
        """
        ...
    
    def set_max_length(self, length: int) -> None:
        """设置最大输入长度
        
        Args:
            length: 最大字符数
        """
        ...
    
    def get_text(self) -> str:
        """获取输入文本
        
        Returns:
            当前输入的文本
        """
        ...
    
    def set_text(self, text: str) -> None:
        """设置输入文本
        
        Args:
            text: 文本内容
        """
        ...
    
    def clear(self) -> None:
        """清空输入框"""
        ...
    
    def focus(self) -> None:
        """聚焦输入框"""
        ...
    
    def _on_send_clicked(self) -> None:
        """发送按钮点击处理"""
        ...
    
    def _submit_message(self) -> None:
        """提交消息
        
        验证输入 -> 添加到历史 -> 发射信号 -> 清空输入框
        """
        ...
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """键盘事件处理
        
        - Enter: 提交
        - Up/Down: 浏览历史
        - Escape: 隐藏面板
        """
        ...
    
    def _navigate_history(self, direction: int) -> None:
        """浏览历史记录
        
        Args:
            direction: -1向上(更早)，1向下(更近)
        """
        ...
    
    def _add_to_history(self, text: str) -> None:
        """添加到历史记录
        
        Args:
            text: 输入的文本
        """
        ...
    
    def show_panel(self, anchor: Optional["QPoint"] = None) -> None:
        """显示输入面板
        
        Args:
            anchor: 锚点位置(可选)
        """
        ...
    
    def hide_panel(self) -> None:
        """隐藏输入面板"""
        ...
    
    def toggle_panel(self) -> None:
        """切换面板显示状态"""
        ...
```

### 3.7 ThemeManager - 主题管理器

```python
"""主题管理器

职责:
- 管理应用主题(深色/浅色)
- 加载和应用QSS样式
- 支持主题切换动画
"""

from typing import TYPE_CHECKING, Optional, Dict
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Signal, QObject

if TYPE_CHECKING:
    pass


class Theme:
    """主题枚举"""
    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"


class ThemeManager(QObject):
    """主题管理器
    
    Attributes:
        _current_theme: 当前主题
        _theme_cache: 主题样式缓存
        _qss_dir: QSS文件目录
        
    Signals:
        theme_changed: 主题变化(theme_name)
    """
    
    theme_changed: Signal = Signal(str)
    
    def __init__(
        self,
        qss_dir: Optional[Path] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        """初始化主题管理器
        
        Args:
            qss_dir: QSS文件目录，默认使用内置目录
            parent: 父对象
        """
        ...
    
    def get_current_theme(self) -> str:
        """获取当前主题
        
        Returns:
            当前主题名称
        """
        ...
    
    def set_theme(self, theme: str) -> None:
        """设置主题
        
        Args:
            theme: 主题名称(Theme.DARK/LIGHT/SYSTEM)
        """
        ...
    
    def toggle_theme(self) -> None:
        """切换主题(深色/浅色之间切换)"""
        ...
    
    def _load_qss(self, theme: str) -> str:
        """加载QSS样式文件
        
        Args:
            theme: 主题名称
            
        Returns:
            QSS样式字符串
        """
        ...
    
    def _apply_qss(self, qss: str) -> None:
        """应用QSS样式
        
        Args:
            qss: QSS样式字符串
        """
        ...
    
    def _detect_system_theme(self) -> str:
        """检测系统主题
        
        Returns:
            Theme.DARK 或 Theme.LIGHT
        """
        ...
    
    def get_color(self, color_name: str) -> str:
        """获取主题颜色
        
        Args:
            color_name: 颜色名称
            
        Returns:
            颜色值(如 "#FFFFFF")
        """
        ...
```

---

## 4. 对话框设计

### 4.1 BaseDialog - 对话框基类

```python
"""对话框基类

职责:
- 提供统一的对话框样式
- 处理对话框动画
- 管理对话框生命周期
"""

from typing import Optional
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal, Qt


class BaseDialog(QDialog):
    """对话框基类
    
    Attributes:
        _title_label: 标题标签
        _content_layout: 内容布局
        _button_layout: 按钮布局
        
    Signals:
        dialog_shown: 对话框显示
        dialog_closed: 对话框关闭(result)
    """
    
    dialog_shown: Signal = Signal()
    dialog_closed: Signal = Signal(int)
    
    def __init__(
        self,
        title: str,
        parent: Optional["QWidget"] = None,
        *,
        width: int = 400,
        height: int = 300,
        modal: bool = True,
    ) -> None:
        """初始化对话框
        
        Args:
            title: 对话框标题
            parent: 父窗口
            width: 宽度
            height: 高度
            modal: 是否模态
        """
        ...
    
    def setup_base_ui(self) -> None:
        """设置基础UI布局"""
        ...
    
    def setup_content(self) -> None:
        """设置内容区域 - 子类重写"""
        ...
    
    def add_button(
        self,
        text: str,
        callback: "Callable[[], None]",
        *,
        primary: bool = False,
    ) -> QPushButton:
        """添加底部按钮
        
        Args:
            text: 按钮文本
            callback: 点击回调
            primary: 是否主按钮
            
        Returns:
            创建的按钮
        """
        ...
    
    def show_animated(self) -> None:
        """带动画显示"""
        ...
    
    def close_animated(self, result: int = 0) -> None:
        """带动画关闭
        
        Args:
            result: 对话框结果
        """
        ...
```

### 4.2 特定对话框概要

```python
# SettingsDialog - 设置对话框
class SettingsDialog(BaseDialog):
    """设置对话框，包含多个设置Tab"""
    ...

# ScheduleDialog - 日程对话框  
class ScheduleDialog(BaseDialog):
    """日程管理对话框，支持添加/编辑/删除日程"""
    ...

# BackpackDialog - 背包对话框
class BackpackDialog(BaseDialog):
    """背包对话框，显示物品网格"""
    ...

# HistoryDialog - 历史记录对话框
class HistoryDialog(BaseDialog):
    """聊天历史对话框，支持搜索和删除"""
    ...

# ShopDialog - 商城对话框
class ShopDialog(BaseDialog):
    """商城对话框，商品列表和购买"""
    ...
```

---

## 5. 配置文件

### 5.1 gui_settings.json

```json
{
  "window": {
    "default_width": 200,
    "default_height": 200,
    "default_position": "bottom_right",
    "stay_on_top": true,
    "enable_transparency": true,
    "opacity": 1.0
  },
  
  "physics": {
    "enable_gravity": true,
    "gravity_acceleration": 9.8,
    "fall_animation_ms": 500,
    "edge_snap_distance_px": 50,
    "edge_snap_enabled": true,
    "bounce_on_land": true,
    "bounce_height_px": 10
  },
  
  "display_mode": {
    "default_mode": "floating",
    "mode_switch_hotkey": "Ctrl+Shift+M",
    "taskbar_walk": {
      "walk_speed_px_per_sec": 30,
      "idle_before_walk_seconds": 10,
      "walk_probability": 0.5,
      "walk_direction_change_probability": 0.2,
      "enable_random_stops": true,
      "stop_duration_range": [3, 10]
    }
  },
  
  "drag": {
    "enable": true,
    "show_grabbed_expression": true,
    "grabbed_expression": "grabbed",
    "left_edge_expression": "climb_left",
    "right_edge_expression": "climb_right"
  },
  
  "chat_bubble": {
    "show_feedback_buttons": false,
    "auto_hide_ms": 10000,
    "typing_speed_ms": 50,
    "max_width": 300,
    "opacity": 0.95,
    "corner_radius": 10
  },
  
  "input_panel": {
    "max_input_length": 500,
    "max_history": 50,
    "placeholder": "和我聊聊吧~",
    "show_send_button": true
  },
  
  "theme": {
    "default_theme": "dark",
    "follow_system": false
  },
  
  "system_tray": {
    "enable": true,
    "show_notifications": true,
    "notification_duration_ms": 3000,
    "minimize_to_tray_on_close": true
  }
}
```

---

## 6. 依赖关系图

```
┌─────────────────────────────────────────────────────────────────┐
│                          GUI Module                              │
│                                                                  │
│  ┌──────────────────┐         ┌──────────────────┐             │
│  │   MainWindow     │◄───────►│ TransparentWidget │             │
│  └────────┬─────────┘         └──────────────────┘             │
│           │                                                      │
│           ▼                                                      │
│  ┌──────────────────┐  ┌────────────┐  ┌────────────────┐      │
│  │   ChatBubble     │  │ InputPanel │  │  MenuSystem    │      │
│  └──────────────────┘  └────────────┘  └────────────────┘      │
│           │                    │               │                 │
│           └────────────────────┼───────────────┘                │
│                                │                                 │
│  ┌──────────────────┐  ┌──────▼───────┐  ┌────────────────┐   │
│  │   SystemTray     │  │ ThemeManager │  │    Dialogs     │   │
│  └──────────────────┘  └──────────────┘  └────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
          │                       │                    │
          ▼                       ▼                    ▼
    ┌──────────┐           ┌──────────┐         ┌──────────┐
    │   Core   │           │  State   │         │Animation │
    │(EventBus)│           │(状态读取)│         │(动画控制)│
    └──────────┘           └──────────┘         └──────────┘
```

---

## 7. PRD章节映射

| PRD章节 | 本模块实现 |
|---------|------------|
| 0.14 动画系统架构 | MainWindow.update_frame() 与动画层集成 |
| 第一部分 §1 聊天记录 | HistoryDialog |
| 第一部分 §3 核心人设修改 | SettingsDialog |
| 第一部分 §4 个人档案 | SettingsDialog (ProfileTab) |
| 第一部分 §7 喂食与背包 | BackpackDialog |
| 第一部分 §9 日程提醒 | ScheduleDialog |
| 第一部分 §12 基础物理交互 | MainWindow 物理模拟 |
| 第一部分 §16 程序启动器 | MenuSystem (管家服务子菜单) |
| 第一部分 §17 网站书签 | MenuSystem (书签子菜单) |
| 第一部分 §20 商城系统 | ShopDialog |
| 第一部分 §24 便签 | InputPanel (快速记录模式) |
| 第一部分 §26 彩蛋 | MainWindow.toggle_display_mode() |
| 技术栈 §3.3 | PySide6 透明窗口实现 |

---

**文档版本历史**:

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0.0 | 2025-12-30 | 初始版本 |
