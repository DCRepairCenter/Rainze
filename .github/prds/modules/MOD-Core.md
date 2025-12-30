# MOD-Core: 核心基础设施模块

> **模块ID**: `rainze.core`
> **版本**: v1.0.0
> **优先级**: P0 (最高)
> **依赖**: 无
> **关联PRD**: [PRD-Rainze.md](../PRD-Rainze.md) 0.12-0.13节

---

## 1. 模块概述

### 1.1 职责定义

Core模块是Rainze应用的基础设施层，提供：

- **事件总线**: 模块间解耦通信
- **配置管理**: JSON配置加载、验证、热重载
- **应用生命周期**: 启动、关闭、异常处理
- **日志系统**: 结构化日志记录
- **依赖注入容器**: 服务注册与获取

### 1.2 设计原则

- **零业务逻辑**: 仅提供基础设施能力
- **单例模式**: 全局唯一实例
- **异步优先**: 基于asyncio的事件循环
- **类型安全**: 完整的类型注解

---

## 2. 目录结构

```
src/rainze/core/
├── __init__.py           # 模块导出
├── app.py                # 应用入口与生命周期
├── config.py             # 配置管理器
├── event_bus.py          # 事件总线
├── di_container.py       # 依赖注入容器
├── logger.py             # 日志系统
├── exceptions.py         # 自定义异常
├── types.py              # 通用类型定义
├── contracts/            # 跨模块契约 ⭐新增
│   ├── __init__.py
│   ├── emotion.py        # 情感标签契约
│   ├── scene.py          # 场景分类契约
│   ├── interaction.py    # 交互请求/响应契约
│   ├── observability.py  # 可观测性契约
│   └── rust_bridge.py    # Rust边界接口契约
└── observability/        # 可观测性实现 ⭐新增
    ├── __init__.py
    ├── tracer.py         # 统一追踪器
    └── metrics.py        # 性能指标收集
```

---

## 3. 类设计

### 3.1 Application (应用主类)

```python
# src/rainze/core/app.py

from typing import Optional, Callable, Awaitable
from pathlib import Path
import asyncio

class Application:
    """
    Rainze应用主类，管理整个应用的生命周期。
    
    使用单例模式，通过 Application.instance() 获取全局实例。
    
    Attributes:
        config: 配置管理器实例
        event_bus: 事件总线实例
        container: 依赖注入容器
        is_running: 应用是否正在运行
    """
    
    _instance: Optional["Application"] = None
    
    def __init__(self, config_dir: Path) -> None:
        """
        初始化应用实例。
        
        Args:
            config_dir: 配置文件目录路径
            
        Raises:
            RuntimeError: 如果已存在实例
        """
        ...
    
    @classmethod
    def instance(cls) -> "Application":
        """获取全局唯一实例。"""
        ...
    
    async def startup(self) -> None:
        """
        应用启动流程。
        
        执行顺序:
        1. 加载配置
        2. 初始化日志
        3. 注册核心服务
        4. 发布 AppStartupEvent
        5. 启动事件循环
        """
        ...
    
    async def shutdown(self, exit_code: int = 0) -> None:
        """
        应用关闭流程。
        
        执行顺序:
        1. 发布 AppShutdownEvent
        2. 等待所有任务完成
        3. 保存状态
        4. 释放资源
        
        Args:
            exit_code: 退出码
        """
        ...
    
    def register_shutdown_hook(
        self, 
        hook: Callable[[], Awaitable[None]],
        priority: int = 0
    ) -> None:
        """
        注册关闭钩子。
        
        Args:
            hook: 异步钩子函数
            priority: 优先级，数值越小越先执行
        """
        ...
    
    def run(self) -> None:
        """阻塞式运行应用（入口方法）。"""
        ...
```

### 3.2 ConfigManager (配置管理器)

```python
# src/rainze/core/config.py

from typing import TypeVar, Type, Optional, Any, Dict
from pathlib import Path
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class ConfigManager:
    """
    配置管理器，负责加载、验证、缓存配置文件。
    
    支持:
    - JSON配置文件加载
    - Pydantic模型验证
    - 配置热重载
    - 环境变量覆盖
    
    Attributes:
        config_dir: 配置文件目录
        _cache: 已加载的配置缓存
        _watchers: 文件监视器
    """
    
    def __init__(self, config_dir: Path) -> None:
        """
        初始化配置管理器。
        
        Args:
            config_dir: 配置文件根目录
        """
        ...
    
    def load(
        self, 
        filename: str, 
        model: Type[T],
        use_cache: bool = True
    ) -> T:
        """
        加载并验证配置文件。
        
        Args:
            filename: 配置文件名 (如 "api_settings.json")
            model: Pydantic模型类
            use_cache: 是否使用缓存
            
        Returns:
            验证后的配置对象
            
        Raises:
            FileNotFoundError: 文件不存在
            ValidationError: 配置验证失败
        """
        ...
    
    def reload(self, filename: str) -> None:
        """
        强制重新加载配置文件。
        
        Args:
            filename: 配置文件名
        """
        ...
    
    def watch(
        self, 
        filename: str, 
        callback: Callable[[str], None]
    ) -> None:
        """
        监视配置文件变化。
        
        Args:
            filename: 配置文件名
            callback: 变化时的回调函数
        """
        ...
    
    def get_raw(self, filename: str) -> Dict[str, Any]:
        """
        获取原始JSON数据（不经过Pydantic验证）。
        
        Args:
            filename: 配置文件名
            
        Returns:
            原始字典数据
        """
        ...
    
    def save(self, filename: str, data: BaseModel) -> None:
        """
        保存配置到文件。
        
        Args:
            filename: 配置文件名
            data: Pydantic模型实例
        """
        ...
```

### 3.3 EventBus (事件总线)

```python
# src/rainze/core/event_bus.py

from typing import TypeVar, Type, Callable, Awaitable, List, Dict
from dataclasses import dataclass
from datetime import datetime
import asyncio

@dataclass
class Event:
    """
    事件基类。
    
    Attributes:
        timestamp: 事件发生时间
        source: 事件来源模块
    """
    timestamp: datetime
    source: str

E = TypeVar("E", bound=Event)

class EventBus:
    """
    异步事件总线，实现模块间解耦通信。
    
    支持:
    - 同步/异步事件处理
    - 事件优先级
    - 事件过滤
    - 通配符订阅
    
    Attributes:
        _handlers: 事件处理器注册表
        _queue: 异步事件队列
    """
    
    def __init__(self) -> None:
        """初始化事件总线。"""
        ...
    
    def subscribe(
        self,
        event_type: Type[E],
        handler: Callable[[E], Awaitable[None]],
        priority: int = 0,
        filter_func: Optional[Callable[[E], bool]] = None
    ) -> Callable[[], None]:
        """
        订阅事件。
        
        Args:
            event_type: 事件类型
            handler: 异步处理函数
            priority: 优先级，数值越小越先执行
            filter_func: 事件过滤器
            
        Returns:
            取消订阅的函数
        """
        ...
    
    async def publish(self, event: Event) -> None:
        """
        发布事件（异步）。
        
        Args:
            event: 事件实例
        """
        ...
    
    def publish_sync(self, event: Event) -> None:
        """
        发布事件（同步，加入队列）。
        
        Args:
            event: 事件实例
        """
        ...
    
    async def wait_for(
        self,
        event_type: Type[E],
        timeout: Optional[float] = None,
        filter_func: Optional[Callable[[E], bool]] = None
    ) -> E:
        """
        等待特定事件发生。
        
        Args:
            event_type: 事件类型
            timeout: 超时时间（秒）
            filter_func: 事件过滤器
            
        Returns:
            匹配的事件实例
            
        Raises:
            asyncio.TimeoutError: 超时
        """
        ...
    
    def clear(self) -> None:
        """清除所有订阅。"""
        ...
```

### 3.4 DIContainer (依赖注入容器)

```python
# src/rainze/core/di_container.py

from typing import TypeVar, Type, Optional, Callable, Any, Dict

T = TypeVar("T")

class DIContainer:
    """
    简单的依赖注入容器。
    
    支持:
    - 单例注册
    - 工厂函数注册
    - 懒加载
    
    Attributes:
        _singletons: 单例实例缓存
        _factories: 工厂函数注册表
    """
    
    def __init__(self) -> None:
        """初始化容器。"""
        ...
    
    def register_singleton(
        self, 
        interface: Type[T], 
        instance: T
    ) -> None:
        """
        注册单例实例。
        
        Args:
            interface: 接口/类型
            instance: 实例
        """
        ...
    
    def register_factory(
        self,
        interface: Type[T],
        factory: Callable[[], T],
        singleton: bool = True
    ) -> None:
        """
        注册工厂函数。
        
        Args:
            interface: 接口/类型
            factory: 工厂函数
            singleton: 是否缓存为单例
        """
        ...
    
    def resolve(self, interface: Type[T]) -> T:
        """
        解析依赖。
        
        Args:
            interface: 接口/类型
            
        Returns:
            实例
            
        Raises:
            KeyError: 未注册的类型
        """
        ...
    
    def try_resolve(self, interface: Type[T]) -> Optional[T]:
        """
        尝试解析依赖（不抛异常）。
        
        Args:
            interface: 接口/类型
            
        Returns:
            实例或None
        """
        ...
```

### 3.5 Logger (日志系统)

```python
# src/rainze/core/logger.py

from typing import Optional, Any, Dict
from pathlib import Path
import structlog

class LoggerFactory:
    """
    日志工厂，创建结构化日志记录器。
    
    基于structlog，支持:
    - JSON格式输出
    - 上下文绑定
    - 多处理器（控制台、文件）
    """
    
    @classmethod
    def configure(
        cls,
        log_dir: Path,
        level: str = "INFO",
        json_format: bool = True
    ) -> None:
        """
        全局配置日志系统。
        
        Args:
            log_dir: 日志文件目录
            level: 日志级别
            json_format: 是否使用JSON格式
        """
        ...
    
    @classmethod
    def get_logger(
        cls, 
        name: str,
        **context: Any
    ) -> structlog.BoundLogger:
        """
        获取绑定上下文的日志记录器。
        
        Args:
            name: 日志器名称（通常是模块名）
            **context: 绑定的上下文字段
            
        Returns:
            绑定日志器
        """
        ...
```

---

## 4. 核心事件定义

```python
# src/rainze/core/events.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from .event_bus import Event

@dataclass
class AppStartupEvent(Event):
    """应用启动完成事件。"""
    config_loaded: bool = True

@dataclass
class AppShutdownEvent(Event):
    """应用即将关闭事件。"""
    exit_code: int = 0
    reason: Optional[str] = None

@dataclass
class ConfigChangedEvent(Event):
    """配置文件变化事件。"""
    filename: str = ""
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None

@dataclass
class ErrorEvent(Event):
    """全局错误事件。"""
    error: Exception = field(default_factory=Exception)
    module: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    recoverable: bool = True
```

---

## 5. 配置Schema

### 5.1 AppConfig

```python
# src/rainze/core/schemas.py

from pydantic import BaseModel, Field
from pathlib import Path
from typing import Optional

class LoggingConfig(BaseModel):
    """日志配置。"""
    level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR)$")
    log_dir: Path = Field(default=Path("./data/logs"))
    json_format: bool = True
    max_file_size_mb: int = Field(default=10, ge=1, le=100)
    retention_days: int = Field(default=7, ge=1, le=90)

class PerformanceConfig(BaseModel):
    """性能配置。"""
    event_queue_size: int = Field(default=1000, ge=100)
    config_cache_ttl_seconds: int = Field(default=300, ge=60)
    startup_timeout_seconds: int = Field(default=30, ge=10)
    shutdown_timeout_seconds: int = Field(default=10, ge=5)

class AppConfig(BaseModel):
    """应用全局配置 (app_settings.json)。"""
    app_name: str = "Rainze"
    version: str = "0.1.0"
    debug: bool = False
    data_dir: Path = Field(default=Path("./data"))
    config_dir: Path = Field(default=Path("./config"))
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
```

---

## 6. 异常定义

```python
# src/rainze/core/exceptions.py

class RainzeError(Exception):
    """Rainze基础异常类。"""
    
    def __init__(self, message: str, code: str = "UNKNOWN"):
        super().__init__(message)
        self.code = code
        self.message = message

class ConfigError(RainzeError):
    """配置相关错误。"""
    pass

class StartupError(RainzeError):
    """启动失败错误。"""
    pass

class ShutdownError(RainzeError):
    """关闭时错误。"""
    pass

class ServiceNotFoundError(RainzeError):
    """服务未注册错误。"""
    pass
```

---

## 7. 使用示例

```python
# main.py

import asyncio
from pathlib import Path
from rainze.core import Application, ConfigManager, EventBus
from rainze.core.events import AppStartupEvent
from rainze.core.schemas import AppConfig

async def on_startup(event: AppStartupEvent) -> None:
    print(f"Application started at {event.timestamp}")

def main():
    # 创建应用实例
    app = Application(config_dir=Path("./config"))
    
    # 订阅启动事件
    app.event_bus.subscribe(AppStartupEvent, on_startup)
    
    # 运行应用
    app.run()

if __name__ == "__main__":
    main()
```

---

## 8. 测试要点

| 测试类型 | 测试内容 |
|---------|---------|
| 单元测试 | ConfigManager加载/验证/热重载 |
| 单元测试 | EventBus订阅/发布/过滤 |
| 单元测试 | DIContainer注册/解析 |
| 集成测试 | Application启动/关闭流程 |
| 性能测试 | 事件发布吞吐量 (>10000/s) |

---

## 9. 依赖清单

```toml
# pyproject.toml 相关依赖
pydantic = ">=2.10"
pydantic-settings = ">=2.7"
structlog = ">=24.4"
watchdog = ">=6.0"  # 文件监视
anyio = ">=4.7"     # 异步支持
```

---

## 10. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.0 | 2025-12-29 | 初始版本 |
| v1.1.0 | 2025-12-30 | 新增跨模块契约 (contracts/) 和可观测性 (observability/) |

---

## 11. 跨模块契约类设计 (新增)

> **设计原则**: 所有模块必须从 `core.contracts` 导入公共类型，禁止重复定义

### 11.1 EmotionTag - 情感标签契约

```python
# src/rainze/core/contracts/emotion.py

from dataclasses import dataclass
from typing import Optional, Set, ClassVar
import re

@dataclass(frozen=True)
class EmotionTag:
    """统一情感标签数据结构
    
    所有模块（AI/State/Animation）必须使用此定义。
    
    Attributes:
        tag: 情感类型 (happy/sad/angry/shy/etc.)
        intensity: 强度 [0.0, 1.0]
    """
    
    # 类变量
    PATTERN: ClassVar[re.Pattern] = re.compile(r"\[EMOTION:(\w+):([\d.]+)\]")
    VALID_TAGS: ClassVar[Set[str]] = {
        "happy", "excited", "sad", "angry", "shy",
        "surprised", "tired", "anxious", "neutral"
    }
    
    tag: str
    intensity: float
    
    def __post_init__(self) -> None:
        """验证标签和强度"""
        ...
    
    def to_string(self) -> str:
        """序列化为标签格式 [EMOTION:tag:intensity]"""
        ...
    
    @classmethod
    def parse(cls, text: str) -> Optional["EmotionTag"]:
        """从文本解析情感标签
        
        Args:
            text: 包含情感标签的文本
            
        Returns:
            解析的EmotionTag，无标签返回None
        """
        ...
    
    @classmethod
    def strip_from_text(cls, text: str) -> str:
        """移除文本中的情感标签
        
        Args:
            text: 原始文本
            
        Returns:
            移除标签后的文本
        """
        ...
```

### 11.2 SceneType & ResponseTier - 场景分类契约

```python
# src/rainze/core/contracts/scene.py

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List

class SceneType(Enum):
    """场景类型枚举
    
    所有模块必须使用此定义，禁止重复定义。
    """
    SIMPLE = auto()   # 简单交互 -> Tier1
    MEDIUM = auto()   # 中等复杂度 -> Tier2
    COMPLEX = auto()  # 复杂场景 -> Tier3

class ResponseTier(Enum):
    """响应层级枚举"""
    TIER1_TEMPLATE = 1  # 模板响应
    TIER2_RULE = 2      # 规则生成
    TIER3_LLM = 3       # LLM生成

@dataclass
class SceneTierMapping:
    """场景-Tier映射配置"""
    scene_type: SceneType
    default_tier: ResponseTier
    allow_override: bool
    fallback_chain: List[ResponseTier]
    timeout_ms: int = 3000
    memory_retrieval: str = "none"  # "none" | "facts_summary" | "full"

def get_scene_tier_table() -> Dict[str, SceneTierMapping]:
    """获取场景-Tier中央映射表（从配置加载）
    
    Returns:
        场景ID到映射配置的字典
    """
    ...
```

### 11.3 InteractionRequest/Response - 交互契约

```python
# src/rainze/core/contracts/interaction.py

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime

class InteractionSource(Enum):
    """交互来源枚举
    
    所有用户交互必须标记来源。
    """
    CHAT_INPUT = auto()       # 用户聊天输入
    PASSIVE_TRIGGER = auto()  # 点击/拖拽
    SYSTEM_EVENT = auto()     # 系统事件
    TOOL_RESULT = auto()      # 工具执行结果
    PLUGIN_ACTION = auto()    # 插件行为
    GAME_INTERACTION = auto() # 游戏交互

@dataclass
class InteractionRequest:
    """统一交互请求格式
    
    所有交互必须封装为此格式，通过UCM处理。
    
    Attributes:
        request_id: 唯一请求ID
        source: 交互来源
        timestamp: 请求时间
        payload: 请求数据
        trace_id: 可观测性追踪ID
    """
    request_id: str
    source: InteractionSource
    timestamp: datetime
    payload: Dict[str, Any]
    trace_id: Optional[str] = None

@dataclass
class InteractionResponse:
    """统一交互响应格式
    
    Attributes:
        request_id: 对应请求ID
        success: 是否成功
        response_text: 响应文本
        emotion: 情感标签
        state_changes: 状态变更记录
        trace_spans: 追踪跨度列表
    """
    request_id: str
    success: bool
    response_text: Optional[str] = None
    emotion: Optional["EmotionTag"] = None
    state_changes: Dict[str, Any] = field(default_factory=dict)
    trace_spans: List[str] = field(default_factory=list)
```

### 11.4 IRustBridge - Rust边界接口契约

```python
# src/rainze/core/contracts/rust_bridge.py

from typing import Protocol, List, Tuple, Optional, runtime_checkable
import numpy as np

@runtime_checkable
class IRustMemorySearch(Protocol):
    """Rust记忆检索接口
    
    实现者: rainze_core.FAISSWrapper
    回退实现: rainze.memory.fallback.PythonMemorySearch
    """
    
    def search(
        self, 
        query_vector: np.ndarray, 
        top_k: int
    ) -> List[Tuple[str, float]]:
        """向量相似度搜索
        
        Args:
            query_vector: 查询向量 [dimension]
            top_k: 返回数量
            
        Returns:
            [(id, similarity_score), ...]
        """
        ...
    
    def rerank(
        self,
        candidates: List[Tuple[str, float]],
        weights: dict
    ) -> List[Tuple[str, float]]:
        """重排序
        
        Args:
            candidates: 候选结果
            weights: 重排序权重
            
        Returns:
            重排序后的结果
        """
        ...

@runtime_checkable
class IRustSystemMonitor(Protocol):
    """Rust系统监控接口
    
    实现者: rainze_core.SystemMonitor
    回退实现: rainze.features.system_monitor.PythonSystemMonitor
    """
    
    def get_cpu_usage(self) -> float:
        """获取CPU使用率 (0.0-100.0)"""
        ...
    
    def get_memory_usage(self) -> float:
        """获取内存使用率 (0.0-100.0)"""
        ...
    
    def is_fullscreen(self) -> bool:
        """检测是否有全屏应用"""
        ...
    
    def is_meeting_app(self) -> bool:
        """检测是否有会议应用"""
        ...

@runtime_checkable
class IRustTextProcess(Protocol):
    """Rust文本处理接口
    
    实现者: rainze_core.TextProcessor
    回退实现: jieba分词
    """
    
    def tokenize(self, text: str) -> List[str]:
        """中文分词"""
        ...
    
    def detect_entities(self, text: str) -> List[Tuple[str, str]]:
        """实体检测
        
        Returns:
            [(entity_text, entity_type), ...]
        """
        ...
```

### 11.5 Tracer - 可观测性契约

```python
# src/rainze/core/observability/tracer.py

from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Generator
from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass
class TraceSpan:
    """追踪跨度数据"""
    span_id: str
    trace_id: str
    parent_id: Optional[str]
    operation: str
    start_time: datetime
    end_time: Optional[datetime] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    def log(self, event: str, data: Optional[Dict] = None) -> None:
        """记录日志事件"""
        ...
    
    def set_tag(self, key: str, value: Any) -> None:
        """设置标签"""
        ...
    
    def duration_ms(self) -> Optional[int]:
        """获取耗时（毫秒）"""
        ...

class Tracer:
    """统一追踪器
    
    使用方式:
        with Tracer.span("memory.search", {"query": q}) as span:
            result = await search(q)
            span.log("found", {"count": len(result)})
    """
    
    _current_trace_id: Optional[str] = None
    _spans: List[TraceSpan] = []
    
    @classmethod
    def set_trace_id(cls, trace_id: str) -> None:
        """设置当前追踪ID"""
        ...
    
    @classmethod
    @contextmanager
    def span(
        cls, 
        operation: str, 
        tags: Optional[Dict] = None
    ) -> Generator[TraceSpan, None, None]:
        """创建追踪跨度的上下文管理器
        
        Args:
            operation: 操作名称 (如 "memory.search", "tool.execute.reminder")
            tags: 初始标签
            
        Yields:
            TraceSpan实例
        """
        ...
    
    @classmethod
    def get_current_spans(cls) -> List[TraceSpan]:
        """获取当前请求的所有跨度"""
        ...
    
    @classmethod
    def flush(cls) -> None:
        """刷新跨度到日志系统"""
        ...
```

---

## 12. 配置加载规范 (新增)

### 12.1 scene_tier_mapping.json Schema

> **文件路径**: `config/scene_tier_mapping.json`
> **加载位置**: `core.contracts.scene.get_scene_tier_table()` 或 `ai.scene_classifier.SceneClassifier.__init__()`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SceneTierMapping",
  "description": "场景类型与响应层级的映射配置",
  "type": "object",
  "additionalProperties": {
    "type": "object",
    "properties": {
      "scene_type": {
        "type": "string",
        "enum": ["SIMPLE", "MEDIUM", "COMPLEX"]
      },
      "default_tier": {
        "type": "string",
        "enum": ["TIER1_TEMPLATE", "TIER2_RULE", "TIER3_LLM"]
      },
      "timeout_ms": {
        "type": "integer",
        "minimum": 50,
        "maximum": 30000
      },
      "memory_retrieval": {
        "type": "string",
        "enum": ["none", "facts_summary", "full"]
      },
      "fallback_chain": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": ["TIER1_TEMPLATE", "TIER2_RULE", "TIER3_LLM"]
        }
      }
    },
    "required": ["scene_type", "default_tier"]
  }
}
```

**示例配置**:

```json
{
  "click": {
    "scene_type": "SIMPLE",
    "default_tier": "TIER1_TEMPLATE",
    "timeout_ms": 50,
    "memory_retrieval": "none",
    "fallback_chain": []
  },
  "hourly_chime": {
    "scene_type": "MEDIUM",
    "default_tier": "TIER2_RULE",
    "timeout_ms": 100,
    "memory_retrieval": "facts_summary",
    "fallback_chain": ["TIER1_TEMPLATE"]
  },
  "conversation": {
    "scene_type": "COMPLEX",
    "default_tier": "TIER3_LLM",
    "timeout_ms": 3000,
    "memory_retrieval": "full",
    "fallback_chain": ["TIER2_RULE", "TIER1_TEMPLATE"]
  },
  "system_warning": {
    "scene_type": "MEDIUM",
    "default_tier": "TIER2_RULE",
    "timeout_ms": 100,
    "memory_retrieval": "none",
    "fallback_chain": ["TIER1_TEMPLATE"]
  },
  "game_interaction": {
    "scene_type": "SIMPLE",
    "default_tier": "TIER1_TEMPLATE",
    "timeout_ms": 50,
    "memory_retrieval": "none",
    "fallback_chain": []
  },
  "tool_execution": {
    "scene_type": "MEDIUM",
    "default_tier": "TIER2_RULE",
    "timeout_ms": 500,
    "memory_retrieval": "facts_summary",
    "fallback_chain": ["TIER1_TEMPLATE"]
  },
  "emotion_analysis": {
    "scene_type": "COMPLEX",
    "default_tier": "TIER3_LLM",
    "timeout_ms": 2000,
    "memory_retrieval": "full",
    "fallback_chain": ["TIER2_RULE", "TIER1_TEMPLATE"]
  }
}
```

### 12.2 配置加载工具函数

```python
# src/rainze/core/contracts/scene.py (补充)

from pathlib import Path
from typing import Dict
import json

_scene_tier_cache: Optional[Dict[str, SceneTierMapping]] = None

def get_scene_tier_table(
    config_path: Optional[Path] = None
) -> Dict[str, SceneTierMapping]:
    """获取场景-Tier中央映射表
    
    Args:
        config_path: 配置文件路径，默认 config/scene_tier_mapping.json
        
    Returns:
        场景ID到映射配置的字典
        
    Raises:
        FileNotFoundError: 配置文件不存在
        ValidationError: 配置格式错误
    """
    global _scene_tier_cache
    if _scene_tier_cache is not None:
        return _scene_tier_cache
    
    if config_path is None:
        config_path = Path("./config/scene_tier_mapping.json")
    
    with open(config_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    _scene_tier_cache = {}
    for scene_id, mapping in raw_data.items():
        _scene_tier_cache[scene_id] = SceneTierMapping(
            scene_type=SceneType[mapping["scene_type"]],
            default_tier=ResponseTier[mapping["default_tier"]],
            timeout_ms=mapping.get("timeout_ms", 3000),
            memory_retrieval=mapping.get("memory_retrieval", "none"),
            fallback_chain=[
                ResponseTier[t] for t in mapping.get("fallback_chain", [])
            ],
            allow_override=mapping.get("allow_override", True)
        )
    
    return _scene_tier_cache

def invalidate_scene_tier_cache() -> None:
    """使缓存失效（配置热重载时调用）"""
    global _scene_tier_cache
    _scene_tier_cache = None
```

---

## 13. UnifiedContextManager (UCM) 接口契约 (新增)

> **说明**: UCM是所有用户交互的唯一入口，定义在 `agent.context_manager`，但接口契约在 `core.contracts` 中声明

### 13.1 IUnifiedContextManager Protocol

```python
# src/rainze/core/contracts/ucm.py

from typing import Protocol, runtime_checkable
from .interaction import InteractionRequest, InteractionResponse

@runtime_checkable
class IUnifiedContextManager(Protocol):
    """统一上下文管理器接口契约
    
    所有用户交互必须通过此接口处理，确保:
    - 状态一致性
    - 记忆完整性
    - 可观测性追踪
    
    实现者: rainze.agent.context_manager.UnifiedContextManager
    """
    
    async def process_interaction(
        self,
        request: InteractionRequest
    ) -> InteractionResponse:
        """处理交互的统一入口
        
        Args:
            request: 统一交互请求
            
        Returns:
            统一交互响应
        """
        ...
    
    async def get_context_summary(self) -> dict:
        """获取当前上下文摘要（用于调试）
        
        Returns:
            上下文状态字典
        """
        ...
```

### 13.2 UCM使用规范

**⛔ 禁止绕过UCM的调用模式**:

```python
# ❌ 错误：直接调用AI模块
response = await ai_service.generate_response(user_input)

# ❌ 错误：直接调用Memory模块
memories = await memory_manager.search(query)

# ❌ 错误：直接调用State模块更新状态
state_manager.update_emotion("happy", 0.8)
```

**✅ 正确：所有交互通过UCM**:

```python
# ✅ 正确：通过UCM处理交互
from rainze.core.contracts.interaction import InteractionRequest, InteractionSource

request = InteractionRequest(
    request_id=uuid4().hex,
    source=InteractionSource.CHAT_INPUT,
    timestamp=datetime.now(),
    payload={"text": user_input}
)
response = await ucm.process_interaction(request)
```

### 13.3 UCM内部处理流程

```
InteractionRequest
       │
       ▼
┌──────────────────────────────────────────────────┐
│               UnifiedContextManager               │
│                                                   │
│  1. [创建TraceSpan]                              │
│       │                                          │
│       ▼                                          │
│  2. [场景分类] ──────────────────────────────────┤
│       │         使用 scene_tier_mapping.json     │
│       ▼                                          │
│  3. [获取Tier和降级链]                           │
│       │                                          │
│       ▼                                          │
│  4. [按需检索记忆]                               │
│       │         memory_retrieval: none/facts/full│
│       ▼                                          │
│  5. [路由到处理器]                               │
│       │         Tier1/Tier2/Tier3               │
│       ▼                                          │
│  6. [更新状态和记忆]                             │
│       │                                          │
│       ▼                                          │
│  7. [记录TraceSpan并返回]                        │
└──────────────────────────────────────────────────┘
       │
       ▼
InteractionResponse
```

---

## 14. Observability 使用示例 (新增)

### 14.1 模块中使用Tracer

```python
# 示例：在Memory模块中使用Tracer

from rainze.core.observability import Tracer

class MemoryManager:
    async def search(self, query: str, top_k: int = 5) -> List[MemoryItem]:
        with Tracer.span("memory.search", {"query": query, "top_k": top_k}) as span:
            # 1. 选择检索策略
            strategy = self._select_strategy(query)
            span.log("strategy_selected", {"strategy": strategy.name})
            
            # 2. 执行检索
            with Tracer.span("memory.search.execute") as exec_span:
                if strategy == Strategy.FTS5:
                    results = await self._fts_search(query)
                else:
                    results = await self._vector_search(query)
                exec_span.set_tag("result_count", len(results))
            
            # 3. 重排序
            with Tracer.span("memory.search.rerank") as rerank_span:
                final_results = self._rerank(results, top_k)
                rerank_span.set_tag("final_count", len(final_results))
            
            span.set_tag("success", True)
            return final_results
```

### 14.2 异常处理与追踪

```python
# 示例：异常时记录追踪信息

from rainze.core.observability import Tracer

async def execute_tool(tool_name: str, params: dict) -> ToolResult:
    with Tracer.span("tool.execute", {"tool": tool_name}) as span:
        try:
            tool = self._registry.get(tool_name)
            result = await tool.run(params)
            span.set_tag("success", True)
            return result
        except ToolExecutionError as e:
            span.set_tag("success", False)
            span.set_tag("error", str(e))
            span.log("error", {"type": type(e).__name__, "message": str(e)})
            raise
```

### 14.3 跨模块追踪关联

```python
# UCM中创建根追踪，子模块自动关联

class UnifiedContextManager:
    async def process_interaction(self, request: InteractionRequest) -> InteractionResponse:
        # 设置请求级别的trace_id
        Tracer.set_trace_id(request.trace_id or uuid4().hex)
        
        with Tracer.span("ucm.process", {"source": request.source.name}) as root_span:
            # 子模块调用会自动关联到此trace
            scene = await self._classify_scene(request)  # 创建子span
            result = await self._generate_response(request, scene)  # 创建子span
            await self._update_state(result)  # 创建子span
            
            root_span.set_tag("scene_type", scene.scene_type.name)
            root_span.set_tag("response_tier", result.tier.name)
            
            # 收集所有span到响应
            return InteractionResponse(
                request_id=request.request_id,
                success=True,
                response_text=result.text,
                emotion=result.emotion,
                trace_spans=[s.span_id for s in Tracer.get_current_spans()]
            )
```
