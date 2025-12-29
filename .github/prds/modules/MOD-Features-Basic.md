# MOD-Features-Basic - 基础功能模块

> **模块版本**: v1.0.0
> **创建时间**: 2025-12-29
> **关联PRD**: PRD-Rainze.md v3.0.3 第一部分
> **关联技术栈**: TECH-Rainze.md v1.0.1
> **模块层级**: 功能层 (Feature Layer)
> **优先级**: P1 (核心体验)
> **依赖模块**: Core, State, AI, GUI, Agent

---

## 1. 模块概述

### 1.1 职责定义

本模块涵盖PRD第一部分定义的**基础稳健功能**，这些功能逻辑主要是"判定+触发"，代码纯本地运行，稳定且即写即用。

### 1.2 功能清单

| 编号 | 功能 | PRD章节 | 子模块 | 优先级 |
|------|------|---------|--------|--------|
| 1 | 聊天记录监控与回溯 | §1 | chat_history | P1 |
| 2 | 动态使用说明书 | §2 | help_system | P2 |
| 3 | 核心人设即时修改 | §3 | persona_editor | P1 |
| 4 | 个人档案注入 | §4 | user_profile | P1 |
| 5 | 整点报时与提醒 | §5 | hourly_chime | P1 |
| 6 | 专注时钟与监督 | §6 | focus_timer | P2 |
| 7 | 喂食与背包系统 | §7 | inventory | P1 |
| 8 | 好感度数值体系 | §8 | affinity | P1 |
| 9 | 日程提醒助手 | §9 | scheduler | P2 |
| 10 | 随机事件小剧场 | §10 | random_events | P2 |
| 11 | 闲聊陪伴模式 | §11 | idle_chat | P2 |
| 12 | 基础物理与交互 | §12 | physics | P1 |
| 13 | 系统状态感知 | §13 | system_monitor | P1 |
| 14 | 剪贴板互动 | §14 | clipboard | P3 |
| 15 | 昼夜作息系统 | §15 | sleep_system | P2 |
| 16 | 程序快速启动器 | §16 | launcher | P2 |
| 17 | 网站快捷访问 | §17 | bookmarks | P2 |
| 18 | 猜拳与掷骰子 | §18 | minigames | P2 |
| 19 | 本地文件整理 | §19 | file_organizer | P3 |
| 20 | 商城与经济系统 | §20 | economy | P2 |
| 21 | 网络延迟感知 | §21 | network_monitor | P3 |
| 22 | 游戏模式侦测 | §22 | gaming_mode | P2 |
| 24 | 随手记/便签条 | §24 | quick_notes | P2 |
| 25 | 本地天气感知 | §25 | weather | P2 |
| 26 | 彩蛋与隐藏指令 | §26 | easter_eggs | P3 |

> **注**: §23 情绪状态机系统属于 MOD-State.md 模块，不在本模块范围内

---

## 2. 目录结构

```
src/rainze/features/
├── __init__.py
├── basic/                      # 基础功能 (§1-§13)
│   ├── __init__.py
│   ├── chat_history.py         # §1 聊天记录
│   ├── help_system.py          # §2 帮助系统
│   ├── persona_editor.py       # §3 人设编辑
│   ├── user_profile.py         # §4 用户档案
│   ├── hourly_chime.py         # §5 整点报时
│   ├── focus_timer.py          # §6 专注时钟
│   ├── inventory.py            # §7 背包系统
│   ├── affinity.py             # §8 好感度
│   ├── scheduler.py            # §9 日程管理
│   ├── random_events.py        # §10 随机事件
│   ├── idle_chat.py            # §11 闲聊系统
│   ├── physics.py              # §12 物理交互
│   └── system_monitor.py       # §13 系统监控
├── extended/                   # 扩展功能 (§14-§26)
│   ├── __init__.py
│   ├── clipboard.py            # §14 剪贴板互动
│   ├── sleep_system.py         # §15 昼夜作息
│   ├── launcher.py             # §16 程序启动器
│   ├── bookmarks.py            # §17 网站书签
│   ├── minigames.py            # §18 小游戏
│   ├── file_organizer.py       # §19 文件整理
│   ├── economy.py              # §20 经济系统
│   ├── network_monitor.py      # §21 网络监控
│   ├── gaming_mode.py          # §22 游戏模式
│   ├── quick_notes.py          # §24 便签条
│   ├── weather.py              # §25 天气感知
│   └── easter_eggs.py          # §26 彩蛋系统
└── models/
    ├── __init__.py
    ├── schedule.py             # 日程数据模型
    ├── item.py                 # 物品数据模型
    ├── event.py                # 事件数据模型
    ├── note.py                 # 便签数据模型
    ├── shop.py                 # 商城数据模型
    └── game_result.py          # 游戏结果模型
```

---

## 3. 核心类设计

### 3.1 ChatHistoryManager - 聊天记录管理

```python
"""聊天记录管理器

PRD映射: §1 聊天记录监控与回溯
"""

from typing import TYPE_CHECKING, List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

if TYPE_CHECKING:
    from rainze.storage import Database


@dataclass
class ChatMessage:
    """聊天消息"""
    id: str
    role: str                   # "user" | "assistant"
    content: str
    timestamp: datetime
    emotion_tag: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class ChatSession:
    """聊天会话"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    messages: List[ChatMessage]
    summary: Optional[str] = None


class ChatHistoryManager:
    """聊天记录管理器
    
    Attributes:
        _db: 数据库引用
        _current_session: 当前会话
        _max_history: 最大历史记录数
    """
    
    def __init__(
        self,
        db: "Database",
        max_history: int = 1000,
    ) -> None:
        """初始化聊天记录管理器
        
        Args:
            db: 数据库实例
            max_history: 最大记录数
        """
        ...
    
    async def add_message(
        self,
        role: str,
        content: str,
        emotion_tag: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ChatMessage:
        """添加消息
        
        Args:
            role: 角色 ("user" | "assistant")
            content: 消息内容
            emotion_tag: 情感标签
            metadata: 额外元数据
            
        Returns:
            创建的消息对象
        """
        ...
    
    async def get_recent_messages(
        self,
        count: int = 20,
        session_id: Optional[str] = None,
    ) -> List[ChatMessage]:
        """获取最近消息
        
        Args:
            count: 获取数量
            session_id: 指定会话ID
            
        Returns:
            消息列表（时间升序）
        """
        ...
    
    async def get_history_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[ChatMessage], int]:
        """分页获取历史
        
        Args:
            page: 页码（从1开始）
            page_size: 每页大小
            
        Returns:
            (消息列表, 总数)
        """
        ...
    
    async def delete_message(self, message_id: str) -> bool:
        """删除单条消息
        
        Args:
            message_id: 消息ID
            
        Returns:
            是否成功删除
        """
        ...
    
    async def delete_by_date_range(
        self,
        start: datetime,
        end: datetime,
    ) -> int:
        """按日期范围删除
        
        Args:
            start: 起始时间
            end: 结束时间
            
        Returns:
            删除的消息数
        """
        ...
    
    async def search_messages(
        self,
        query: str,
        limit: int = 50,
    ) -> List[ChatMessage]:
        """搜索消息
        
        使用FTS5全文搜索
        
        Args:
            query: 搜索词
            limit: 返回数量限制
            
        Returns:
            匹配的消息列表
        """
        ...
    
    async def start_new_session(self) -> ChatSession:
        """开始新会话
        
        Returns:
            新会话对象
        """
        ...
    
    async def end_current_session(self, summary: Optional[str] = None) -> None:
        """结束当前会话
        
        Args:
            summary: 会话摘要
        """
        ...
    
    async def cleanup_old_records(self, days: int = 30) -> int:
        """清理旧记录
        
        Args:
            days: 保留天数
            
        Returns:
            清理的记录数
        """
        ...


### 3.2 HourlyChimeService - 整点报时服务

```python
"""整点报时服务

PRD映射: §5 整点报时与提醒
"""

from typing import TYPE_CHECKING, Optional, Dict, Any, Callable
from datetime import datetime, time
from dataclasses import dataclass
from enum import Enum

if TYPE_CHECKING:
    from rainze.agent import UnifiedContextManager
    from rainze.core import EventBus


class TimePeriod(Enum):
    """时间段"""
    DEEP_NIGHT = "deep_night"   # 00-05
    MORNING = "morning"         # 06-11
    AFTERNOON = "afternoon"     # 12-17
    EVENING = "evening"         # 18-23


@dataclass
class ChimeConfig:
    """报时配置"""
    enable: bool = True
    enable_sound: bool = True
    sound_path: str = "./assets/audio/chime.wav"
    expression: str = "shout"


@dataclass
class ChimeContext:
    """报时上下文"""
    hour: int
    time_period: TimePeriod
    weather: Optional[str]
    user_activity: str
    mood: str
    energy: int


class HourlyChimeService:
    """整点报时服务
    
    Attributes:
        _context_manager: 上下文管理器
        _event_bus: 事件总线
        _config: 报时配置
        _last_chime_hour: 上次报时的小时
    """
    
    def __init__(
        self,
        context_manager: "UnifiedContextManager",
        event_bus: "EventBus",
        config: Optional[ChimeConfig] = None,
    ) -> None:
        """初始化报时服务
        
        Args:
            context_manager: 上下文管理器
            event_bus: 事件总线
            config: 报时配置
        """
        ...
    
    def check_and_trigger(self) -> bool:
        """检查并触发报时
        
        每秒调用一次，在整点时触发
        
        Returns:
            是否触发了报时
        """
        ...
    
    async def trigger_chime(self, hour: int) -> None:
        """触发报时
        
        Args:
            hour: 小时数 (0-23)
        """
        ...
    
    def _build_context(self, hour: int) -> ChimeContext:
        """构建报时上下文
        
        Args:
            hour: 小时数
            
        Returns:
            报时上下文
        """
        ...
    
    def _get_time_period(self, hour: int) -> TimePeriod:
        """获取时间段
        
        Args:
            hour: 小时数
            
        Returns:
            时间段枚举
        """
        ...
    
    def _play_sound(self) -> None:
        """播放报时音效"""
        ...
    
    def set_enabled(self, enabled: bool) -> None:
        """设置启用状态
        
        Args:
            enabled: 是否启用
        """
        ...
```


### 3.3 FocusTimerService - 专注时钟服务

```python
"""专注时钟服务

PRD映射: §6 专注时钟与监督
"""

from typing import TYPE_CHECKING, Optional, List, Set, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum, auto

if TYPE_CHECKING:
    from rainze.agent import UnifiedContextManager
    from rainze_core import SystemMonitor


class FocusState(Enum):
    """专注状态"""
    IDLE = auto()           # 空闲
    FOCUSING = auto()       # 专注中
    PAUSED = auto()         # 暂停
    COMPLETED = auto()      # 完成


@dataclass
class FocusSession:
    """专注会话"""
    session_id: str
    start_time: datetime
    target_duration: timedelta
    elapsed_duration: timedelta = field(default_factory=lambda: timedelta())
    warning_count: int = 0
    distraction_apps: List[str] = field(default_factory=list)
    state: FocusState = FocusState.IDLE


@dataclass
class FocusConfig:
    """专注配置"""
    default_duration_minutes: int = 25
    check_interval_seconds: int = 3
    warning_cooldown_seconds: int = 30
    shake_intensity: int = 5
    blacklist: List[str] = field(default_factory=list)


class FocusTimerService:
    """专注时钟服务
    
    Attributes:
        _context_manager: 上下文管理器
        _system_monitor: 系统监控器（Rust）
        _config: 配置
        _current_session: 当前会话
        _blacklist: 黑名单应用
        _last_warning_time: 上次警告时间
    """
    
    def __init__(
        self,
        context_manager: "UnifiedContextManager",
        system_monitor: "SystemMonitor",
        config: Optional[FocusConfig] = None,
    ) -> None:
        """初始化专注时钟
        
        Args:
            context_manager: 上下文管理器
            system_monitor: 系统监控器
            config: 配置
        """
        ...
    
    async def start_focus(
        self,
        duration_minutes: int = 25,
    ) -> FocusSession:
        """开始专注
        
        Args:
            duration_minutes: 专注时长（分钟）
            
        Returns:
            专注会话
            
        Raises:
            FocusAlreadyActiveError: 已有进行中的专注
        """
        ...
    
    async def pause_focus(self) -> None:
        """暂停专注"""
        ...
    
    async def resume_focus(self) -> None:
        """恢复专注"""
        ...
    
    async def cancel_focus(self) -> None:
        """取消专注"""
        ...
    
    async def tick(self) -> None:
        """每秒调用的tick函数
        
        - 检查活动窗口
        - 更新已用时间
        - 检查是否完成
        """
        ...
    
    async def _check_distraction(self) -> Optional[str]:
        """检查是否有分心应用
        
        Returns:
            检测到的分心应用名，无则返回None
        """
        ...
    
    async def _trigger_warning(self, app_name: str) -> None:
        """触发警告
        
        Args:
            app_name: 分心应用名
        """
        ...
    
    async def _complete_focus(self) -> None:
        """完成专注"""
        ...
    
    def get_remaining_time(self) -> timedelta:
        """获取剩余时间
        
        Returns:
            剩余时间
        """
        ...
    
    def get_progress(self) -> float:
        """获取进度
        
        Returns:
            进度百分比 (0-1)
        """
        ...
    
    def add_to_blacklist(self, app: str) -> None:
        """添加应用到黑名单
        
        Args:
            app: 应用名或进程名
        """
        ...
    
    def remove_from_blacklist(self, app: str) -> None:
        """从黑名单移除应用
        
        Args:
            app: 应用名
        """
        ...


### 3.4 InventoryManager - 背包管理器

```python
"""背包管理器

PRD映射: §7 喂食与背包系统
"""

from typing import TYPE_CHECKING, Optional, List, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path

if TYPE_CHECKING:
    from rainze.state import StateManager


@dataclass
class ItemAttributes:
    """物品属性"""
    taste: List[str] = field(default_factory=list)      # 口感
    texture: str = ""                                    # 质地
    temperature: str = "room"                            # 温度
    size: str = "medium"                                 # 大小
    color: str = ""                                      # 颜色
    freshness: str = "fresh"                            # 新鲜度


@dataclass
class ItemEffects:
    """物品效果"""
    affinity_bonus: int = 0
    mood_impact: float = 0.0
    energy_restore: int = 0
    hunger_restore: int = 10


@dataclass
class Item:
    """物品定义"""
    id: str
    display_name: str
    icon: str
    quantity: int
    category: str
    attributes: ItemAttributes
    effects: ItemEffects
    context_tags: List[str] = field(default_factory=list)
    animation_override: Optional[str] = None


class InventoryManager:
    """背包管理器
    
    Attributes:
        _state_manager: 状态管理器
        _items: 物品映射 {id: Item}
        _items_path: 物品数据文件路径
    """
    
    def __init__(
        self,
        state_manager: "StateManager",
        items_path: Path = Path("./data/items.json"),
    ) -> None:
        """初始化背包管理器
        
        Args:
            state_manager: 状态管理器
            items_path: 物品数据文件路径
        """
        ...
    
    async def load_items(self) -> None:
        """加载物品数据"""
        ...
    
    async def save_items(self) -> None:
        """保存物品数据"""
        ...
    
    def get_item(self, item_id: str) -> Optional[Item]:
        """获取物品
        
        Args:
            item_id: 物品ID
            
        Returns:
            物品对象
        """
        ...
    
    def list_items(
        self,
        category: Optional[str] = None,
    ) -> List[Item]:
        """列出物品
        
        Args:
            category: 按类别筛选
            
        Returns:
            物品列表
        """
        ...
    
    def add_item(
        self,
        item_id: str,
        quantity: int = 1,
    ) -> bool:
        """添加物品
        
        Args:
            item_id: 物品ID
            quantity: 数量
            
        Returns:
            是否成功
        """
        ...
    
    def remove_item(
        self,
        item_id: str,
        quantity: int = 1,
    ) -> bool:
        """移除物品
        
        Args:
            item_id: 物品ID
            quantity: 数量
            
        Returns:
            是否成功
        """
        ...
    
    def use_item(self, item_id: str) -> Optional[ItemEffects]:
        """使用物品
        
        Args:
            item_id: 物品ID
            
        Returns:
            物品效果，失败返回None
        """
        ...
    
    def get_food_items(self) -> List[Item]:
        """获取所有食物物品
        
        Returns:
            食物物品列表
        """
        ...
    
    def register_custom_item(self, item: Item) -> None:
        """注册自定义物品
        
        Args:
            item: 物品对象
        """
        ...
```


### 3.5 SchedulerService - 日程服务

```python
"""日程服务

PRD映射: §9 日程提醒助手
"""

from typing import TYPE_CHECKING, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from rainze.core import EventBus


class ReminderType(Enum):
    """提醒类型"""
    ONCE = "once"           # 一次性
    DAILY = "daily"         # 每日
    WEEKLY = "weekly"       # 每周
    CUSTOM = "custom"       # 自定义


@dataclass
class Schedule:
    """日程"""
    id: str
    title: str
    datetime: datetime
    reminder_type: ReminderType = ReminderType.ONCE
    advance_minutes: int = 5        # 提前提醒分钟数
    message: Optional[str] = None
    is_completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)


class SchedulerService:
    """日程服务
    
    Attributes:
        _event_bus: 事件总线
        _schedules: 日程列表
        _poll_interval: 轮询间隔（秒）
    """
    
    def __init__(
        self,
        event_bus: "EventBus",
        poll_interval: int = 30,
    ) -> None:
        """初始化日程服务
        
        Args:
            event_bus: 事件总线
            poll_interval: 轮询间隔
        """
        ...
    
    async def load_schedules(self) -> None:
        """加载日程数据"""
        ...
    
    async def save_schedules(self) -> None:
        """保存日程数据"""
        ...
    
    async def add_schedule(
        self,
        title: str,
        datetime_: datetime,
        reminder_type: ReminderType = ReminderType.ONCE,
        advance_minutes: int = 5,
        message: Optional[str] = None,
    ) -> Schedule:
        """添加日程
        
        Args:
            title: 日程标题
            datetime_: 日程时间
            reminder_type: 提醒类型
            advance_minutes: 提前提醒分钟数
            message: 提醒消息
            
        Returns:
            创建的日程
        """
        ...
    
    async def remove_schedule(self, schedule_id: str) -> bool:
        """移除日程
        
        Args:
            schedule_id: 日程ID
            
        Returns:
            是否成功
        """
        ...
    
    async def update_schedule(
        self,
        schedule_id: str,
        **kwargs,
    ) -> Optional[Schedule]:
        """更新日程
        
        Args:
            schedule_id: 日程ID
            **kwargs: 要更新的字段
            
        Returns:
            更新后的日程
        """
        ...
    
    def get_schedule(self, schedule_id: str) -> Optional[Schedule]:
        """获取日程
        
        Args:
            schedule_id: 日程ID
            
        Returns:
            日程对象
        """
        ...
    
    def list_schedules(
        self,
        include_completed: bool = False,
    ) -> List[Schedule]:
        """列出日程
        
        Args:
            include_completed: 是否包含已完成
            
        Returns:
            日程列表
        """
        ...
    
    def list_upcoming(
        self,
        hours: int = 24,
    ) -> List[Schedule]:
        """列出即将到来的日程
        
        Args:
            hours: 时间范围（小时）
            
        Returns:
            日程列表
        """
        ...
    
    async def check_and_trigger(self) -> List[Schedule]:
        """检查并触发提醒
        
        每poll_interval秒调用一次
        
        Returns:
            触发的日程列表
        """
        ...
    
    async def _trigger_reminder(self, schedule: Schedule) -> None:
        """触发提醒
        
        Args:
            schedule: 日程
        """
        ...
    
    async def mark_completed(self, schedule_id: str) -> bool:
        """标记完成
        
        Args:
            schedule_id: 日程ID
            
        Returns:
            是否成功
        """
        ...
```


### 3.6 RandomEventService - 随机事件服务

```python
"""随机事件服务

PRD映射: §10 随机事件小剧场
"""

from typing import TYPE_CHECKING, Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from rainze.agent import UnifiedContextManager


@dataclass
class EventOption:
    """事件选项"""
    text: str
    coins_change: int = 0
    affinity_change: int = 0
    result_text: str = ""


@dataclass
class RandomEvent:
    """随机事件"""
    id: str
    situation: str                      # 情景描述
    options: List[EventOption]          # 选项列表
    generated_at: datetime
    is_ai_generated: bool = True


class RandomEventService:
    """随机事件服务
    
    Attributes:
        _context_manager: 上下文管理器
        _trigger_interval: 触发间隔（分钟）
        _last_event_time: 上次事件时间
        _recent_events: 最近事件历史（用于避免重复）
    """
    
    def __init__(
        self,
        context_manager: "UnifiedContextManager",
        trigger_interval_minutes: int = 60,
    ) -> None:
        """初始化随机事件服务
        
        Args:
            context_manager: 上下文管理器
            trigger_interval_minutes: 触发间隔
        """
        ...
    
    def should_trigger(self) -> bool:
        """判断是否应该触发事件
        
        Returns:
            是否触发
        """
        ...
    
    async def generate_event(self) -> RandomEvent:
        """生成随机事件
        
        优先使用AI生成，失败时从预设库选择
        
        Returns:
            随机事件
        """
        ...
    
    async def _generate_ai_event(self) -> Optional[RandomEvent]:
        """AI生成事件
        
        Returns:
            AI生成的事件，失败返回None
        """
        ...
    
    def _get_preset_event(self) -> RandomEvent:
        """获取预设事件
        
        Returns:
            预设事件
        """
        ...
    
    async def handle_choice(
        self,
        event: RandomEvent,
        choice_index: int,
    ) -> Dict[str, Any]:
        """处理用户选择
        
        Args:
            event: 事件
            choice_index: 选择的选项索引
            
        Returns:
            处理结果 {result_text, coins_change, affinity_change}
        """
        ...
    
    def set_interval(self, minutes: int) -> None:
        """设置触发间隔
        
        Args:
            minutes: 间隔分钟数
        """
        ...
```

### 3.7 IdleChatService - 闲聊服务

```python
"""闲聊服务

PRD映射: §11 闲聊陪伴模式
"""

from typing import TYPE_CHECKING, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

if TYPE_CHECKING:
    from rainze.agent import UnifiedContextManager


@dataclass
class IdleChatConfig:
    """闲聊配置"""
    enable: bool = True
    idle_timeout_minutes: int = 20
    chat_cooldown_minutes: int = 10
    max_length: int = 50


class IdleChatService:
    """闲聊服务
    
    Attributes:
        _context_manager: 上下文管理器
        _config: 配置
        _last_activity_time: 上次用户活动时间
        _last_chat_time: 上次闲聊时间
    """
    
    def __init__(
        self,
        context_manager: "UnifiedContextManager",
        config: Optional[IdleChatConfig] = None,
    ) -> None:
        """初始化闲聊服务
        
        Args:
            context_manager: 上下文管理器
            config: 配置
        """
        ...
    
    def update_activity(self) -> None:
        """更新用户活动时间
        
        在检测到用户操作时调用
        """
        ...
    
    def get_idle_duration(self) -> timedelta:
        """获取空闲时长
        
        Returns:
            空闲时长
        """
        ...
    
    def should_chat(self) -> bool:
        """判断是否应该闲聊
        
        Returns:
            是否触发闲聊
        """
        ...
    
    async def trigger_chat(self) -> Optional[str]:
        """触发闲聊
        
        Returns:
            闲聊内容
        """
        ...
    
    def set_enabled(self, enabled: bool) -> None:
        """设置启用状态
        
        Args:
            enabled: 是否启用
        """
        ...
```

### 3.8 SystemStatusService - 系统状态服务

```python
"""系统状态服务

PRD映射: §13 系统状态感知与主动场景识别
"""

from typing import TYPE_CHECKING, Optional, Dict, Any, List, Set
from dataclasses import dataclass
from enum import Enum, auto

if TYPE_CHECKING:
    from rainze.agent import UnifiedContextManager
    from rainze_core import SystemMonitor


class WarningType(Enum):
    """警告类型"""
    CPU_HIGH = "cpu_high"
    MEMORY_HIGH = "memory_high"
    DISK_FULL = "disk_full"


class UserActivityState(Enum):
    """用户活动状态"""
    ACTIVE = "active"           # 活跃
    IDLE = "idle"               # 空闲
    FULLSCREEN = "fullscreen"   # 全屏应用
    MEETING = "meeting"         # 会议中
    GAMING = "gaming"           # 游戏中


@dataclass
class SystemStatus:
    """系统状态"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    active_window: str
    user_activity: UserActivityState


@dataclass
class SystemMonitorConfig:
    """系统监控配置"""
    enable: bool = True
    check_interval_seconds: int = 5
    cpu_warning_threshold: int = 85
    memory_warning_threshold: int = 90
    meeting_apps: List[str] = None
    gaming_apps: List[str] = None


class SystemStatusService:
    """系统状态服务
    
    Attributes:
        _context_manager: 上下文管理器
        _system_monitor: Rust系统监控模块
        _config: 配置
        _last_status: 上次状态
        _warning_cooldowns: 警告冷却时间
    """
    
    def __init__(
        self,
        context_manager: "UnifiedContextManager",
        system_monitor: "SystemMonitor",
        config: Optional[SystemMonitorConfig] = None,
    ) -> None:
        """初始化系统状态服务
        
        Args:
            context_manager: 上下文管理器
            system_monitor: Rust系统监控模块
            config: 配置
        """
        ...
    
    async def get_status(self) -> SystemStatus:
        """获取当前系统状态
        
        Returns:
            系统状态
        """
        ...
    
    async def check_and_warn(self) -> Optional[WarningType]:
        """检查并触发警告
        
        Returns:
            触发的警告类型
        """
        ...
    
    async def _trigger_warning(
        self,
        warning_type: WarningType,
        value: float,
    ) -> None:
        """触发警告
        
        Args:
            warning_type: 警告类型
            value: 当前值
        """
        ...
    
    def detect_user_activity(self) -> UserActivityState:
        """检测用户活动状态
        
        Returns:
            用户活动状态
        """
        ...
    
    def is_fullscreen(self) -> bool:
        """是否全屏应用
        
        Returns:
            是否全屏
        """
        ...
    
    def is_in_meeting(self) -> bool:
        """是否在会议中
        
        Returns:
            是否会议
        """
        ...
    
    def get_active_window_title(self) -> str:
        """获取活动窗口标题
        
        Returns:
            窗口标题
        """
        ...
    
    def get_active_process_name(self) -> str:
        """获取活动进程名
        
        Returns:
            进程名
        """
        ...
```

### 3.9 AffinityManager - 好感度系统

```python
"""
好感度系统管理器
PRD: 第一部分 8. 好感度数值体系
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum

if TYPE_CHECKING:
    from rainze.core.state import StateManager
    from rainze.core.memory import MemoryManager


class AffinityLevel(IntEnum):
    """好感度等级"""
    STRANGER = 1      # 陌生 0-24
    FAMILIAR = 2      # 熟悉 25-49
    INTIMATE = 3      # 亲密 50-74
    BELOVED = 4       # 挚爱 75-99
    BONDED = 5        # 羁绊 100+


@dataclass
class AffinityEvent:
    """好感度变化事件"""
    timestamp: datetime
    action: str
    delta: int
    old_value: int
    new_value: int
    old_level: AffinityLevel
    new_level: AffinityLevel


class AffinityManager:
    """好感度系统管理器
    
    Attributes:
        current_value: 当前好感度数值 (0-999)
        current_level: 当前好感度等级
        state_manager: 状态管理器引用
        memory_manager: 记忆管理器引用
        on_level_up: 等级提升回调
    """
    
    LEVEL_THRESHOLDS = {
        AffinityLevel.STRANGER: 0,
        AffinityLevel.FAMILIAR: 25,
        AffinityLevel.INTIMATE: 50,
        AffinityLevel.BELOVED: 75,
        AffinityLevel.BONDED: 100,
    }
    
    MIN_AFFINITY = 10
    MAX_AFFINITY = 999
    
    def __init__(
        self,
        state_manager: StateManager,
        memory_manager: MemoryManager,
        initial_value: int = 50
    ) -> None:
        """初始化好感度系统
        
        Args:
            state_manager: 状态管理器
            memory_manager: 记忆管理器
            initial_value: 初始好感度值
        """
        ...
    
    @property
    def current_value(self) -> int:
        """获取当前好感度值"""
        ...
    
    @property
    def current_level(self) -> AffinityLevel:
        """获取当前好感度等级"""
        ...
    
    def add_affinity(self, amount: int, action: str) -> AffinityEvent:
        """增加好感度
        
        Args:
            amount: 增加数量
            action: 触发动作描述
            
        Returns:
            好感度变化事件
        """
        ...
    
    def reduce_affinity(self, amount: int, action: str) -> AffinityEvent:
        """减少好感度
        
        Args:
            amount: 减少数量
            action: 触发动作描述
            
        Returns:
            好感度变化事件
        """
        ...
    
    def get_level_progress(self) -> tuple[int, int]:
        """获取当前等级进度
        
        Returns:
            (当前等级内进度, 等级所需总进度)
        """
        ...
    
    def get_proactivity_multiplier(self) -> float:
        """获取主动性乘数
        
        根据好感度等级返回主动行为频率乘数
        
        Returns:
            主动性乘数 (0.2-1.0)
        """
        ...
    
    def register_level_up_callback(self, callback: Callable[[AffinityLevel, AffinityLevel], None]) -> None:
        """注册等级提升回调
        
        Args:
            callback: 回调函数 (old_level, new_level)
        """
        ...
```

### 3.10 FeedingManager - 喂食系统

```python
"""
喂食系统管理器
PRD: 第一部分 7. 喂食与背包系统
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

if TYPE_CHECKING:
    from rainze.features.basic.inventory import InventoryManager
    from rainze.features.basic.affinity import AffinityManager
    from rainze.core.state import StateManager
    from rainze.core.generation import ResponseGenerator


@dataclass
class FoodItem:
    """食物物品"""
    id: str
    display_name: str
    icon_path: str
    category: str
    attributes: dict[str, Any]  # taste, texture, temperature等
    effects: dict[str, int]      # affinity_bonus, mood_impact等
    context_tags: list[str]


@dataclass
class FeedingResult:
    """喂食结果"""
    success: bool
    food_item: FoodItem
    response_text: str
    emotion_tag: str
    affinity_change: int
    energy_change: int
    hunger_change: int


class FeedingManager:
    """喂食系统管理器
    
    Attributes:
        inventory_manager: 背包管理器
        affinity_manager: 好感度管理器
        state_manager: 状态管理器
        response_generator: 响应生成器
    """
    
    def __init__(
        self,
        inventory_manager: InventoryManager,
        affinity_manager: AffinityManager,
        state_manager: StateManager,
        response_generator: ResponseGenerator
    ) -> None:
        """初始化喂食系统
        
        Args:
            inventory_manager: 背包管理器
            affinity_manager: 好感度管理器
            state_manager: 状态管理器
            response_generator: 响应生成器
        """
        ...
    
    async def feed(self, food_id: str) -> FeedingResult:
        """执行喂食
        
        Args:
            food_id: 食物ID
            
        Returns:
            喂食结果
            
        Raises:
            ItemNotFoundError: 食物不存在
            InsufficientQuantityError: 数量不足
        """
        ...
    
    async def generate_feed_response(self, food_item: FoodItem) -> tuple[str, str]:
        """生成喂食响应
        
        Args:
            food_item: 食物物品
            
        Returns:
            (响应文本, 情感标签)
        """
        ...
    
    def get_food_list(self) -> list[FoodItem]:
        """获取可用食物列表
        
        Returns:
            食物列表
        """
        ...
    
    def load_food_definitions(self, config_path: str) -> None:
        """加载食物定义
        
        Args:
            config_path: 配置文件路径
        """
        ...
```

### 3.11 VoiceInteractionService - 互动语音

```python
"""
互动语音服务
PRD: 第二部分 2. 本地TTS语音
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Callable
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

if TYPE_CHECKING:
    from rainze.gui.animation import AnimationController


class MouthShape(str, Enum):
    """嘴型"""
    CLOSED = "closed"
    A = "A"
    I = "I"
    U = "U"
    E = "E"
    O = "O"


@dataclass
class TTSConfig:
    """TTS配置"""
    model_path: str
    sample_rate: int = 22050
    speaker_id: Optional[int] = None


class VoiceInteractionService:
    """互动语音服务
    
    Attributes:
        tts_config: TTS配置
        animation_controller: 动画控制器
        is_speaking: 是否正在说话
        audio_cache_dir: 音频缓存目录
    """
    
    def __init__(
        self,
        tts_config: TTSConfig,
        animation_controller: AnimationController,
        cache_dir: Path
    ) -> None:
        """初始化语音服务
        
        Args:
            tts_config: TTS配置
            animation_controller: 动画控制器
            cache_dir: 缓存目录
        """
        ...
    
    async def speak(
        self,
        text: str,
        emotion: Optional[str] = None,
        sync_lipsync: bool = True
    ) -> None:
        """播放语音
        
        Args:
            text: 要说的文本
            emotion: 情感标签
            sync_lipsync: 是否同步口型
        """
        ...
    
    async def generate_audio(self, text: str, emotion: Optional[str] = None) -> Path:
        """生成音频文件
        
        Args:
            text: 文本
            emotion: 情感
            
        Returns:
            生成的音频文件路径
        """
        ...
    
    def analyze_amplitude(self, audio_path: Path) -> list[tuple[float, float]]:
        """分析音频振幅
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            [(时间戳, 振幅), ...]
        """
        ...
    
    def amplitude_to_mouth_shape(self, amplitude: float) -> MouthShape:
        """振幅转嘴型
        
        Args:
            amplitude: 振幅值
            
        Returns:
            嘴型
        """
        ...
    
    def stop(self) -> None:
        """停止当前语音"""
        ...
    
    def set_volume(self, volume: float) -> None:
        """设置音量
        
        Args:
            volume: 音量 (0.0-1.0)
        """
        ...
```

### 3.12 TimeGreetingService - 时段问候

```python
"""
时段问候服务
PRD: 第一部分 5. 整点报时与提醒
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import datetime, time
from dataclasses import dataclass
from enum import Enum

if TYPE_CHECKING:
    from rainze.core.generation import ResponseGenerator
    from rainze.core.state import StateManager


class TimePeriod(str, Enum):
    """时段"""
    DEEP_NIGHT = "deep_night"    # 00-05
    MORNING = "morning"          # 06-11
    AFTERNOON = "afternoon"      # 12-17
    EVENING = "evening"          # 18-23


@dataclass
class TimePeriodConfig:
    """时段配置"""
    period_name: str
    atmosphere: str
    energy_level: str
    typical_activities: list[str]
    health_concerns: list[str]
    mood_tendency: str


class TimeGreetingService:
    """时段问候服务
    
    Attributes:
        response_generator: 响应生成器
        state_manager: 状态管理器
        period_configs: 时段配置映射
    """
    
    def __init__(
        self,
        response_generator: ResponseGenerator,
        state_manager: StateManager,
        config_path: str
    ) -> None:
        """初始化时段问候服务
        
        Args:
            response_generator: 响应生成器
            state_manager: 状态管理器
            config_path: 配置文件路径
        """
        ...
    
    def get_current_period(self) -> TimePeriod:
        """获取当前时段
        
        Returns:
            当前时段
        """
        ...
    
    def get_period_config(self, period: TimePeriod) -> TimePeriodConfig:
        """获取时段配置
        
        Args:
            period: 时段
            
        Returns:
            时段配置
        """
        ...
    
    async def generate_greeting(
        self,
        period: Optional[TimePeriod] = None,
        include_weather: bool = True
    ) -> tuple[str, str]:
        """生成问候语
        
        Args:
            period: 指定时段，None则使用当前时段
            include_weather: 是否包含天气信息
            
        Returns:
            (问候文本, 情感标签)
        """
        ...
    
    def is_late_night_activity(self) -> bool:
        """检测是否深夜活动
        
        Returns:
            是否深夜还在活动
        """
        ...
    
    async def generate_late_night_reminder(self) -> str:
        """生成深夜提醒
        
        Returns:
            提醒文本
        """
        ...
```

### 3.13 HolidayManager - 生日/节日

```python
"""
生日/节日管理器
PRD: 第一部分 26. 彩蛋与隐藏指令 (节日部分)
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import date, datetime
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from rainze.core.generation import ResponseGenerator
    from rainze.core.memory import MemoryManager


@dataclass
class Holiday:
    """节日定义"""
    id: str
    name: str
    date_pattern: str  # "MM-DD" 或 "LUNAR:MM-DD"
    is_lunar: bool = False
    celebration_type: str = "normal"  # normal, major, special
    custom_effects: list[str] = field(default_factory=list)


@dataclass
class UpcomingEvent:
    """即将到来的事件"""
    event_type: str  # "birthday", "holiday"
    name: str
    date: date
    days_until: int


class HolidayManager:
    """生日/节日管理器
    
    Attributes:
        response_generator: 响应生成器
        memory_manager: 记忆管理器
        holidays: 节日列表
        master_birthday: 用户生日
    """
    
    def __init__(
        self,
        response_generator: ResponseGenerator,
        memory_manager: MemoryManager,
        config_path: str
    ) -> None:
        """初始化节日管理器
        
        Args:
            response_generator: 响应生成器
            memory_manager: 记忆管理器
            config_path: 配置文件路径
        """
        ...
    
    def set_master_birthday(self, birthday: date) -> None:
        """设置用户生日
        
        Args:
            birthday: 生日日期
        """
        ...
    
    def check_today(self) -> list[Holiday]:
        """检查今日节日
        
        Returns:
            今日节日列表
        """
        ...
    
    def is_master_birthday(self) -> bool:
        """是否是用户生日
        
        Returns:
            是否生日
        """
        ...
    
    def get_upcoming_events(self, days: int = 7) -> list[UpcomingEvent]:
        """获取即将到来的事件
        
        Args:
            days: 天数范围
            
        Returns:
            事件列表
        """
        ...
    
    async def generate_holiday_greeting(self, holiday: Holiday) -> tuple[str, str]:
        """生成节日问候
        
        Args:
            holiday: 节日
            
        Returns:
            (问候文本, 情感标签)
        """
        ...
    
    async def generate_birthday_celebration(self) -> tuple[str, str, list[str]]:
        """生成生日庆祝
        
        Returns:
            (祝福文本, 情感标签, 特效列表)
        """
        ...
    
    def register_custom_holiday(self, holiday: Holiday) -> None:
        """注册自定义节日
        
        Args:
            holiday: 节日定义
        """
        ...
```

### 3.14 ClipboardManager - 剪贴板互动

```python
"""剪贴板互动管理器 - 监听剪贴板变化并生成个性化响应"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import re

if TYPE_CHECKING:
    from ..ai.response_generator import ResponseGenerator


class ContentType(str, Enum):
    """剪贴板内容类型"""
    TEXT = "text"
    LINK = "link"
    CODE = "code"
    IMAGE = "image"
    LONG_TEXT = "long_text"
    UNKNOWN = "unknown"


@dataclass
class ClipboardContent:
    """剪贴板内容"""
    raw_content: str
    content_type: ContentType
    preview: str  # 截断预览
    detected_keywords: list[str] = field(default_factory=list)
    timestamp: float = 0.0


@dataclass
class ContentDetectionRule:
    """内容检测规则"""
    pattern: str
    content_type: ContentType
    hint: str


class ClipboardManager:
    """剪贴板互动管理器
    
    Attributes:
        response_generator: AI响应生成器
        config_path: 配置文件路径
        is_monitoring: 是否正在监听
        last_content: 最后一次剪贴板内容
        on_content_change: 内容变化回调
    """
    
    def __init__(
        self,
        response_generator: ResponseGenerator,
        config_path: str = "./config/clipboard_settings.json"
    ) -> None:
        """初始化剪贴板管理器
        
        Args:
            response_generator: 响应生成器
            config_path: 配置文件路径
        """
        ...
    
    def start_monitoring(self) -> None:
        """开始监听剪贴板"""
        ...
    
    def stop_monitoring(self) -> None:
        """停止监听剪贴板"""
        ...
    
    def _detect_content_type(self, content: str) -> ContentType:
        """检测内容类型
        
        Args:
            content: 剪贴板内容
            
        Returns:
            内容类型
        """
        ...
    
    def _extract_keywords(self, content: str) -> list[str]:
        """提取关键词
        
        Args:
            content: 内容
            
        Returns:
            关键词列表
        """
        ...
    
    def get_current_content(self) -> Optional[ClipboardContent]:
        """获取当前剪贴板内容
        
        Returns:
            剪贴板内容，如果为空则返回None
        """
        ...
    
    async def generate_reaction(self, content: ClipboardContent) -> tuple[str, str]:
        """生成剪贴板反应
        
        Args:
            content: 剪贴板内容
            
        Returns:
            (反应文本, 情感标签)
        """
        ...
    
    def clear_clipboard(self) -> bool:
        """清空剪贴板（"吃掉"功能）
        
        Returns:
            是否成功
        """
        ...
    
    async def generate_eat_feedback(self, content: ClipboardContent) -> tuple[str, str]:
        """生成"吃掉"反馈
        
        Args:
            content: 被吃掉的内容
            
        Returns:
            (反馈文本, 情感标签)
        """
        ...
    
    def register_on_change(self, callback: Callable[[ClipboardContent], None]) -> None:
        """注册内容变化回调
        
        Args:
            callback: 回调函数
        """
        ...
```

### 3.15 SleepSystemManager - 昼夜作息系统

```python
"""昼夜作息系统管理器 - 管理桌宠的睡眠和唤醒"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import random

if TYPE_CHECKING:
    from ..ai.response_generator import ResponseGenerator
    from ..state.user_state_manager import UserStateManager


class SleepState(str, Enum):
    """睡眠状态"""
    AWAKE = "awake"
    SLEEPY = "sleepy"  # 犯困
    NAPPING = "napping"  # 小睡
    DEEP_SLEEP = "deep_sleep"  # 深睡


class WakeReason(str, Enum):
    """唤醒原因"""
    NATURAL = "natural"  # 自然醒
    USER_INTERACTION = "user_interaction"  # 用户交互
    ALARM = "alarm"  # 闹钟
    SCHEDULED = "scheduled"  # 计划唤醒


@dataclass
class SleepSession:
    """睡眠会话"""
    start_time: datetime
    planned_duration_minutes: int
    actual_end_time: Optional[datetime] = None
    wake_reason: Optional[WakeReason] = None


class SleepSystemManager:
    """昼夜作息系统管理器
    
    Attributes:
        response_generator: AI响应生成器
        state_manager: 状态管理器
        current_state: 当前睡眠状态
        current_session: 当前睡眠会话
        on_state_change: 状态变化回调
    """
    
    def __init__(
        self,
        response_generator: ResponseGenerator,
        state_manager: UserStateManager,
        config_path: str = "./config/sleep_settings.json"
    ) -> None:
        """初始化睡眠系统
        
        Args:
            response_generator: 响应生成器
            state_manager: 状态管理器
            config_path: 配置文件路径
        """
        ...
    
    def get_sleep_state(self) -> SleepState:
        """获取当前睡眠状态
        
        Returns:
            睡眠状态
        """
        ...
    
    def check_sleepy_condition(self, idle_minutes: int) -> bool:
        """检查是否满足犯困条件
        
        Args:
            idle_minutes: 空闲分钟数
            
        Returns:
            是否应该犯困
        """
        ...
    
    def try_fall_asleep(self) -> bool:
        """尝试入睡（基于概率）
        
        Returns:
            是否成功入睡
        """
        ...
    
    def start_nap(self) -> SleepSession:
        """开始小睡
        
        Returns:
            睡眠会话
        """
        ...
    
    def wake_up(self, reason: WakeReason) -> SleepSession:
        """唤醒
        
        Args:
            reason: 唤醒原因
            
        Returns:
            已结束的睡眠会话
        """
        ...
    
    async def generate_wake_response(
        self, 
        session: SleepSession,
        reason: WakeReason
    ) -> tuple[str, str]:
        """生成唤醒响应
        
        Args:
            session: 睡眠会话
            reason: 唤醒原因
            
        Returns:
            (响应文本, 情感标签)
        """
        ...
    
    def get_sleepy_expressions(self) -> list[str]:
        """获取犯困表情列表
        
        Returns:
            表情名称列表
        """
        ...
    
    def get_sleep_expressions(self) -> list[str]:
        """获取睡眠表情列表
        
        Returns:
            表情名称列表
        """
        ...
    
    def register_state_change_callback(
        self, 
        callback: Callable[[SleepState, SleepState], None]
    ) -> None:
        """注册状态变化回调
        
        Args:
            callback: 回调函数(旧状态, 新状态)
        """
        ...
```

### 3.16 LauncherManager - 程序快速启动器

```python
"""程序快速启动器 - 管理和启动用户配置的应用程序"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import subprocess

if TYPE_CHECKING:
    from ..ai.response_generator import ResponseGenerator


class AppCategory(str, Enum):
    """应用分类"""
    BROWSER = "browser"
    DEVELOPMENT = "development"
    GAME = "game"
    OFFICE = "office"
    MEDIA = "media"
    COMMUNICATION = "communication"
    UTILITY = "utility"
    OTHER = "other"


@dataclass
class AppConfig:
    """应用配置"""
    name: str
    path: str
    category: AppCategory
    icon: str = "🚀"
    args: list[str] = field(default_factory=list)
    working_dir: Optional[str] = None


@dataclass
class LaunchResult:
    """启动结果"""
    success: bool
    app_name: str
    message: str
    error: Optional[str] = None


class LauncherManager:
    """程序启动器管理器
    
    Attributes:
        response_generator: AI响应生成器
        apps: 已配置的应用列表
        config_path: 配置文件路径
    """
    
    def __init__(
        self,
        response_generator: ResponseGenerator,
        config_path: str = "./config/launcher.json"
    ) -> None:
        """初始化启动器
        
        Args:
            response_generator: 响应生成器
            config_path: 配置文件路径
        """
        ...
    
    def get_app_list(self) -> list[AppConfig]:
        """获取应用列表
        
        Returns:
            应用配置列表
        """
        ...
    
    def get_apps_by_category(self, category: AppCategory) -> list[AppConfig]:
        """按分类获取应用
        
        Args:
            category: 应用分类
            
        Returns:
            应用列表
        """
        ...
    
    def launch_app(self, app_name: str) -> LaunchResult:
        """启动应用
        
        Args:
            app_name: 应用名称
            
        Returns:
            启动结果
        """
        ...
    
    def launch_app_by_path(self, path: str, args: list[str] = None) -> LaunchResult:
        """通过路径启动应用
        
        Args:
            path: 应用路径
            args: 启动参数
            
        Returns:
            启动结果
        """
        ...
    
    async def generate_launch_feedback(self, result: LaunchResult) -> tuple[str, str]:
        """生成启动反馈
        
        Args:
            result: 启动结果
            
        Returns:
            (反馈文本, 情感标签)
        """
        ...
    
    def add_app(self, app: AppConfig) -> bool:
        """添加应用
        
        Args:
            app: 应用配置
            
        Returns:
            是否成功
        """
        ...
    
    def remove_app(self, app_name: str) -> bool:
        """移除应用
        
        Args:
            app_name: 应用名称
            
        Returns:
            是否成功
        """
        ...
    
    def validate_app_path(self, path: str) -> bool:
        """验证应用路径
        
        Args:
            path: 应用路径
            
        Returns:
            路径是否有效
        """
        ...
```

### 3.17 BookmarksManager - 网站快捷访问

```python
"""网站快捷访问管理器 - 管理和打开用户收藏的网站"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass, field
from enum import Enum
import webbrowser

if TYPE_CHECKING:
    from ..ai.response_generator import ResponseGenerator


class SiteCategory(str, Enum):
    """网站分类"""
    VIDEO = "video"
    DEVELOPMENT = "development"
    AI = "ai"
    SOCIAL = "social"
    NEWS = "news"
    SHOPPING = "shopping"
    ENTERTAINMENT = "entertainment"
    REFERENCE = "reference"
    OTHER = "other"


@dataclass
class BookmarkConfig:
    """书签配置"""
    name: str
    url: str
    category: SiteCategory
    icon: str = "🔗"
    description: Optional[str] = None


class BookmarksManager:
    """书签管理器
    
    Attributes:
        response_generator: AI响应生成器
        bookmarks: 书签列表
        config_path: 配置文件路径
    """
    
    def __init__(
        self,
        response_generator: ResponseGenerator,
        config_path: str = "./config/bookmarks.json"
    ) -> None:
        """初始化书签管理器
        
        Args:
            response_generator: 响应生成器
            config_path: 配置文件路径
        """
        ...
    
    def get_bookmarks(self) -> list[BookmarkConfig]:
        """获取所有书签
        
        Returns:
            书签列表
        """
        ...
    
    def get_bookmarks_by_category(self, category: SiteCategory) -> list[BookmarkConfig]:
        """按分类获取书签
        
        Args:
            category: 分类
            
        Returns:
            书签列表
        """
        ...
    
    def open_bookmark(self, name: str) -> bool:
        """打开书签
        
        Args:
            name: 书签名称
            
        Returns:
            是否成功
        """
        ...
    
    def open_url(self, url: str) -> bool:
        """打开URL
        
        Args:
            url: 网址
            
        Returns:
            是否成功
        """
        ...
    
    async def generate_navigation_message(self, bookmark: BookmarkConfig) -> tuple[str, str]:
        """生成导航消息
        
        Args:
            bookmark: 书签
            
        Returns:
            (消息文本, 情感标签)
        """
        ...
    
    def add_bookmark(self, bookmark: BookmarkConfig) -> bool:
        """添加书签
        
        Args:
            bookmark: 书签配置
            
        Returns:
            是否成功
        """
        ...
    
    def remove_bookmark(self, name: str) -> bool:
        """移除书签
        
        Args:
            name: 书签名称
            
        Returns:
            是否成功
        """
        ...
    
    def search_bookmarks(self, query: str) -> list[BookmarkConfig]:
        """搜索书签
        
        Args:
            query: 搜索词
            
        Returns:
            匹配的书签
        """
        ...
```

### 3.18 MinigamesManager - 猜拳与掷骰子

```python
"""小游戏管理器 - 管理猜拳、掷骰子等小游戏"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass, field
from enum import Enum
import random

if TYPE_CHECKING:
    from ..ai.response_generator import ResponseGenerator
    from ..features.economy_manager import EconomyManager
    from ..features.affinity_manager import AffinityManager


class RPSChoice(str, Enum):
    """猜拳选择"""
    ROCK = "rock"
    PAPER = "paper"
    SCISSORS = "scissors"


class GameResult(str, Enum):
    """游戏结果"""
    WIN = "win"
    LOSE = "lose"
    DRAW = "draw"


@dataclass
class GameOutcome:
    """游戏结果"""
    game_name: str
    player_choice: Optional[str]
    pet_choice: str
    result: GameResult
    coins_change: int = 0
    affinity_change: int = 0
    streak_info: Optional[str] = None


@dataclass
class DailyRewardStatus:
    """每日奖励状态"""
    remaining_rewards: int
    next_reset_time: str


class MinigamesManager:
    """小游戏管理器
    
    Attributes:
        response_generator: AI响应生成器
        economy_manager: 经济系统管理器
        affinity_manager: 好感度管理器
        daily_reward_count: 今日已奖励次数
        win_streak: 连胜次数
        lose_streak: 连败次数
    """
    
    def __init__(
        self,
        response_generator: ResponseGenerator,
        economy_manager: EconomyManager,
        affinity_manager: AffinityManager,
        config_path: str = "./config/minigame_settings.json"
    ) -> None:
        """初始化小游戏管理器
        
        Args:
            response_generator: 响应生成器
            economy_manager: 经济管理器
            affinity_manager: 好感度管理器
            config_path: 配置文件路径
        """
        ...
    
    def play_rps(self, player_choice: RPSChoice) -> GameOutcome:
        """玩猜拳
        
        Args:
            player_choice: 玩家选择
            
        Returns:
            游戏结果
        """
        ...
    
    def play_dice(self) -> GameOutcome:
        """玩掷骰子
        
        Returns:
            游戏结果
        """
        ...
    
    def _determine_rps_result(
        self, 
        player: RPSChoice, 
        pet: RPSChoice
    ) -> GameResult:
        """判断猜拳结果
        
        Args:
            player: 玩家选择
            pet: 桌宠选择
            
        Returns:
            游戏结果
        """
        ...
    
    def _apply_rewards(self, outcome: GameOutcome) -> None:
        """应用奖励
        
        Args:
            outcome: 游戏结果
        """
        ...
    
    def check_daily_reward_available(self) -> bool:
        """检查每日奖励是否可用
        
        Returns:
            是否可用
        """
        ...
    
    def get_daily_reward_status(self) -> DailyRewardStatus:
        """获取每日奖励状态
        
        Returns:
            奖励状态
        """
        ...
    
    async def generate_game_response(self, outcome: GameOutcome) -> tuple[str, str]:
        """生成游戏响应
        
        Args:
            outcome: 游戏结果
            
        Returns:
            (响应文本, 情感标签)
        """
        ...
    
    def get_streak_info(self) -> dict[str, int]:
        """获取连胜/连败信息
        
        Returns:
            {"win_streak": n, "lose_streak": m}
        """
        ...
    
    def reset_daily_rewards(self) -> None:
        """重置每日奖励"""
        ...
```

### 3.19 FileOrganizerManager - 本地文件整理

```python
"""本地文件整理管理器 - 按规则整理文件"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path
import shutil

if TYPE_CHECKING:
    from ..ai.response_generator import ResponseGenerator


@dataclass
class CategoryRule:
    """分类规则"""
    name: str
    extensions: list[str]
    target_folder: str


@dataclass
class OrganizeProgress:
    """整理进度"""
    total_files: int
    processed_files: int
    current_file: Optional[str]
    percentage: float


@dataclass
class OrganizeResult:
    """整理结果"""
    success: bool
    total_files: int
    moved_files: dict[str, int]  # {分类: 数量}
    errors: list[str]
    duration_seconds: float


class FileOrganizerManager:
    """文件整理管理器
    
    Attributes:
        response_generator: AI响应生成器
        category_rules: 分类规则
        on_progress: 进度回调
    """
    
    def __init__(
        self,
        response_generator: ResponseGenerator,
        config_path: str = "./config/file_organizer_settings.json"
    ) -> None:
        """初始化文件整理器
        
        Args:
            response_generator: 响应生成器
            config_path: 配置文件路径
        """
        ...
    
    def get_category_rules(self) -> list[CategoryRule]:
        """获取分类规则
        
        Returns:
            规则列表
        """
        ...
    
    def add_category_rule(self, rule: CategoryRule) -> bool:
        """添加分类规则
        
        Args:
            rule: 规则
            
        Returns:
            是否成功
        """
        ...
    
    def scan_directory(self, source_dir: str) -> dict[str, list[str]]:
        """扫描目录
        
        Args:
            source_dir: 源目录
            
        Returns:
            {分类: [文件路径]}
        """
        ...
    
    async def organize(
        self, 
        source_dir: str, 
        target_dir: str,
        progress_callback: Optional[Callable[[OrganizeProgress], None]] = None
    ) -> OrganizeResult:
        """整理文件
        
        Args:
            source_dir: 源目录
            target_dir: 目标目录
            progress_callback: 进度回调
            
        Returns:
            整理结果
        """
        ...
    
    def preview_organize(self, source_dir: str) -> dict[str, list[str]]:
        """预览整理结果
        
        Args:
            source_dir: 源目录
            
        Returns:
            {分类: [文件名]}
        """
        ...
    
    async def generate_completion_report(self, result: OrganizeResult) -> tuple[str, str]:
        """生成完成报告
        
        Args:
            result: 整理结果
            
        Returns:
            (报告文本, 情感标签)
        """
        ...
    
    def undo_last_organize(self) -> bool:
        """撤销上次整理
        
        Returns:
            是否成功
        """
        ...
    
    def register_progress_callback(
        self, 
        callback: Callable[[OrganizeProgress], None]
    ) -> None:
        """注册进度回调
        
        Args:
            callback: 回调函数
        """
        ...
```

### 3.20 EconomyManager - 商城与经济系统

```python
"""商城与经济系统管理器 - 管理金币、商城和购买"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, date

if TYPE_CHECKING:
    from ..state.user_state_manager import UserStateManager


class ItemCategory(str, Enum):
    """商品分类"""
    FOOD = "food"
    CLOTHING = "clothing"
    FURNITURE = "furniture"
    CONSUMABLE = "consumable"
    SPECIAL = "special"


class CurrencyChangeReason(str, Enum):
    """货币变化原因"""
    FOCUS_REWARD = "focus_reward"
    SCHEDULE_COMPLETE = "schedule_complete"
    DAILY_CHECKIN = "daily_checkin"
    GAME_REWARD = "game_reward"
    RANDOM_EVENT = "random_event"
    PURCHASE = "purchase"
    ADMIN_ADJUST = "admin_adjust"


@dataclass
class ShopItem:
    """商品"""
    id: str
    name: str
    category: ItemCategory
    price: int
    description: str
    icon: str
    is_limited: bool = False
    stock: Optional[int] = None


@dataclass
class PurchaseResult:
    """购买结果"""
    success: bool
    item: Optional[ShopItem]
    message: str
    new_balance: int


@dataclass
class CheckinReward:
    """签到奖励"""
    coins: int
    streak_days: int
    bonus_coins: int  # 连续签到奖励


class EconomyManager:
    """经济系统管理器
    
    Attributes:
        state_manager: 状态管理器
        shop_items: 商品列表
        daily_limits: 每日限制
    """
    
    def __init__(
        self,
        state_manager: UserStateManager,
        config_path: str = "./config/economy_settings.json"
    ) -> None:
        """初始化经济系统
        
        Args:
            state_manager: 状态管理器
            config_path: 配置文件路径
        """
        ...
    
    def get_balance(self) -> int:
        """获取当前余额
        
        Returns:
            金币数量
        """
        ...
    
    def add_coins(self, amount: int, reason: CurrencyChangeReason) -> int:
        """增加金币
        
        Args:
            amount: 数量
            reason: 原因
            
        Returns:
            新余额
        """
        ...
    
    def remove_coins(self, amount: int, reason: CurrencyChangeReason) -> bool:
        """扣除金币
        
        Args:
            amount: 数量
            reason: 原因
            
        Returns:
            是否成功
        """
        ...
    
    def get_shop_items(self, category: Optional[ItemCategory] = None) -> list[ShopItem]:
        """获取商品列表
        
        Args:
            category: 分类筛选
            
        Returns:
            商品列表
        """
        ...
    
    def purchase_item(self, item_id: str) -> PurchaseResult:
        """购买商品
        
        Args:
            item_id: 商品ID
            
        Returns:
            购买结果
        """
        ...
    
    def daily_checkin(self) -> CheckinReward:
        """每日签到
        
        Returns:
            签到奖励
        """
        ...
    
    def is_checkin_available(self) -> bool:
        """是否可以签到
        
        Returns:
            是否可用
        """
        ...
    
    def get_checkin_streak(self) -> int:
        """获取连续签到天数
        
        Returns:
            天数
        """
        ...
    
    def check_daily_limit(self, source: str) -> bool:
        """检查每日限制
        
        Args:
            source: 来源类型
            
        Returns:
            是否还有额度
        """
        ...
    
    def get_transaction_history(self, limit: int = 20) -> list[dict]:
        """获取交易历史
        
        Args:
            limit: 数量限制
            
        Returns:
            交易记录列表
        """
        ...
```

### 3.21 NetworkMonitorManager - 网络延迟感知

```python
"""网络延迟感知管理器 - 监控网络状态并生成反应"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import asyncio

if TYPE_CHECKING:
    from ..ai.response_generator import ResponseGenerator


class NetworkStatus(str, Enum):
    """网络状态"""
    NORMAL = "normal"
    HIGH_LATENCY = "high_latency"
    DISCONNECTED = "disconnected"
    RECOVERING = "recovering"


@dataclass
class NetworkState:
    """网络状态"""
    status: NetworkStatus
    latency_ms: Optional[int]
    last_check_time: float
    consecutive_failures: int = 0


class NetworkMonitorManager:
    """网络监控管理器
    
    Attributes:
        response_generator: AI响应生成器
        current_state: 当前网络状态
        is_monitoring: 是否正在监控
        on_status_change: 状态变化回调
    """
    
    def __init__(
        self,
        response_generator: ResponseGenerator,
        config_path: str = "./config/network_settings.json"
    ) -> None:
        """初始化网络监控器
        
        Args:
            response_generator: 响应生成器
            config_path: 配置文件路径
        """
        ...
    
    def start_monitoring(self) -> None:
        """开始监控"""
        ...
    
    def stop_monitoring(self) -> None:
        """停止监控"""
        ...
    
    async def check_network(self) -> NetworkState:
        """检查网络状态
        
        Returns:
            网络状态
        """
        ...
    
    async def ping(self, target: str = "baidu.com") -> Optional[int]:
        """Ping测试
        
        Args:
            target: 目标地址
            
        Returns:
            延迟毫秒，失败返回None
        """
        ...
    
    def get_current_state(self) -> NetworkState:
        """获取当前状态
        
        Returns:
            网络状态
        """
        ...
    
    async def generate_status_reaction(
        self, 
        old_status: NetworkStatus, 
        new_status: NetworkStatus,
        latency: Optional[int] = None
    ) -> tuple[str, str]:
        """生成状态变化反应
        
        Args:
            old_status: 旧状态
            new_status: 新状态
            latency: 延迟
            
        Returns:
            (反应文本, 情感标签)
        """
        ...
    
    def get_status_expression(self, status: NetworkStatus) -> str:
        """获取状态对应表情
        
        Args:
            status: 网络状态
            
        Returns:
            表情名称
        """
        ...
    
    def register_status_callback(
        self, 
        callback: Callable[[NetworkStatus, NetworkStatus], None]
    ) -> None:
        """注册状态变化回调
        
        Args:
            callback: 回调函数(旧状态, 新状态)
        """
        ...
```

### 3.22 GamingModeManager - 游戏模式侦测

```python
"""游戏模式侦测管理器 - 检测用户游戏状态并调整行为"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

if TYPE_CHECKING:
    from ..ai.response_generator import ResponseGenerator


class GamingModeBehavior(str, Enum):
    """游戏模式行为"""
    MINIMIZE_TRAY = "minimize_tray"
    MINIMIZE_CORNER = "minimize_corner"
    CHEER_SILENT = "cheer_silent"


@dataclass
class GamingSession:
    """游戏会话"""
    game_name: str
    game_category: Optional[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: int = 0


class GamingModeManager:
    """游戏模式管理器
    
    Attributes:
        response_generator: AI响应生成器
        game_whitelist: 游戏进程白名单
        is_gaming: 是否在游戏中
        current_session: 当前游戏会话
        on_mode_change: 模式变化回调
    """
    
    def __init__(
        self,
        response_generator: ResponseGenerator,
        config_path: str = "./config/gaming_mode_settings.json"
    ) -> None:
        """初始化游戏模式管理器
        
        Args:
            response_generator: 响应生成器
            config_path: 配置文件路径
        """
        ...
    
    def start_monitoring(self) -> None:
        """开始监控"""
        ...
    
    def stop_monitoring(self) -> None:
        """停止监控"""
        ...
    
    def is_in_gaming_mode(self) -> bool:
        """是否在游戏模式
        
        Returns:
            是否在游戏
        """
        ...
    
    def check_gaming_process(self) -> Optional[str]:
        """检查游戏进程
        
        Returns:
            检测到的游戏名称，无则返回None
        """
        ...
    
    def enter_gaming_mode(self, game_name: str) -> GamingSession:
        """进入游戏模式
        
        Args:
            game_name: 游戏名称
            
        Returns:
            游戏会话
        """
        ...
    
    def exit_gaming_mode(self) -> GamingSession:
        """退出游戏模式
        
        Returns:
            已结束的游戏会话
        """
        ...
    
    async def generate_exit_greeting(self, session: GamingSession) -> tuple[str, str]:
        """生成退出问候
        
        Args:
            session: 游戏会话
            
        Returns:
            (问候文本, 情感标签)
        """
        ...
    
    def get_behavior_on_detect(self) -> GamingModeBehavior:
        """获取检测到游戏时的行为
        
        Returns:
            行为类型
        """
        ...
    
    def add_to_whitelist(self, process_name: str, category: Optional[str] = None) -> bool:
        """添加到白名单
        
        Args:
            process_name: 进程名
            category: 分类
            
        Returns:
            是否成功
        """
        ...
    
    def remove_from_whitelist(self, process_name: str) -> bool:
        """从白名单移除
        
        Args:
            process_name: 进程名
            
        Returns:
            是否成功
        """
        ...
    
    def register_mode_callback(
        self, 
        callback: Callable[[bool, Optional[GamingSession]], None]
    ) -> None:
        """注册模式变化回调
        
        Args:
            callback: 回调函数(是否游戏中, 会话)
        """
        ...
```

### 3.24 QuickNotesManager - 随手记/便签条

```python
"""随手记/便签管理器 - 管理用户的快速笔记"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass, field
from datetime import datetime
import random

if TYPE_CHECKING:
    from ..ai.response_generator import ResponseGenerator


@dataclass
class Note:
    """便签"""
    id: str
    content: str
    created_at: datetime
    keywords: list[str] = field(default_factory=list)
    is_recalled: bool = False  # 是否被回忆过
    recall_count: int = 0


@dataclass
class RecallEvent:
    """回忆事件"""
    note: Note
    age_days: int
    context_match: bool  # 是否与当前上下文相关


class QuickNotesManager:
    """便签管理器
    
    Attributes:
        response_generator: AI响应生成器
        notes: 便签列表
        notes_file_path: 便签文件路径
    """
    
    def __init__(
        self,
        response_generator: ResponseGenerator,
        config_path: str = "./config/notes_settings.json"
    ) -> None:
        """初始化便签管理器
        
        Args:
            response_generator: 响应生成器
            config_path: 配置文件路径
        """
        ...
    
    def add_note(self, content: str) -> Note:
        """添加便签
        
        Args:
            content: 内容
            
        Returns:
            创建的便签
        """
        ...
    
    def get_all_notes(self) -> list[Note]:
        """获取所有便签
        
        Returns:
            便签列表
        """
        ...
    
    def search_notes(self, query: str) -> list[Note]:
        """搜索便签
        
        Args:
            query: 搜索词
            
        Returns:
            匹配的便签
        """
        ...
    
    def delete_note(self, note_id: str) -> bool:
        """删除便签
        
        Args:
            note_id: 便签ID
            
        Returns:
            是否成功
        """
        ...
    
    def get_random_note(self) -> Optional[Note]:
        """获取随机便签
        
        Returns:
            随机便签，无则返回None
        """
        ...
    
    def should_recall(self) -> bool:
        """是否应该触发回忆
        
        Returns:
            是否触发
        """
        ...
    
    def trigger_recall(self, context: Optional[str] = None) -> Optional[RecallEvent]:
        """触发回忆
        
        Args:
            context: 当前上下文
            
        Returns:
            回忆事件
        """
        ...
    
    async def generate_recall_message(self, event: RecallEvent) -> tuple[str, str]:
        """生成回忆消息
        
        Args:
            event: 回忆事件
            
        Returns:
            (消息文本, 情感标签)
        """
        ...
    
    def _extract_keywords(self, content: str) -> list[str]:
        """提取关键词
        
        Args:
            content: 内容
            
        Returns:
            关键词列表
        """
        ...
    
    def _save_notes(self) -> None:
        """保存便签到文件"""
        ...
    
    def _load_notes(self) -> None:
        """从文件加载便签"""
        ...
```

### 3.25 WeatherManager - 本地天气感知

```python
"""本地天气感知管理器 - 获取天气信息并影响桌宠表现"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import httpx

if TYPE_CHECKING:
    from ..ai.response_generator import ResponseGenerator


class WeatherCondition(str, Enum):
    """天气状况"""
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    SNOW = "snow"
    STORM = "storm"
    FOG = "fog"
    HOT = "hot"
    COLD = "cold"


@dataclass
class WeatherData:
    """天气数据"""
    condition: WeatherCondition
    temperature: float
    humidity: int
    description: str
    city: str
    update_time: float


@dataclass
class WeatherEffect:
    """天气效果"""
    expression: str  # 表情
    overlay: Optional[str]  # 叠加图层
    particle_effect: Optional[str]  # 粒子效果


class WeatherManager:
    """天气管理器
    
    Attributes:
        response_generator: AI响应生成器
        current_weather: 当前天气
        city: 城市
        on_weather_change: 天气变化回调
    """
    
    def __init__(
        self,
        response_generator: ResponseGenerator,
        config_path: str = "./config/weather_settings.json"
    ) -> None:
        """初始化天气管理器
        
        Args:
            response_generator: 响应生成器
            config_path: 配置文件路径
        """
        ...
    
    def set_city(self, city: str) -> None:
        """设置城市
        
        Args:
            city: 城市名称
        """
        ...
    
    async def fetch_weather(self) -> WeatherData:
        """获取天气
        
        Returns:
            天气数据
        """
        ...
    
    def get_current_weather(self) -> Optional[WeatherData]:
        """获取当前缓存的天气
        
        Returns:
            天气数据，无则返回None
        """
        ...
    
    def get_weather_effect(self, weather: WeatherData) -> WeatherEffect:
        """获取天气效果
        
        Args:
            weather: 天气数据
            
        Returns:
            天气效果
        """
        ...
    
    async def generate_weather_comment(self, weather: WeatherData) -> tuple[str, str]:
        """生成天气评论
        
        Args:
            weather: 天气数据
            
        Returns:
            (评论文本, 情感标签)
        """
        ...
    
    def is_extreme_weather(self, weather: WeatherData) -> bool:
        """是否极端天气
        
        Args:
            weather: 天气数据
            
        Returns:
            是否极端
        """
        ...
    
    def should_update(self) -> bool:
        """是否应该更新天气
        
        Returns:
            是否需要更新
        """
        ...
    
    def register_weather_callback(
        self, 
        callback: Callable[[WeatherData, WeatherData], None]
    ) -> None:
        """注册天气变化回调
        
        Args:
            callback: 回调函数(旧天气, 新天气)
        """
        ...
```

### 3.26 EasterEggsManager - 彩蛋与隐藏指令

```python
"""彩蛋与隐藏指令管理器 - 管理特殊交互和隐藏功能"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Callable
from dataclasses import dataclass, field
from datetime import date
from enum import Enum

if TYPE_CHECKING:
    from ..ai.response_generator import ResponseGenerator
    from ..state.user_state_manager import UserStateManager


class EasterEggType(str, Enum):
    """彩蛋类型"""
    CLICK_COMBO = "click_combo"
    DRAG_OFF_SCREEN = "drag_off_screen"
    SPECIAL_DATE = "special_date"
    HIDDEN_COMMAND = "hidden_command"
    GROWTH_MILESTONE = "growth_milestone"


@dataclass
class EasterEgg:
    """彩蛋定义"""
    id: str
    type: EasterEggType
    name: str
    description: str
    trigger_condition: str
    reward: Optional[dict] = None
    is_discovered: bool = False


@dataclass
class HiddenCommand:
    """隐藏指令"""
    command: str
    action: str
    description: str


@dataclass
class GrowthMilestone:
    """成长里程碑"""
    days: int
    stage: str
    unlock: str
    achieved: bool = False


class EasterEggsManager:
    """彩蛋管理器
    
    Attributes:
        response_generator: AI响应生成器
        state_manager: 状态管理器
        discovered_eggs: 已发现的彩蛋
        click_count: 连续点击计数
        on_egg_discovered: 彩蛋发现回调
    """
    
    def __init__(
        self,
        response_generator: ResponseGenerator,
        state_manager: UserStateManager,
        config_path: str = "./config/easter_eggs_settings.json"
    ) -> None:
        """初始化彩蛋管理器
        
        Args:
            response_generator: 响应生成器
            state_manager: 状态管理器
            config_path: 配置文件路径
        """
        ...
    
    def record_click(self) -> Optional[EasterEgg]:
        """记录点击
        
        Returns:
            触发的彩蛋，无则返回None
        """
        ...
    
    def check_drag_off_screen(self, x: int, y: int, screen_bounds: tuple) -> Optional[EasterEgg]:
        """检查拖出屏幕
        
        Args:
            x: X坐标
            y: Y坐标
            screen_bounds: 屏幕边界 (width, height)
            
        Returns:
            触发的彩蛋
        """
        ...
    
    def check_special_date(self) -> Optional[EasterEgg]:
        """检查特殊日期
        
        Returns:
            触发的彩蛋
        """
        ...
    
    def process_command(self, text: str) -> Optional[tuple[HiddenCommand, str]]:
        """处理隐藏指令
        
        Args:
            text: 输入文本
            
        Returns:
            (指令, 执行结果)
        """
        ...
    
    def check_growth_milestone(self, interaction_days: int) -> Optional[GrowthMilestone]:
        """检查成长里程碑
        
        Args:
            interaction_days: 互动天数
            
        Returns:
            达成的里程碑
        """
        ...
    
    def get_discovered_eggs(self) -> list[EasterEgg]:
        """获取已发现的彩蛋
        
        Returns:
            彩蛋列表
        """
        ...
    
    def get_discovery_progress(self) -> tuple[int, int]:
        """获取发现进度
        
        Returns:
            (已发现数, 总数)
        """
        ...
    
    async def generate_egg_response(self, egg: EasterEgg) -> tuple[str, str, Optional[str]]:
        """生成彩蛋响应
        
        Args:
            egg: 彩蛋
            
        Returns:
            (响应文本, 情感标签, 特殊动画)
        """
        ...
    
    def register_discovery_callback(
        self, 
        callback: Callable[[EasterEgg], None]
    ) -> None:
        """注册发现回调
        
        Args:
            callback: 回调函数
        """
        ...
    
    def is_command(self, text: str) -> bool:
        """是否是隐藏指令
        
        Args:
            text: 输入文本
            
        Returns:
            是否是指令
        """
        ...
```

---

## 4. 数据模型

### 4.1 Schedule - 日程模型

```python
"""日程数据模型"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class ReminderType(str, Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


class ScheduleModel(BaseModel):
    """日程数据模型"""
    id: str = Field(..., description="日程ID")
    title: str = Field(..., description="日程标题")
    datetime: datetime = Field(..., description="日程时间")
    reminder_type: ReminderType = Field(default=ReminderType.ONCE)
    advance_minutes: int = Field(default=5, ge=0, le=60)
    message: Optional[str] = Field(default=None)
    is_completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True
```

### 4.2 Item - 物品模型

```python
"""物品数据模型"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ItemAttributesModel(BaseModel):
    """物品属性"""
    taste: List[str] = Field(default_factory=list)
    texture: str = Field(default="")
    temperature: str = Field(default="room")
    size: str = Field(default="medium")
    color: str = Field(default="")
    freshness: str = Field(default="fresh")


class ItemEffectsModel(BaseModel):
    """物品效果"""
    affinity_bonus: int = Field(default=0)
    mood_impact: float = Field(default=0.0)
    energy_restore: int = Field(default=0)
    hunger_restore: int = Field(default=10)


class ItemModel(BaseModel):
    """物品"""
    id: str
    display_name: str
    icon: str
    quantity: int = Field(default=0, ge=0)
    category: str
    attributes: ItemAttributesModel = Field(default_factory=ItemAttributesModel)
    effects: ItemEffectsModel = Field(default_factory=ItemEffectsModel)
    context_tags: List[str] = Field(default_factory=list)
    animation_override: Optional[str] = Field(default=None)
```

---

## 5. 配置文件

### 5.1 功能配置汇总

各功能的配置文件已在PRD中定义，主要包括：

- `chat_settings.json` - 聊天记录
- `chime_settings.json` - 整点报时
- `focus_settings.json` - 专注时钟
- `schedule_settings.json` - 日程管理
- `random_event_settings.json` - 随机事件
- `idle_chat_settings.json` - 闲聊
- `physics_settings.json` - 物理交互
- `system_monitor_settings.json` - 系统监控

---

## 6. 测试要点

| 功能 | 测试项 | 预期结果 |
|------|--------|----------|
| 聊天记录 | 添加/删除/搜索 | 正确持久化 |
| 整点报时 | 准点触发 | 误差<1秒 |
| 专注时钟 | 黑名单检测 | 正确识别分心应用 |
| 背包系统 | 物品使用 | 正确应用效果 |
| 日程 | 提前提醒 | 按设定时间提醒 |
| 随机事件 | AI生成 | 生成有效事件 |
| 系统监控 | 阈值警告 | 超阈值触发警告 |

---

> **文档版本**: v1.0.0
> **生成时间**: 2025-12-29
> **生成工具**: Claude Opus 4
