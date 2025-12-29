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
└── types.py              # 通用类型定义
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
