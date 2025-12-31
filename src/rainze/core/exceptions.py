"""
自定义异常定义
Custom Exception Definitions

本模块定义 Rainze 应用的所有自定义异常类。
This module defines all custom exception classes for Rainze.

Reference:
    - MOD: .github/prds/modules/MOD-Core.md §6

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations


class RainzeError(Exception):
    """
    Rainze 基础异常类
    Base exception class for Rainze

    所有 Rainze 自定义异常都继承自此类。
    All Rainze custom exceptions inherit from this class.

    Attributes:
        code: 错误代码 / Error code
        message: 错误消息 / Error message
    """

    def __init__(self, message: str, code: str = "UNKNOWN") -> None:
        """
        初始化异常 / Initialize exception

        Args:
            message: 错误描述 / Error description
            code: 错误代码 / Error code
        """
        super().__init__(message)
        self.code = code
        self.message = message

    def __str__(self) -> str:
        """返回格式化的错误信息 / Return formatted error message"""
        return f"[{self.code}] {self.message}"


class ConfigError(RainzeError):
    """
    配置相关错误
    Configuration related error

    当配置文件无法加载、解析或验证失败时抛出。
    Raised when config file cannot be loaded, parsed, or validation fails.
    """

    def __init__(self, message: str, filename: str | None = None) -> None:
        """
        初始化配置错误 / Initialize config error

        Args:
            message: 错误描述 / Error description
            filename: 配置文件名 / Config filename
        """
        code = "CONFIG_ERROR"
        if filename:
            message = f"{filename}: {message}"
        super().__init__(message, code)
        self.filename = filename


class StartupError(RainzeError):
    """
    启动失败错误
    Startup failure error

    当应用启动过程中发生不可恢复错误时抛出。
    Raised when an unrecoverable error occurs during startup.
    """

    def __init__(self, message: str, component: str | None = None) -> None:
        """
        初始化启动错误 / Initialize startup error

        Args:
            message: 错误描述 / Error description
            component: 失败的组件名 / Failed component name
        """
        code = "STARTUP_ERROR"
        if component:
            message = f"[{component}] {message}"
        super().__init__(message, code)
        self.component = component


class ShutdownError(RainzeError):
    """
    关闭时错误
    Shutdown error

    当应用关闭过程中发生错误时抛出。
    Raised when an error occurs during shutdown.
    """

    def __init__(self, message: str) -> None:
        """
        初始化关闭错误 / Initialize shutdown error

        Args:
            message: 错误描述 / Error description
        """
        super().__init__(message, "SHUTDOWN_ERROR")


class ServiceNotFoundError(RainzeError):
    """
    服务未注册错误
    Service not found error

    当尝试从依赖注入容器获取未注册的服务时抛出。
    Raised when trying to resolve an unregistered service from DI container.
    """

    def __init__(self, service_type: type) -> None:
        """
        初始化服务未找到错误 / Initialize service not found error

        Args:
            service_type: 请求的服务类型 / Requested service type
        """
        message = f"Service not registered: {service_type.__name__}"
        super().__init__(message, "SERVICE_NOT_FOUND")
        self.service_type = service_type


class EventError(RainzeError):
    """
    事件处理错误
    Event handling error

    当事件发布或处理过程中发生错误时抛出。
    Raised when an error occurs during event publishing or handling.
    """

    def __init__(self, message: str, event_type: str | None = None) -> None:
        """
        初始化事件错误 / Initialize event error

        Args:
            message: 错误描述 / Error description
            event_type: 事件类型名 / Event type name
        """
        code = "EVENT_ERROR"
        if event_type:
            message = f"[{event_type}] {message}"
        super().__init__(message, code)
        self.event_type = event_type
