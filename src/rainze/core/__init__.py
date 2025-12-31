"""
Core 模块 - 核心基础设施
Core Module - Core Infrastructure

本模块提供 Rainze 应用的基础设施能力，包括：
This module provides infrastructure capabilities for Rainze:

- 事件总线 / Event Bus
- 配置管理 / Configuration Management
- 应用生命周期 / Application Lifecycle
- 日志系统 / Logging System
- 依赖注入容器 / Dependency Injection Container

Design Principles / 设计原则:
- 零业务逻辑 / Zero business logic
- 单例模式 / Singleton pattern
- 异步优先 / Async-first
- 类型安全 / Type-safe

Reference:
    - MOD: .github/prds/modules/MOD-Core.md

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from .app import Application, AppShutdownEvent, AppStartupEvent
from .config import ConfigManager
from .event_bus import Event, EventBus
from .exceptions import (
    ConfigError,
    EventError,
    RainzeError,
    ServiceNotFoundError,
    ShutdownError,
    StartupError,
)
from .schemas import AppConfig, GUIConfig

__all__: list[str] = [
    "Application",
    "AppStartupEvent",
    "AppShutdownEvent",
    "ConfigManager",
    "EventBus",
    "Event",
    "RainzeError",
    "ConfigError",
    "StartupError",
    "ShutdownError",
    "ServiceNotFoundError",
    "EventError",
    "AppConfig",
    "GUIConfig",
]
