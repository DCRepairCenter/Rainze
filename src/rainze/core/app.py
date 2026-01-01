"""
应用主类
Application Main Class

本模块提供 Rainze 应用的主入口和生命周期管理。
This module provides main entry and lifecycle management for Rainze.

Reference:
    - MOD: .github/prds/modules/MOD-Core.md §3.1

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import asyncio
import signal
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable, List, Optional

from .config import ConfigManager
from .event_bus import Event, EventBus
from .exceptions import StartupError

__all__ = ["Application", "AppStartupEvent", "AppShutdownEvent"]


@dataclass
class AppStartupEvent(Event):
    """
    应用启动完成事件
    Application startup complete event
    """

    config_loaded: bool = True


@dataclass
class AppShutdownEvent(Event):
    """
    应用即将关闭事件
    Application about to shutdown event
    """

    exit_code: int = 0
    reason: Optional[str] = None


@dataclass
class _ShutdownHook:
    """
    关闭钩子（内部使用）
    Shutdown hook (internal use)
    """

    hook: Callable[[], Awaitable[None]]
    priority: int


class Application:
    """
    Rainze 应用主类
    Rainze Application Main Class

    管理整个应用的生命周期，使用单例模式。
    Manages entire application lifecycle, uses singleton pattern.

    Attributes:
        config: 配置管理器实例 / Config manager instance
        event_bus: 事件总线实例 / Event bus instance
        is_running: 应用是否正在运行 / Whether app is running

    Example:
        >>> app = Application(config_dir=Path("./config"))
        >>> app.event_bus.subscribe(AppStartupEvent, on_startup)
        >>> app.run()
    """

    _instance: Optional["Application"] = None

    def __init__(self, config_dir: Path) -> None:
        """
        初始化应用实例
        Initialize application instance

        Args:
            config_dir: 配置文件目录路径 / Config directory path

        Raises:
            RuntimeError: 如果已存在实例 / If instance already exists
        """
        if Application._instance is not None:
            raise RuntimeError(
                "Application instance already exists. Use Application.instance()"
            )

        self._config_dir = config_dir
        self.config: ConfigManager = ConfigManager(config_dir)
        self.event_bus: EventBus = EventBus()
        self.is_running: bool = False
        self._shutdown_hooks: List[_ShutdownHook] = []
        self._exit_code: int = 0

        Application._instance = self

    @classmethod
    def instance(cls) -> "Application":
        """
        获取全局唯一实例
        Get global singleton instance

        Returns:
            应用实例 / Application instance

        Raises:
            RuntimeError: 如果实例未创建 / If instance not created
        """
        if cls._instance is None:
            raise RuntimeError(
                "Application not initialized. Create instance first."
            )
        return cls._instance

    @classmethod
    def has_instance(cls) -> bool:
        """
        检查是否已创建实例
        Check if instance has been created
        """
        return cls._instance is not None

    async def startup(self) -> None:
        """
        应用启动流程
        Application startup flow

        执行顺序 / Execution order:
        1. 加载配置 / Load config
        2. 初始化日志 / Initialize logging
        3. 注册核心服务 / Register core services
        4. 发布 AppStartupEvent / Publish AppStartupEvent
        5. 启动事件循环处理 / Start event loop processing
        """
        try:
            # 1. 验证配置目录 / Validate config directory
            if not self._config_dir.exists():
                raise StartupError(
                    f"Config directory not found: {self._config_dir}",
                    component="config",
                )

            # 2. 启动事件队列处理 / Start event queue processing
            await self.event_bus.start_queue_processor()

            # 3. 标记为运行中 / Mark as running
            self.is_running = True

            # 4. 发布启动事件 / Publish startup event
            await self.event_bus.publish(
                AppStartupEvent(
                    source="core.app",
                    config_loaded=True,
                )
            )

        except Exception as e:
            self.is_running = False
            raise StartupError(str(e), component="startup") from e

    async def shutdown(self, exit_code: int = 0, reason: str | None = None) -> None:
        """
        应用关闭流程
        Application shutdown flow

        执行顺序 / Execution order:
        1. 发布 AppShutdownEvent / Publish AppShutdownEvent
        2. 执行关闭钩子 / Execute shutdown hooks
        3. 停止事件队列 / Stop event queue
        4. 保存状态 / Save state
        5. 释放资源 / Release resources

        Args:
            exit_code: 退出码 / Exit code
            reason: 关闭原因 / Shutdown reason
        """
        if not self.is_running:
            return

        self._exit_code = exit_code

        # 1. 发布关闭事件 / Publish shutdown event
        await self.event_bus.publish(
            AppShutdownEvent(
                source="core.app",
                exit_code=exit_code,
                reason=reason,
            )
        )

        # 2. 执行关闭钩子（按优先级）/ Execute shutdown hooks (by priority)
        sorted_hooks = sorted(self._shutdown_hooks, key=lambda h: h.priority)
        for hook_entry in sorted_hooks:
            try:
                await hook_entry.hook()
            except Exception:
                pass  # 忽略钩子错误 / Ignore hook errors

        # 3. 停止事件队列 / Stop event queue
        await self.event_bus.stop_queue_processor()

        # 4. 标记为已停止 / Mark as stopped
        self.is_running = False

    def register_shutdown_hook(
        self,
        hook: Callable[[], Awaitable[None]],
        priority: int = 0,
    ) -> None:
        """
        注册关闭钩子
        Register shutdown hook

        Args:
            hook: 异步钩子函数 / Async hook function
            priority: 优先级，数值越小越先执行 / Priority, lower = earlier
        """
        self._shutdown_hooks.append(_ShutdownHook(hook=hook, priority=priority))

    def run(self) -> int:
        """
        阻塞式运行应用（入口方法）
        Run application blocking (entry method)

        Returns:
            退出码 / Exit code
        """
        # 设置信号处理 / Setup signal handlers
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # 处理 SIGINT (Ctrl+C) / Handle SIGINT
        if sys.platform != "win32":
            for sig in (signal.SIGTERM, signal.SIGINT):
                # 创建信号处理器 / Create signal handler
                def make_handler(s: signal.Signals) -> Callable[[], None]:
                    def handler() -> None:
                        asyncio.create_task(self._handle_signal(s))
                    return handler

                loop.add_signal_handler(sig, make_handler(sig))

        try:
            loop.run_until_complete(self._run_async())
        except KeyboardInterrupt:
            loop.run_until_complete(self.shutdown(0, "KeyboardInterrupt"))
        finally:
            loop.close()

        return self._exit_code

    async def _run_async(self) -> None:
        """
        异步运行主循环
        Run async main loop
        """
        await self.startup()

        # 保持运行直到关闭 / Keep running until shutdown
        while self.is_running:
            await asyncio.sleep(0.1)

    async def _handle_signal(self, sig: signal.Signals) -> None:
        """
        处理系统信号
        Handle system signal
        """
        await self.shutdown(0, f"Signal: {sig.name}")

    @classmethod
    def reset_instance(cls) -> None:
        """
        重置单例实例（仅用于测试）
        Reset singleton instance (for testing only)
        """
        cls._instance = None
