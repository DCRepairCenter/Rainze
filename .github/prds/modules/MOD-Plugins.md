# MOD-Plugins - 插件系统模块

> **模块版本**: v1.0.0
> **创建时间**: 2025-12-29
> **关联PRD**: PRD-Rainze.md v3.0.3 第三部分
> **关联技术栈**: TECH-Rainze.md v1.0.1
> **模块层级**: 应用层 (Application Layer)
> **优先级**: P2 (扩展能力)
> **依赖模块**: Core, AI, State, Tools

---

## 1. 模块概述

### 1.1 职责定义

| 维度 | 说明 |
|------|------|
| **核心职责** | 提供可扩展的插件架构，支持热加载/卸载、权限管理、沙箱隔离 |
| **技术栈** | Python动态导入、multiprocessing（可选沙箱）、JSON Schema |
| **对外接口** | PluginManager、PluginAPI、PluginSandbox |
| **依赖模块** | Core (事件总线)、AI (调用能力)、State (状态访问)、Tools (工具扩展) |
| **被依赖于** | 第三方插件、游戏插件、集成插件 |

### 1.2 插件类型定义

| 类型 | 标识 | 用途 | 示例 |
|------|------|------|------|
| game | `game` | 小游戏插件 | 猜拳、骰子、卡牌 |
| tool | `tool` | 工具插件 | 文件整理、翻译 |
| effect | `effect` | 特效插件 | 天气效果、节日特效 |
| integration | `integration` | 集成插件 | 音乐嗅探、日历同步 |
| custom | `custom` | 自定义插件 | 用户自定义功能 |

### 1.3 PRD映射

| PRD章节 | 内容概要 | 本模块覆盖 |
|---------|----------|------------|
| 第三部分 插件系统架构 | 插件类型、生命周期、API | ✅ 完整覆盖 |
| 第三部分 插件目录结构 | 目录组织规范 | ✅ 覆盖 |
| 第三部分 插件清单 | plugin.json规范 | ✅ 覆盖 |
| 第一部分 §18 | 猜拳与掷骰子 | 作为game插件实现 |

---

## 2. 目录结构

```
src/rainze/plugins/
├── __init__.py
├── manager.py              # PluginManager 插件管理器
├── loader.py               # PluginLoader 插件加载器
├── registry.py             # PluginRegistry 插件注册表
├── api/                    # 插件API
│   ├── __init__.py
│   ├── plugin_api.py       # PluginAPI 对外暴露的API
│   ├── pet_api.py          # PetAPI 宠物控制接口
│   ├── economy_api.py      # EconomyAPI 经济系统接口
│   ├── ui_api.py           # UIAPI 界面接口
│   ├── storage_api.py      # StorageAPI 存储接口
│   └── event_api.py        # EventAPI 事件接口
├── sandbox/                # 沙箱系统
│   ├── __init__.py
│   ├── executor.py         # SandboxExecutor 沙箱执行器
│   ├── permissions.py      # PermissionManager 权限管理
│   └── resource_limit.py   # ResourceLimiter 资源限制
├── manifest/               # 清单解析
│   ├── __init__.py
│   ├── parser.py           # ManifestParser 清单解析器
│   └── validator.py        # ManifestValidator 清单验证器
├── builtin/                # 内置插件
│   ├── __init__.py
│   ├── games/
│   │   ├── __init__.py
│   │   ├── rock_paper_scissors.py
│   │   └── dice_roll.py
│   └── local_llm/          # 本地LLM插件
│       ├── __init__.py
│       └── fallback_llm.py
└── models/                 # 数据模型
    ├── __init__.py
    ├── plugin.py           # 插件数据模型
    ├── manifest.py         # 清单数据模型
    └── permission.py       # 权限数据模型
```

---

## 3. 核心类设计

### 3.1 PluginManager - 插件管理器

```python
"""插件管理器

统一管理所有插件的生命周期。

PRD映射: 第三部分 插件系统架构
"""

from typing import TYPE_CHECKING, Optional, Dict, List, Callable, Any
from pathlib import Path
from enum import Enum, auto
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from rainze.core import EventBus, ConfigManager


class PluginState(Enum):
    """插件状态"""
    UNLOADED = auto()       # 未加载
    LOADED = auto()         # 已加载
    ENABLED = auto()        # 已启用
    DISABLED = auto()       # 已禁用
    ERROR = auto()          # 错误状态


@dataclass
class PluginInfo:
    """插件信息"""
    id: str
    name: str
    version: str
    author: str
    description: str
    plugin_type: str
    entry: str
    state: PluginState
    path: Path
    permissions: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


class PluginManager:
    """插件管理器
    
    职责:
    - 扫描和发现插件
    - 管理插件生命周期
    - 提供插件API
    - 处理插件依赖
    
    Attributes:
        _plugins: 已注册插件映射 {id: PluginInfo}
        _instances: 插件实例映射 {id: PluginInstance}
        _plugin_dirs: 插件目录列表
        _event_bus: 事件总线引用
        _api: 插件API实例
    """
    
    def __init__(
        self,
        event_bus: "EventBus",
        config_manager: "ConfigManager",
        plugin_dirs: Optional[List[Path]] = None,
    ) -> None:
        """初始化插件管理器
        
        Args:
            event_bus: 事件总线实例
            config_manager: 配置管理器实例
            plugin_dirs: 插件目录列表，默认为 ["./plugins"]
        """
        ...
    
    async def initialize(self) -> None:
        """异步初始化
        
        - 扫描插件目录
        - 加载内置插件
        - 恢复已启用插件状态
        """
        ...
    
    # ==================== 插件发现 ====================
    
    async def scan_plugins(self) -> List[PluginInfo]:
        """扫描所有插件目录
        
        Returns:
            发现的插件信息列表
        """
        ...
    
    async def discover_plugin(self, path: Path) -> Optional[PluginInfo]:
        """发现单个插件
        
        Args:
            path: 插件目录路径
            
        Returns:
            插件信息，解析失败返回None
        """
        ...
    
    # ==================== 生命周期管理 ====================
    
    async def load_plugin(self, plugin_id: str) -> bool:
        """加载插件
        
        执行顺序:
        1. 验证清单
        2. 检查依赖
        3. 检查权限
        4. 导入模块
        5. 调用 onLoad 钩子
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            是否加载成功
            
        Raises:
            PluginNotFoundError: 插件不存在
            PluginDependencyError: 依赖不满足
            PluginPermissionError: 权限不足
        """
        ...
    
    async def unload_plugin(self, plugin_id: str) -> bool:
        """卸载插件
        
        执行顺序:
        1. 调用 onUnload 钩子
        2. 清理资源
        3. 移除模块
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            是否卸载成功
        """
        ...
    
    async def enable_plugin(self, plugin_id: str) -> bool:
        """启用插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            是否启用成功
        """
        ...
    
    async def disable_plugin(self, plugin_id: str) -> bool:
        """禁用插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            是否禁用成功
        """
        ...
    
    async def reload_plugin(self, plugin_id: str) -> bool:
        """重新加载插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            是否重载成功
        """
        ...
    
    # ==================== 插件查询 ====================
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginInfo]:
        """获取插件信息
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            插件信息
        """
        ...
    
    def list_plugins(
        self,
        plugin_type: Optional[str] = None,
        state: Optional[PluginState] = None,
    ) -> List[PluginInfo]:
        """列出插件
        
        Args:
            plugin_type: 按类型筛选
            state: 按状态筛选
            
        Returns:
            插件信息列表
        """
        ...
    
    def is_enabled(self, plugin_id: str) -> bool:
        """检查插件是否启用
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            是否启用
        """
        ...
    
    # ==================== 插件调用 ====================
    
    async def call_plugin_method(
        self,
        plugin_id: str,
        method: str,
        *args,
        **kwargs,
    ) -> Any:
        """调用插件方法
        
        Args:
            plugin_id: 插件ID
            method: 方法名
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            方法返回值
            
        Raises:
            PluginNotEnabledError: 插件未启用
            PluginMethodNotFoundError: 方法不存在
        """
        ...
    
    async def broadcast_event(
        self,
        event_name: str,
        event_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """向所有启用的插件广播事件
        
        Args:
            event_name: 事件名称
            event_data: 事件数据
            
        Returns:
            各插件的响应 {plugin_id: response}
        """
        ...
    
    # ==================== 插件API ====================
    
    def get_api(self) -> "PluginAPI":
        """获取插件API实例
        
        Returns:
            PluginAPI实例
        """
        ...


### 3.2 PluginAPI - 插件API

```python
"""插件API

提供给插件使用的安全API接口。

PRD映射: 第三部分 Plugin API
"""

from typing import TYPE_CHECKING, Optional, Dict, Any, List, Callable
from dataclasses import dataclass

if TYPE_CHECKING:
    from rainze.state import StateManager
    from rainze.gui import MainWindow


@dataclass
class DialogOptions:
    """对话框选项"""
    title: str
    content: str
    buttons: List[str] = None
    default_button: int = 0
    icon: Optional[str] = None


@dataclass
class MenuItemOptions:
    """菜单项选项"""
    label: str
    icon: Optional[str] = None
    shortcut: Optional[str] = None
    callback: Optional[Callable] = None


class PluginAPI:
    """插件API
    
    提供给插件调用的安全接口，所有操作都经过权限检查。
    
    使用示例:
    ```python
    # 在插件中使用
    async def on_enable(api: PluginAPI):
        await api.pet.say("插件已启用！")
        api.economy.add_coins(10)
    ```
    """
    
    def __init__(
        self,
        plugin_id: str,
        permissions: List[str],
        state_manager: "StateManager",
        main_window: "MainWindow",
    ) -> None:
        """初始化插件API
        
        Args:
            plugin_id: 插件ID（用于权限检查）
            permissions: 已授权权限列表
            state_manager: 状态管理器
            main_window: 主窗口
        """
        ...
    
    @property
    def pet(self) -> "PetAPI":
        """获取宠物控制API"""
        ...
    
    @property
    def economy(self) -> "EconomyAPI":
        """获取经济系统API"""
        ...
    
    @property
    def affinity(self) -> "AffinityAPI":
        """获取好感度API"""
        ...
    
    @property
    def ui(self) -> "UIAPI":
        """获取界面API"""
        ...
    
    @property
    def storage(self) -> "StorageAPI":
        """获取存储API"""
        ...
    
    @property
    def events(self) -> "EventAPI":
        """获取事件API"""
        ...


class PetAPI:
    """宠物控制API
    
    权限要求: pet.read, pet.write
    """
    
    async def say(self, message: str, emotion: Optional[str] = None) -> None:
        """让宠物说话
        
        Args:
            message: 说话内容
            emotion: 情感标签（可选）
            
        权限: pet.write
        """
        ...
    
    async def play_animation(self, name: str) -> bool:
        """播放动画
        
        Args:
            name: 动画名称
            
        Returns:
            是否播放成功
            
        权限: pet.write
        """
        ...
    
    async def set_expression(self, expression: str, duration_ms: int = 0) -> None:
        """设置表情
        
        Args:
            expression: 表情名称
            duration_ms: 持续时间，0表示持续
            
        权限: pet.write
        """
        ...
    
    def get_mood(self) -> str:
        """获取当前心情
        
        Returns:
            心情状态
            
        权限: pet.read
        """
        ...
    
    def get_energy(self) -> int:
        """获取当前能量
        
        Returns:
            能量值 (0-100)
            
        权限: pet.read
        """
        ...


class EconomyAPI:
    """经济系统API
    
    权限要求: economy.read, economy.write
    """
    
    def get_coins(self) -> int:
        """获取金币数量
        
        Returns:
            金币数量
            
        权限: economy.read
        """
        ...
    
    def add_coins(self, amount: int, reason: str = "") -> bool:
        """增加金币
        
        Args:
            amount: 增加数量
            reason: 原因（用于日志）
            
        Returns:
            是否成功
            
        权限: economy.write
        """
        ...
    
    def remove_coins(self, amount: int, reason: str = "") -> bool:
        """扣除金币
        
        Args:
            amount: 扣除数量
            reason: 原因
            
        Returns:
            是否成功（余额不足返回False）
            
        权限: economy.write
        """
        ...


class AffinityAPI:
    """好感度API
    
    权限要求: affinity.read, affinity.write
    """
    
    def get_affinity(self) -> int:
        """获取好感度
        
        Returns:
            好感度值
            
        权限: affinity.read
        """
        ...
    
    def get_level(self) -> int:
        """获取好感度等级
        
        Returns:
            等级 (1-5)
            
        权限: affinity.read
        """
        ...
    
    def add_affinity(self, amount: int, reason: str = "") -> None:
        """增加好感度
        
        Args:
            amount: 增加量
            reason: 原因
            
        权限: affinity.write
        """
        ...


class UIAPI:
    """界面API
    
    权限要求: ui.dialog, ui.menu, ui.notification
    """
    
    async def show_dialog(self, options: DialogOptions) -> int:
        """显示对话框
        
        Args:
            options: 对话框选项
            
        Returns:
            点击的按钮索引
            
        权限: ui.dialog
        """
        ...
    
    def show_menu(self, items: List[MenuItemOptions]) -> None:
        """显示菜单
        
        Args:
            items: 菜单项列表
            
        权限: ui.menu
        """
        ...
    
    def show_notification(self, title: str, message: str) -> None:
        """显示通知
        
        Args:
            title: 标题
            message: 内容
            
        权限: ui.notification
        """
        ...
    
    def show_toast(self, message: str, duration_ms: int = 3000) -> None:
        """显示Toast提示
        
        Args:
            message: 消息内容
            duration_ms: 显示时长
            
        权限: ui.notification
        """
        ...


class StorageAPI:
    """存储API
    
    权限要求: storage.read, storage.write
    
    注意: 每个插件有独立的存储空间
    """
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取存储值
        
        Args:
            key: 键名
            default: 默认值
            
        Returns:
            存储的值
            
        权限: storage.read
        """
        ...
    
    def set(self, key: str, value: Any) -> None:
        """设置存储值
        
        Args:
            key: 键名
            value: 值（必须可JSON序列化）
            
        权限: storage.write
        """
        ...
    
    def delete(self, key: str) -> bool:
        """删除存储值
        
        Args:
            key: 键名
            
        Returns:
            是否存在并删除
            
        权限: storage.write
        """
        ...
    
    def list_keys(self) -> List[str]:
        """列出所有键
        
        Returns:
            键名列表
            
        权限: storage.read
        """
        ...


class EventAPI:
    """事件API
    
    权限要求: events.subscribe, events.emit
    """
    
    def on(
        self,
        event_name: str,
        handler: Callable[[Dict[str, Any]], None],
    ) -> Callable[[], None]:
        """订阅事件
        
        Args:
            event_name: 事件名称
            handler: 事件处理函数
            
        Returns:
            取消订阅的函数
            
        权限: events.subscribe
        """
        ...
    
    def emit(self, event_name: str, data: Dict[str, Any]) -> None:
        """发射事件
        
        Args:
            event_name: 事件名称
            data: 事件数据
            
        权限: events.emit
        """
        ...
```

### 3.3 PluginBase - 插件基类

```python
"""插件基类

所有插件必须继承此类。
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, Dict, Any

if TYPE_CHECKING:
    from .api import PluginAPI


class PluginBase(ABC):
    """插件基类
    
    插件开发者需要继承此类并实现相关方法。
    
    生命周期钩子:
    - on_load: 插件加载时调用
    - on_enable: 插件启用时调用
    - on_disable: 插件禁用时调用
    - on_unload: 插件卸载时调用
    - on_update: 定时更新时调用（可选）
    
    示例:
    ```python
    class MyPlugin(PluginBase):
        @property
        def id(self) -> str:
            return "my_plugin"
        
        async def on_enable(self, api: PluginAPI) -> None:
            await api.pet.say("我的插件启用了！")
    ```
    """
    
    @property
    @abstractmethod
    def id(self) -> str:
        """插件唯一标识"""
        ...
    
    @property
    def name(self) -> str:
        """插件显示名称（默认为id）"""
        return self.id
    
    @property
    def version(self) -> str:
        """插件版本"""
        return "1.0.0"
    
    @property
    def description(self) -> str:
        """插件描述"""
        return ""
    
    # ==================== 生命周期钩子 ====================
    
    async def on_load(self) -> None:
        """插件加载时调用
        
        此时还没有API访问权限，仅用于初始化内部状态。
        """
        pass
    
    async def on_enable(self, api: "PluginAPI") -> None:
        """插件启用时调用
        
        Args:
            api: 插件API实例
        """
        pass
    
    async def on_disable(self) -> None:
        """插件禁用时调用
        
        应在此处清理资源。
        """
        pass
    
    async def on_unload(self) -> None:
        """插件卸载时调用
        
        最后的清理机会。
        """
        pass
    
    async def on_update(self, delta_time: float) -> None:
        """定时更新回调（可选）
        
        Args:
            delta_time: 距上次更新的时间（秒）
            
        注意: 需要在plugin.json中声明update_interval
        """
        pass
    
    # ==================== 事件处理 ====================
    
    async def on_event(self, event_name: str, event_data: Dict[str, Any]) -> Optional[Any]:
        """事件处理回调
        
        Args:
            event_name: 事件名称
            event_data: 事件数据
            
        Returns:
            可选的响应数据
        """
        return None


### 3.4 PermissionManager - 权限管理

```python
"""权限管理

管理插件权限的检查和授权。
"""

from typing import Dict, List, Set, Optional
from enum import Enum, auto
from dataclasses import dataclass


class PermissionLevel(Enum):
    """权限级别"""
    NONE = auto()           # 无权限
    READ = auto()           # 只读
    WRITE = auto()          # 读写
    ADMIN = auto()          # 管理员


@dataclass
class Permission:
    """权限定义"""
    name: str               # 权限名称，如 "economy.write"
    level: PermissionLevel
    description: str
    dangerous: bool = False # 是否为危险权限
    requires_confirm: bool = False  # 是否需要用户确认


# 预定义权限列表
BUILTIN_PERMISSIONS: Dict[str, Permission] = {
    "pet.read": Permission("pet.read", PermissionLevel.READ, "读取宠物状态"),
    "pet.write": Permission("pet.write", PermissionLevel.WRITE, "控制宠物行为"),
    "economy.read": Permission("economy.read", PermissionLevel.READ, "读取金币数量"),
    "economy.write": Permission("economy.write", PermissionLevel.WRITE, "修改金币数量"),
    "affinity.read": Permission("affinity.read", PermissionLevel.READ, "读取好感度"),
    "affinity.write": Permission("affinity.write", PermissionLevel.WRITE, "修改好感度"),
    "ui.dialog": Permission("ui.dialog", PermissionLevel.WRITE, "显示对话框"),
    "ui.menu": Permission("ui.menu", PermissionLevel.WRITE, "添加菜单项"),
    "ui.notification": Permission("ui.notification", PermissionLevel.WRITE, "显示通知"),
    "storage.read": Permission("storage.read", PermissionLevel.READ, "读取插件存储"),
    "storage.write": Permission("storage.write", PermissionLevel.WRITE, "写入插件存储"),
    "events.subscribe": Permission("events.subscribe", PermissionLevel.READ, "订阅事件"),
    "events.emit": Permission("events.emit", PermissionLevel.WRITE, "发射事件"),
    "system.read": Permission("system.read", PermissionLevel.READ, "读取系统信息"),
    "system.write": Permission("system.write", PermissionLevel.ADMIN, "系统操作", dangerous=True, requires_confirm=True),
    "file.read": Permission("file.read", PermissionLevel.READ, "读取文件", dangerous=True),
    "file.write": Permission("file.write", PermissionLevel.ADMIN, "写入文件", dangerous=True, requires_confirm=True),
    "network": Permission("network", PermissionLevel.WRITE, "网络访问", dangerous=True, requires_confirm=True),
}


class PermissionManager:
    """权限管理器
    
    Attributes:
        _granted: 已授权权限 {plugin_id: set(permissions)}
        _denied: 已拒绝权限 {plugin_id: set(permissions)}
    """
    
    def __init__(self) -> None:
        """初始化权限管理器"""
        ...
    
    def check_permission(self, plugin_id: str, permission: str) -> bool:
        """检查插件是否有指定权限
        
        Args:
            plugin_id: 插件ID
            permission: 权限名称
            
        Returns:
            是否有权限
        """
        ...
    
    def grant_permission(self, plugin_id: str, permission: str) -> bool:
        """授予权限
        
        Args:
            plugin_id: 插件ID
            permission: 权限名称
            
        Returns:
            是否成功授予
        """
        ...
    
    def revoke_permission(self, plugin_id: str, permission: str) -> bool:
        """撤销权限
        
        Args:
            plugin_id: 插件ID
            permission: 权限名称
            
        Returns:
            是否成功撤销
        """
        ...
    
    def get_granted_permissions(self, plugin_id: str) -> Set[str]:
        """获取插件已授权的权限
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            权限集合
        """
        ...
    
    def get_required_permissions(self, manifest: Dict) -> List[str]:
        """从清单中提取所需权限
        
        Args:
            manifest: plugin.json内容
            
        Returns:
            权限列表
        """
        ...
    
    def get_dangerous_permissions(self, permissions: List[str]) -> List[Permission]:
        """筛选危险权限
        
        Args:
            permissions: 权限列表
            
        Returns:
            危险权限列表
        """
        ...
    
    async def request_user_confirmation(
        self,
        plugin_id: str,
        permissions: List[str],
    ) -> bool:
        """请求用户确认危险权限
        
        Args:
            plugin_id: 插件ID
            permissions: 需要确认的权限
            
        Returns:
            用户是否同意
        """
        ...
```

---

## 4. 数据模型

### 4.1 PluginManifest - 插件清单模型

```python
"""插件清单数据模型

对应 plugin.json 文件结构。
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


class MenuEntry(BaseModel):
    """菜单入口配置"""
    label: str
    icon: Optional[str] = None
    category: str = "plugins"


class ConfigSchemaItem(BaseModel):
    """配置Schema项"""
    type: str  # "string" | "number" | "boolean" | "array"
    default: Any = None
    description: Optional[str] = None
    enum: Optional[List[Any]] = None


class PluginManifest(BaseModel):
    """插件清单
    
    对应 plugin.json 结构
    """
    # 必需字段
    id: str = Field(..., description="插件唯一标识")
    name: str = Field(..., description="插件显示名称")
    version: str = Field(..., description="版本号 (SemVer)")
    author: str = Field(..., description="作者")
    description: str = Field(..., description="插件描述")
    type: str = Field(..., description="插件类型: game|tool|effect|integration|custom")
    entry: str = Field(..., description="入口文件名")
    
    # 可选字段
    menu_entry: Optional[MenuEntry] = None
    permissions: List[str] = Field(default_factory=list)
    config_schema: Dict[str, ConfigSchemaItem] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    min_app_version: str = "1.0.0"
    
    # 高级配置
    update_interval: Optional[float] = None  # 定时更新间隔（秒）
    sandbox_mode: bool = False  # 是否启用沙箱
    
    class Config:
        extra = "allow"  # 允许额外字段
```

---

## 5. 内置插件示例

### 5.1 猜拳游戏插件

```python
"""猜拳游戏插件

PRD映射: 第一部分 §18.1
"""

from typing import Dict, Any
from enum import Enum, auto
import random

from rainze.plugins import PluginBase, PluginAPI


class Choice(Enum):
    ROCK = "rock"
    PAPER = "paper"
    SCISSORS = "scissors"


class RockPaperScissorsPlugin(PluginBase):
    """猜拳游戏插件"""
    
    @property
    def id(self) -> str:
        return "rock_paper_scissors"
    
    @property
    def name(self) -> str:
        return "猜拳游戏"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def __init__(self) -> None:
        self._api: PluginAPI = None
        self._streak: int = 0  # 连胜/连败
        self._daily_rewards: int = 0  # 今日奖励次数
        self._max_daily_rewards: int = 5
    
    async def on_enable(self, api: PluginAPI) -> None:
        """启用时保存API引用"""
        self._api = api
        # 从存储恢复状态
        self._daily_rewards = api.storage.get("daily_rewards", 0)
    
    async def play(self, player_choice: str) -> Dict[str, Any]:
        """进行一局游戏
        
        Args:
            player_choice: 玩家选择 ("rock"|"paper"|"scissors")
            
        Returns:
            游戏结果
        """
        pet_choice = random.choice(list(Choice)).value
        result = self._judge(player_choice, pet_choice)
        
        # 处理奖励
        reward_coins = 0
        if result == "win" and self._daily_rewards < self._max_daily_rewards:
            reward_coins = 5
            self._api.economy.add_coins(reward_coins, "猜拳获胜")
            self._daily_rewards += 1
            self._api.storage.set("daily_rewards", self._daily_rewards)
        
        # 更新连胜
        if result == "win":
            self._streak = max(0, self._streak) + 1
        elif result == "lose":
            self._streak = min(0, self._streak) - 1
        else:
            self._streak = 0
        
        return {
            "player_choice": player_choice,
            "pet_choice": pet_choice,
            "result": result,
            "reward_coins": reward_coins,
            "streak": self._streak,
            "remaining_rewards": self._max_daily_rewards - self._daily_rewards,
        }
    
    def _judge(self, player: str, pet: str) -> str:
        """判定胜负"""
        if player == pet:
            return "draw"
        
        wins = {
            ("rock", "scissors"),
            ("scissors", "paper"),
            ("paper", "rock"),
        }
        
        if (player, pet) in wins:
            return "win"
        else:
            return "lose"
```

---

## 6. 配置文件

### 6.1 plugin.json 示例

```json
{
  "id": "rock_paper_scissors",
  "name": "猜拳游戏",
  "version": "1.0.0",
  "author": "Rainze Team",
  "description": "经典的石头剪刀布游戏",
  "type": "game",
  "entry": "main.py",
  "menu_entry": {
    "label": "猜拳",
    "icon": "✊",
    "category": "games"
  },
  "permissions": [
    "economy.read",
    "economy.write",
    "affinity.write",
    "ui.dialog",
    "storage.read",
    "storage.write"
  ],
  "config_schema": {
    "win_coins": {
      "type": "number",
      "default": 5,
      "description": "获胜奖励金币"
    },
    "max_daily_rewards": {
      "type": "number",
      "default": 5,
      "description": "每日最大奖励次数"
    }
  },
  "dependencies": [],
  "min_app_version": "1.0.0"
}
```

### 6.2 plugin_settings.json

```json
{
  "enable_plugins": true,
  "plugin_directories": ["./plugins"],
  "auto_load_plugins": true,
  "disabled_plugins": [],
  "plugin_update_check": false,
  "sandbox_mode": false,
  "max_plugin_memory_mb": 100,
  "plugin_timeout_seconds": 30,
  "builtin_plugins": {
    "rock_paper_scissors": true,
    "dice_roll": true,
    "local_llm_fallback": false
  },
  "permission_defaults": {
    "auto_grant_safe": true,
    "prompt_for_dangerous": true
  }
}
```

---

## 7. 错误处理

### 7.1 异常定义

```python
"""插件系统异常定义"""


class PluginError(Exception):
    """插件错误基类"""
    pass


class PluginNotFoundError(PluginError):
    """插件不存在"""
    pass


class PluginAlreadyLoadedError(PluginError):
    """插件已加载"""
    pass


class PluginDependencyError(PluginError):
    """依赖不满足"""
    pass


class PluginPermissionError(PluginError):
    """权限不足"""
    pass


class PluginManifestError(PluginError):
    """清单解析错误"""
    pass


class PluginExecutionError(PluginError):
    """执行错误"""
    pass


class PluginTimeoutError(PluginError):
    """执行超时"""
    pass
```

---

## 8. 测试要点

| 测试类别 | 测试项 | 预期结果 |
|----------|--------|----------|
| 生命周期 | 加载/卸载/启用/禁用 | 状态正确转换 |
| 权限 | 无权限调用API | 抛出PluginPermissionError |
| 隔离 | 插件A访问插件B存储 | 访问失败 |
| 超时 | 插件执行超过30秒 | 自动终止 |
| 热重载 | 修改代码后重载 | 新代码生效 |
| 依赖 | 缺少依赖时加载 | 抛出PluginDependencyError |

---

> **文档版本**: v1.0.0
> **生成时间**: 2025-12-29
> **生成工具**: Claude Opus 4
