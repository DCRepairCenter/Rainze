# MOD-Tools - 工具调用模块

> **模块版本**: v1.0.0
> **创建时间**: 2025-12-30
> **关联PRD**: PRD-Rainze.md v3.0.3 §0.10
> **关联技术栈**: TECH-Rainze.md v1.0.1
> **模块层级**: 业务层 (Business Layer)
> **优先级**: P1 (核心体验)
> **依赖模块**: Core, AI, State

---

## 1. 模块概述

### 1.1 职责定义

| 维度 | 说明 |
|------|------|
| **核心职责** | 实现ReAct模式的工具调用，让桌宠能执行实际操作 |
| **技术栈** | asyncio、subprocess、webbrowser、httpx |
| **对外接口** | ToolRegistry、ToolExecutor、ReActEngine |
| **依赖模块** | Core (事件总线)、AI (LLM调用)、State (状态更新) |
| **被依赖于** | Agent (工具路由)、Plugins (扩展工具) |

### 1.2 ReAct模式架构

```
[用户意图识别] → [工具选择] → [ReAct循环]
                                   │
       ┌───────────────────────────┼───────────────────────────┐
       ↓                           ↓                           ↓
  [Thought]                   [Action]                   [Observation]
   LLM判断                    执行工具                    收集结果
       │                           │                           │
       └───────────────────────────┴───────────────────────────┘
                                   │
                                   ↓
                          [最终回复生成]
```

### 1.3 PRD映射

| PRD章节 | 内容概要 | 本模块覆盖 |
|---------|----------|------------|
| §0.10 Tool Use能力 | ReAct模式、首批工具、错误处理 | ✅ 完整覆盖 |
| §0.6 降级链 | 工具失败时的降级策略 | 错误恢复 |
| 第一部分 §16 | 程序快速启动器 | app_launcher工具 |
| 第一部分 §17 | 网站快捷访问 | bookmark工具 |

### 1.4 首批工具清单

| 工具名称 | 功能 | 触发示例 |
|----------|------|----------|
| `system_reminder` | 设置系统提醒/闹钟 | "提醒我明天早上8点开会" |
| `weather_query` | 查询天气信息 | "明天天气怎么样" |
| `app_launcher` | 启动应用程序 | "帮我打开VS Code" |
| `note_manager` | 管理便签笔记 | "帮我记一下明天要买牛奶" |
| `web_search` | 简单网页搜索 (可选) | "帮我搜一下Python教程" |

---

## 2. 目录结构

```
src/rainze/tools/
├── __init__.py
├── registry.py             # ToolRegistry 工具注册表
├── executor.py             # ToolExecutor 工具执行器
├── react_engine.py         # ReActEngine ReAct引擎
├── builtin/                # 内置工具实现
│   ├── __init__.py
│   ├── base_tool.py        # BaseTool 工具基类
│   ├── reminder.py         # SystemReminderTool 提醒工具
│   ├── weather.py          # WeatherQueryTool 天气工具
│   ├── launcher.py         # AppLauncherTool 启动器工具
│   ├── note.py             # NoteManagerTool 便签工具
│   └── web_search.py       # WebSearchTool 搜索工具
├── error_handling/         # 错误处理
│   ├── __init__.py
│   ├── retry.py            # RetryStrategy 重试策略
│   ├── fallback.py         # ToolFallback 降级处理
│   └── rollback.py         # StateRollback 状态回滚
├── cache/                  # 工具缓存
│   ├── __init__.py
│   └── result_cache.py     # ToolResultCache 结果缓存
├── confirmation/           # 确认机制
│   ├── __init__.py
│   └── high_risk.py        # HighRiskConfirmation 高风险操作确认
└── models/                 # 数据模型
    ├── __init__.py
    ├── tool.py             # 工具定义模型
    ├── execution.py        # 执行结果模型
    └── config.py           # 配置模型
```

---

## 3. 核心类设计

### 3.1 BaseTool - 工具基类

```python
"""工具基类

所有工具必须继承此类，实现execute方法。

PRD映射: §0.10 Tool Use能力
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum, auto


class ToolCategory(Enum):
    """工具类别"""
    SYSTEM = auto()         # 系统工具 (提醒、启动器)
    QUERY = auto()          # 查询工具 (天气、搜索)
    STORAGE = auto()        # 存储工具 (便签)
    EXTERNAL = auto()       # 外部服务
    CUSTOM = auto()         # 自定义/插件


@dataclass
class ToolSchema:
    """工具Schema定义"""
    name: str
    description: str
    category: ToolCategory
    parameters: Dict[str, "ParameterSchema"]
    required_params: List[str]
    cacheable: bool = False
    cache_ttl_minutes: int = 0
    requires_confirmation: bool = False
    confirmation_message: Optional[str] = None


@dataclass
class ParameterSchema:
    """参数Schema"""
    name: str
    type: str               # "string" | "number" | "boolean" | "array"
    description: str
    required: bool = False
    default: Any = None
    enum: Optional[List[Any]] = None


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    execution_time_ms: int = 0
    cached: bool = False
    requires_retry: bool = False


class BaseTool(ABC):
    """工具基类
    
    Attributes:
        _name: 工具名称
        _schema: 工具Schema
        _enabled: 是否启用
    """
    
    def __init__(self) -> None:
        """初始化工具"""
        ...
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        ...
    
    @property
    @abstractmethod
    def schema(self) -> ToolSchema:
        """工具Schema"""
        ...
    
    @property
    def enabled(self) -> bool:
        """是否启用"""
        ...
    
    @enabled.setter
    def enabled(self, value: bool) -> None:
        ...
    
    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """验证参数
        
        Args:
            params: 输入参数
            
        Returns:
            (是否有效, 错误信息)
        """
        ...
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行工具
        
        Args:
            params: 工具参数
            
        Returns:
            执行结果
        """
        ...
    
    def get_prompt_description(self) -> str:
        """获取用于Prompt的工具描述
        
        Returns:
            JSON格式的工具描述
        """
        ...


### 3.2 ToolRegistry - 工具注册表

```python
"""工具注册表

管理所有可用工具的注册和查找。
"""

from typing import Dict, List, Optional, Type


class ToolRegistry:
    """工具注册表
    
    Attributes:
        _tools: 已注册工具映射 {name: tool_instance}
        _categories: 按类别分组的工具列表
    """
    
    def __init__(self) -> None:
        """初始化注册表"""
        ...
    
    def register(self, tool: "BaseTool") -> None:
        """注册工具
        
        Args:
            tool: 工具实例
            
        Raises:
            ToolAlreadyRegisteredError: 工具名称已存在
        """
        ...
    
    def unregister(self, name: str) -> bool:
        """注销工具
        
        Args:
            name: 工具名称
            
        Returns:
            是否成功注销
        """
        ...
    
    def get(self, name: str) -> Optional["BaseTool"]:
        """获取工具
        
        Args:
            name: 工具名称
            
        Returns:
            工具实例，不存在返回None
        """
        ...
    
    def list_all(self) -> List["BaseTool"]:
        """列出所有工具"""
        ...
    
    def list_by_category(self, category: "ToolCategory") -> List["BaseTool"]:
        """按类别列出工具"""
        ...
    
    def list_enabled(self) -> List["BaseTool"]:
        """列出所有启用的工具"""
        ...
    
    def get_all_schemas(self) -> List["ToolSchema"]:
        """获取所有工具的Schema"""
        ...
    
    def get_prompt_tools_description(self) -> str:
        """生成用于Prompt的工具列表描述
        
        Returns:
            格式化的工具列表字符串
        """
        ...
    
    def register_builtin_tools(self) -> None:
        """注册所有内置工具"""
        ...


### 3.3 ToolExecutor - 工具执行器

```python
"""工具执行器

负责工具的实际执行，包括重试、缓存、错误处理。

PRD映射: §0.10 错误处理与恢复机制
"""

from typing import Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass


@dataclass
class ExecutionContext:
    """执行上下文"""
    tool_name: str
    params: Dict[str, Any]
    attempt: int = 1
    max_attempts: int = 3
    timeout_seconds: int = 10
    trace_id: Optional[str] = None


@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3
    initial_delay_ms: int = 500
    backoff_multiplier: float = 2.0
    max_delay_ms: int = 5000
    retryable_errors: List[str] = field(default_factory=list)


class ToolExecutor:
    """工具执行器
    
    Attributes:
        _registry: 工具注册表
        _cache: 结果缓存
        _retry_config: 重试配置
        _state_manager: 状态管理器（用于回滚）
    """
    
    def __init__(
        self,
        registry: "ToolRegistry",
        cache: "ToolResultCache",
        retry_config: RetryConfig,
        state_manager: Optional["StateManager"] = None,
    ) -> None:
        """初始化执行器
        
        Args:
            registry: 工具注册表
            cache: 结果缓存
            retry_config: 重试配置
            state_manager: 状态管理器
        """
        ...
    
    async def execute(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: Optional[ExecutionContext] = None,
    ) -> "ToolResult":
        """执行工具
        
        完整执行流程:
        1. 查找工具
        2. 验证参数
        3. 检查缓存
        4. 检查是否需要确认
        5. 执行（带重试）
        6. 缓存结果
        7. 返回结果
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            context: 执行上下文
            
        Returns:
            执行结果
        """
        ...
    
    async def execute_with_retry(
        self,
        tool: "BaseTool",
        params: Dict[str, Any],
        context: ExecutionContext,
    ) -> "ToolResult":
        """带重试的执行
        
        使用指数退避策略重试。
        
        Args:
            tool: 工具实例
            params: 参数
            context: 执行上下文
            
        Returns:
            执行结果
        """
        ...
    
    async def _check_cache(
        self,
        tool_name: str,
        params: Dict[str, Any],
    ) -> Optional["ToolResult"]:
        """检查缓存
        
        Args:
            tool_name: 工具名称
            params: 参数
            
        Returns:
            缓存的结果，未命中返回None
        """
        ...
    
    async def _handle_error(
        self,
        tool_name: str,
        error: Exception,
        context: ExecutionContext,
    ) -> "ToolResult":
        """处理执行错误
        
        Args:
            tool_name: 工具名称
            error: 异常
            context: 执行上下文
            
        Returns:
            错误结果
        """
        ...
    
    def register_pre_hook(
        self,
        hook: Callable[[str, Dict[str, Any]], Awaitable[None]],
    ) -> None:
        """注册执行前钩子"""
        ...
    
    def register_post_hook(
        self,
        hook: Callable[["ToolResult"], Awaitable[None]],
    ) -> None:
        """注册执行后钩子"""
        ...


### 3.4 ReActEngine - ReAct推理引擎

```python
"""ReAct推理引擎

实现Reasoning + Acting的循环推理模式。

PRD映射: §0.10 ReAct模式
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum, auto


class ReActStep(Enum):
    """ReAct步骤"""
    THOUGHT = auto()        # 思考
    ACTION = auto()         # 行动
    OBSERVATION = auto()    # 观察


@dataclass
class ReActTurn:
    """ReAct单轮记录"""
    step: ReActStep
    content: str
    tool_name: Optional[str] = None
    tool_params: Optional[Dict[str, Any]] = None
    tool_result: Optional["ToolResult"] = None


@dataclass
class ReActResult:
    """ReAct完整结果"""
    success: bool
    final_response: str
    turns: List[ReActTurn]
    total_tool_calls: int
    total_tokens_used: int
    execution_time_ms: int


class ReActEngine:
    """ReAct推理引擎
    
    Attributes:
        _executor: 工具执行器
        _llm_client: LLM客户端
        _max_iterations: 最大迭代次数
        _attention_manager: 注意力管理器
    """
    
    def __init__(
        self,
        executor: "ToolExecutor",
        llm_client: "LLMClient",
        max_iterations: int = 5,
        max_tool_calls_per_turn: int = 3,
    ) -> None:
        """初始化ReAct引擎
        
        Args:
            executor: 工具执行器
            llm_client: LLM客户端
            max_iterations: 最大迭代次数
            max_tool_calls_per_turn: 每轮最大工具调用数
        """
        ...
    
    async def run(
        self,
        user_input: str,
        context: Dict[str, Any],
    ) -> ReActResult:
        """运行ReAct循环
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            
        Returns:
            ReAct执行结果
        """
        ...
    
    async def _think(
        self,
        history: List[ReActTurn],
        context: Dict[str, Any],
    ) -> tuple[str, Optional[Dict[str, Any]]]:
        """思考步骤
        
        让LLM判断是否需要工具，输出思考过程。
        
        Args:
            history: 历史记录
            context: 上下文
            
        Returns:
            (思考内容, 工具调用JSON或None)
        """
        ...
    
    async def _act(
        self,
        tool_call: Dict[str, Any],
    ) -> "ToolResult":
        """行动步骤
        
        执行工具调用。
        
        Args:
            tool_call: 工具调用信息 {"tool": name, "params": {...}}
            
        Returns:
            工具执行结果
        """
        ...
    
    async def _observe(
        self,
        result: "ToolResult",
    ) -> str:
        """观察步骤
        
        处理工具结果，生成观察描述。
        
        Args:
            result: 工具执行结果
            
        Returns:
            观察描述
        """
        ...
    
    async def _generate_final_response(
        self,
        history: List[ReActTurn],
        context: Dict[str, Any],
    ) -> str:
        """生成最终响应
        
        基于所有执行历史生成用户可见的最终回复。
        
        Args:
            history: 执行历史
            context: 上下文
            
        Returns:
            最终响应文本
        """
        ...
    
    def _check_should_continue(
        self,
        history: List[ReActTurn],
        iteration: int,
    ) -> bool:
        """检查是否应继续迭代
        
        Args:
            history: 执行历史
            iteration: 当前迭代次数
            
        Returns:
            是否继续
        """
        ...
    
    def _build_react_prompt(
        self,
        user_input: str,
        history: List[ReActTurn],
        available_tools: List["ToolSchema"],
    ) -> str:
        """构建ReAct Prompt
        
        Args:
            user_input: 用户输入
            history: 执行历史
            available_tools: 可用工具列表
            
        Returns:
            完整Prompt
        """
        ...


### 3.5 HighRiskConfirmation - 高风险操作确认

```python
"""高风险操作确认

对危险操作要求用户确认后执行。

PRD映射: §0.10 高风险操作确认
"""

from typing import Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass


@dataclass
class ConfirmationRequest:
    """确认请求"""
    tool_name: str
    operation: str
    message: str
    details: Optional[str] = None
    timeout_seconds: int = 30
    default_on_timeout: str = "cancel"  # "cancel" | "proceed"


@dataclass
class ConfirmationResult:
    """确认结果"""
    confirmed: bool
    timed_out: bool = False
    user_message: Optional[str] = None


class HighRiskConfirmation:
    """高风险操作确认管理器
    
    Attributes:
        _high_risk_operations: 高风险操作配置
        _confirmation_handler: 确认处理器（UI回调）
    """
    
    # 默认高风险操作
    DEFAULT_HIGH_RISK = {
        "file_delete": {
            "requires_confirmation": True,
            "message": "即将删除文件，确认继续？"
        },
        "file_move_batch": {
            "requires_confirmation": True,
            "threshold": 10,
            "message": "即将移动{count}个文件，确认继续？"
        },
        "send_message": {
            "requires_confirmation": True,
            "message": "即将发送消息，确认继续？"
        },
    }
    
    def __init__(
        self,
        config: Dict[str, Any],
        confirmation_handler: Callable[[ConfirmationRequest], Awaitable[ConfirmationResult]],
    ) -> None:
        """初始化确认管理器
        
        Args:
            config: 高风险操作配置
            confirmation_handler: 确认处理器（通常是UI弹窗）
        """
        ...
    
    def is_high_risk(
        self,
        tool_name: str,
        params: Dict[str, Any],
    ) -> bool:
        """判断是否为高风险操作
        
        Args:
            tool_name: 工具名称
            params: 参数
            
        Returns:
            是否高风险
        """
        ...
    
    async def request_confirmation(
        self,
        tool_name: str,
        params: Dict[str, Any],
    ) -> ConfirmationResult:
        """请求用户确认
        
        Args:
            tool_name: 工具名称
            params: 参数
            
        Returns:
            确认结果
        """
        ...
    
    def add_high_risk_operation(
        self,
        operation_name: str,
        config: Dict[str, Any],
    ) -> None:
        """添加高风险操作
        
        Args:
            operation_name: 操作名称
            config: 配置
        """
        ...


---

## 4. 内置工具实现

### 4.1 SystemReminderTool - 提醒工具

```python
"""系统提醒工具

设置系统级提醒/闹钟。

PRD映射: §0.10 system_reminder工具
"""

from typing import Dict, Any, Optional
from datetime import datetime
import asyncio


class SystemReminderTool(BaseTool):
    """系统提醒工具
    
    Attributes:
        _scheduler: 提醒调度器
        _active_reminders: 活跃提醒列表
    """
    
    @property
    def name(self) -> str:
        return "system_reminder"
    
    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="system_reminder",
            description="设置系统提醒，到时间后弹出通知",
            category=ToolCategory.SYSTEM,
            parameters={
                "title": ParameterSchema(
                    name="title",
                    type="string",
                    description="提醒标题",
                    required=True,
                ),
                "datetime": ParameterSchema(
                    name="datetime",
                    type="string",
                    description="提醒时间，支持ISO格式或相对时间（如'明天8点'）",
                    required=True,
                ),
                "message": ParameterSchema(
                    name="message",
                    type="string",
                    description="提醒内容",
                    required=False,
                ),
                "repeat": ParameterSchema(
                    name="repeat",
                    type="string",
                    description="重复模式",
                    required=False,
                    enum=["once", "daily", "weekly"],
                    default="once",
                ),
            },
            required_params=["title", "datetime"],
            cacheable=False,
            requires_confirmation=False,
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行提醒设置
        
        Args:
            params: 包含title, datetime, message, repeat的参数
            
        Returns:
            执行结果
        """
        ...
    
    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """解析日期时间字符串
        
        支持:
        - ISO格式: "2025-12-30T08:00:00"
        - 相对时间: "明天8点", "后天下午3点", "5分钟后"
        
        Args:
            datetime_str: 时间字符串
            
        Returns:
            解析后的datetime，失败返回None
        """
        ...
    
    async def _schedule_reminder(
        self,
        title: str,
        target_time: datetime,
        message: Optional[str],
        repeat: str,
    ) -> str:
        """调度提醒
        
        Returns:
            提醒ID
        """
        ...
    
    async def cancel_reminder(self, reminder_id: str) -> bool:
        """取消提醒
        
        Args:
            reminder_id: 提醒ID
            
        Returns:
            是否成功取消
        """
        ...


### 4.2 WeatherQueryTool - 天气工具

```python
"""天气查询工具

查询天气信息。

PRD映射: §0.10 weather_query工具
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class WeatherInfo:
    """天气信息"""
    city: str
    date: str
    temperature: float
    condition: str
    humidity: int
    wind_speed: float
    description: str


class WeatherQueryTool(BaseTool):
    """天气查询工具
    
    Attributes:
        _api_url: 天气API地址
        _default_city: 默认城市
    """
    
    @property
    def name(self) -> str:
        return "weather_query"
    
    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="weather_query",
            description="查询指定城市的天气信息",
            category=ToolCategory.QUERY,
            parameters={
                "city": ParameterSchema(
                    name="city",
                    type="string",
                    description="城市名，默认使用用户配置的城市",
                    required=False,
                ),
                "date": ParameterSchema(
                    name="date",
                    type="string",
                    description="查询日期",
                    required=False,
                    enum=["today", "tomorrow"],
                    default="today",
                ),
            },
            required_params=[],
            cacheable=True,
            cache_ttl_minutes=30,
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行天气查询
        
        Args:
            params: 包含city, date的参数
            
        Returns:
            包含天气信息的结果
        """
        ...
    
    async def _fetch_weather(
        self,
        city: str,
        date: str,
    ) -> Optional[WeatherInfo]:
        """获取天气数据
        
        使用wttr.in免费API。
        
        Args:
            city: 城市名
            date: 日期
            
        Returns:
            天气信息
        """
        ...


### 4.3 AppLauncherTool - 启动器工具

```python
"""应用启动器工具

启动已配置的应用程序。

PRD映射: §0.10 app_launcher工具, 第一部分§16
"""

from typing import Dict, Any, Optional, List
import subprocess
from pathlib import Path


class AppLauncherTool(BaseTool):
    """应用启动器工具
    
    Attributes:
        _apps_config: 应用配置（来自launcher.json）
    """
    
    @property
    def name(self) -> str:
        return "app_launcher"
    
    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="app_launcher",
            description="启动已配置的应用程序",
            category=ToolCategory.SYSTEM,
            parameters={
                "app_name": ParameterSchema(
                    name="app_name",
                    type="string",
                    description="应用名称，需在launcher.json中配置",
                    required=True,
                ),
            },
            required_params=["app_name"],
            cacheable=False,
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行应用启动
        
        Args:
            params: 包含app_name的参数
            
        Returns:
            执行结果
        """
        ...
    
    def get_available_apps(self) -> List[str]:
        """获取可用应用列表"""
        ...
    
    def _find_app_path(self, app_name: str) -> Optional[Path]:
        """查找应用路径
        
        Args:
            app_name: 应用名称
            
        Returns:
            应用路径
        """
        ...
    
    async def _launch_app(self, path: Path) -> bool:
        """启动应用
        
        Args:
            path: 应用路径
            
        Returns:
            是否成功启动
        """
        ...


### 4.4 NoteManagerTool - 便签工具

```python
"""便签管理工具

创建、读取、搜索便签。

PRD映射: §0.10 note_manager工具, 第一部分§24
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Note:
    """便签"""
    id: str
    content: str
    created_at: datetime
    tags: List[str]


class NoteManagerTool(BaseTool):
    """便签管理工具
    
    Attributes:
        _notes_path: 便签文件路径
    """
    
    @property
    def name(self) -> str:
        return "note_manager"
    
    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="note_manager",
            description="创建、读取或搜索便签",
            category=ToolCategory.STORAGE,
            parameters={
                "action": ParameterSchema(
                    name="action",
                    type="string",
                    description="操作类型",
                    required=True,
                    enum=["create", "read", "search", "list"],
                ),
                "content": ParameterSchema(
                    name="content",
                    type="string",
                    description="便签内容（create时必需）",
                    required=False,
                ),
                "query": ParameterSchema(
                    name="query",
                    type="string",
                    description="搜索关键词（search时必需）",
                    required=False,
                ),
                "note_id": ParameterSchema(
                    name="note_id",
                    type="string",
                    description="便签ID（read时可用）",
                    required=False,
                ),
            },
            required_params=["action"],
            cacheable=False,
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行便签操作
        
        Args:
            params: 操作参数
            
        Returns:
            执行结果
        """
        ...
    
    async def create_note(self, content: str, tags: List[str] = None) -> Note:
        """创建便签"""
        ...
    
    async def read_note(self, note_id: str) -> Optional[Note]:
        """读取便签"""
        ...
    
    async def search_notes(self, query: str) -> List[Note]:
        """搜索便签"""
        ...
    
    async def list_notes(self, limit: int = 10) -> List[Note]:
        """列出最近便签"""
        ...


---

## 5. 工具结果缓存

```python
"""工具结果缓存

对可缓存工具的结果进行缓存，减少重复调用。

PRD映射: §0.10 工具结果缓存
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json


@dataclass
class CacheEntry:
    """缓存条目"""
    result: "ToolResult"
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0


class ToolResultCache:
    """工具结果缓存
    
    Attributes:
        _cache: 缓存存储
        _max_entries: 最大条目数
        _default_ttl: 默认TTL
    """
    
    def __init__(
        self,
        max_entries: int = 100,
        default_ttl_minutes: int = 30,
    ) -> None:
        """初始化缓存
        
        Args:
            max_entries: 最大条目数
            default_ttl_minutes: 默认TTL分钟数
        """
        ...
    
    def get(
        self,
        tool_name: str,
        params: Dict[str, Any],
    ) -> Optional["ToolResult"]:
        """获取缓存
        
        Args:
            tool_name: 工具名称
            params: 参数
            
        Returns:
            缓存的结果，未命中返回None
        """
        ...
    
    def set(
        self,
        tool_name: str,
        params: Dict[str, Any],
        result: "ToolResult",
        ttl_minutes: Optional[int] = None,
    ) -> None:
        """设置缓存
        
        Args:
            tool_name: 工具名称
            params: 参数
            result: 执行结果
            ttl_minutes: TTL分钟数，None使用默认值
        """
        ...
    
    def invalidate(
        self,
        tool_name: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> int:
        """使缓存失效
        
        Args:
            tool_name: 工具名称
            params: 参数，None则使该工具所有缓存失效
            
        Returns:
            失效的条目数
        """
        ...
    
    def clear(self) -> None:
        """清空所有缓存"""
        ...
    
    def _make_cache_key(
        self,
        tool_name: str,
        params: Dict[str, Any],
    ) -> str:
        """生成缓存键
        
        Args:
            tool_name: 工具名称
            params: 参数
            
        Returns:
            缓存键（hash）
        """
        ...
    
    def _evict_expired(self) -> int:
        """清除过期条目
        
        Returns:
            清除的条目数
        """
        ...
    
    def _evict_lru(self) -> None:
        """LRU淘汰"""
        ...


---

## 6. 配置模型

### 6.1 工具配置 (tool_settings.json)

```python
"""工具配置Pydantic模型"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class RetryStrategyConfig(BaseModel):
    """重试策略配置"""
    enable: bool = True
    max_attempts: int = 3
    initial_delay_ms: int = 500
    backoff_multiplier: float = 2.0
    max_delay_ms: int = 5000
    retryable_errors: List[str] = [
        "network_timeout",
        "rate_limit",
        "server_error",
        "transient_failure",
    ]
    non_retryable_errors: List[str] = [
        "auth_error",
        "invalid_params",
        "permission_denied",
    ]


class ToolCacheConfig(BaseModel):
    """工具缓存配置"""
    enable: bool = True
    max_entries: int = 100
    eviction_policy: str = "LRU"
    tool_ttl_minutes: Dict[str, int] = {
        "weather_query": 30,
        "web_search": 10,
    }
    non_cacheable_tools: List[str] = [
        "system_reminder",
        "app_launcher",
        "note_manager",
    ]


class HighRiskConfig(BaseModel):
    """高风险操作配置"""
    enable_confirmation: bool = True
    operations: Dict[str, Dict[str, any]] = {}
    confirmation_timeout_seconds: int = 30
    default_on_timeout: str = "cancel"


class AttentionManagementConfig(BaseModel):
    """注意力管理配置"""
    enable_prefilter: bool = True
    max_tool_result_tokens: int = 500
    max_tool_calls_per_turn: int = 3
    enable_split_confirmation: bool = True
    log_tool_calls: bool = True
    warn_on_high_frequency: bool = True
    high_frequency_threshold_per_hour: int = 20


class ToolSettings(BaseModel):
    """工具系统完整配置"""
    enable_tools: bool = True
    react_mode: bool = True
    tool_timeout_seconds: int = 10
    retry_strategy: RetryStrategyConfig = Field(default_factory=RetryStrategyConfig)
    tool_cache: ToolCacheConfig = Field(default_factory=ToolCacheConfig)
    high_risk_operations: HighRiskConfig = Field(default_factory=HighRiskConfig)
    attention_management: AttentionManagementConfig = Field(default_factory=AttentionManagementConfig)
    available_tools: Dict[str, Dict[str, any]] = {}
    error_messages: Dict[str, str] = {}


---

## 7. 事件定义

```python
"""工具系统事件定义"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class ToolExecutionStartedEvent:
    """工具执行开始事件"""
    tool_name: str
    params: Dict[str, Any]
    trace_id: str


@dataclass
class ToolExecutionCompletedEvent:
    """工具执行完成事件"""
    tool_name: str
    success: bool
    execution_time_ms: int
    cached: bool
    trace_id: str


@dataclass
class ToolExecutionFailedEvent:
    """工具执行失败事件"""
    tool_name: str
    error: str
    error_type: str
    attempts: int
    trace_id: str


@dataclass
class ToolConfirmationRequestedEvent:
    """工具确认请求事件"""
    tool_name: str
    message: str
    timeout_seconds: int


@dataclass
class ToolConfirmationResultEvent:
    """工具确认结果事件"""
    tool_name: str
    confirmed: bool
    timed_out: bool


@dataclass
class ReActIterationEvent:
    """ReAct迭代事件"""
    iteration: int
    step: str  # "thought" | "action" | "observation"
    content: str


---

## 8. 依赖与接口

### 8.1 依赖模块

| 模块 | 用途 |
|------|------|
| Core | 事件总线、配置加载 |
| AI | LLM客户端（ReAct推理） |
| State | 状态回滚 |

### 8.2 对外接口

```python
# 模块导出
from rainze.tools import (
    # 注册表
    ToolRegistry,
    
    # 执行器
    ToolExecutor,
    ExecutionContext,
    
    # ReAct引擎
    ReActEngine,
    ReActResult,
    
    # 工具基类
    BaseTool,
    ToolSchema,
    ToolResult,
    ToolCategory,
    
    # 内置工具
    SystemReminderTool,
    WeatherQueryTool,
    AppLauncherTool,
    NoteManagerTool,
    
    # 缓存
    ToolResultCache,
    
    # 确认
    HighRiskConfirmation,
    ConfirmationRequest,
    ConfirmationResult,
    
    # 事件
    ToolExecutionStartedEvent,
    ToolExecutionCompletedEvent,
    ToolExecutionFailedEvent,
)
```

---

## 9. 使用示例

### 9.1 注册和执行工具

```python
# 初始化
registry = ToolRegistry()
registry.register_builtin_tools()

cache = ToolResultCache(max_entries=100)
executor = ToolExecutor(registry, cache, RetryConfig())

# 执行工具
result = await executor.execute(
    tool_name="weather_query",
    params={"city": "北京", "date": "today"},
)

if result.success:
    print(f"天气: {result.data}")
else:
    print(f"查询失败: {result.error}")
```

### 9.2 使用ReAct引擎

```python
# 初始化ReAct引擎
react_engine = ReActEngine(
    executor=executor,
    llm_client=llm_client,
    max_iterations=5,
)

# 处理用户请求
result = await react_engine.run(
    user_input="帮我查一下明天北京的天气，然后提醒我带伞",
    context={"user_city": "北京"},
)

print(result.final_response)
# 输出: "明天北京有雨，我已经帮你设置了提醒，记得带伞哦~"
```

---

**文档版本历史**:

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0.0 | 2025-12-30 | 初始版本 |
