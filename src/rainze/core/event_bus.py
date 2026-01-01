"""
事件总线
Event Bus

本模块提供异步事件总线实现，用于模块间解耦通信。
This module provides async event bus for decoupled inter-module communication.

Features / 功能:
- 异步/同步事件发布 / Async/sync event publishing
- 事件优先级 / Event priority
- 事件过滤 / Event filtering
- 通配符订阅 / Wildcard subscription

Reference:
    - MOD: .github/prds/modules/MOD-Core.md §3.3

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    TypeVar,
)

if TYPE_CHECKING:
    pass

# 导出列表 / Export list
__all__ = ["Event", "EventBus"]


@dataclass
class Event:
    """
    事件基类
    Base event class

    所有自定义事件都应继承此类。
    All custom events should inherit from this class.

    Attributes:
        timestamp: 事件发生时间 / Event timestamp
        source: 事件来源模块 / Event source module
    """

    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""


# 事件类型变量 / Event type variable
E = TypeVar("E", bound=Event)

# 事件处理器类型 / Event handler type
EventHandler = Callable[[E], Awaitable[None]]
EventFilter = Callable[[E], bool]


@dataclass
class _HandlerEntry:
    """
    处理器注册条目（内部使用）
    Handler registration entry (internal use)
    """

    handler: EventHandler[Any]
    priority: int
    filter_func: EventFilter[Any] | None


class EventBus:
    """
    异步事件总线
    Async Event Bus

    实现模块间解耦通信，支持异步事件处理。
    Enables decoupled inter-module communication with async event handling.

    Attributes:
        _handlers: 事件处理器注册表 / Event handler registry
        _queue: 异步事件队列 / Async event queue

    Example:
        >>> bus = EventBus()
        >>> async def on_startup(event: AppStartupEvent) -> None:
        ...     print(f"App started at {event.timestamp}")
        >>> bus.subscribe(AppStartupEvent, on_startup)
        >>> await bus.publish(AppStartupEvent(source="core"))
    """

    def __init__(self, queue_size: int = 1000) -> None:
        """
        初始化事件总线
        Initialize event bus

        Args:
            queue_size: 事件队列大小 / Event queue size
        """
        # 处理器注册表: 事件类型 -> 处理器列表
        # Handler registry: event type -> handler list
        self._handlers: dict[type[Event], list[_HandlerEntry]] = {}

        # 异步事件队列 / Async event queue
        self._queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=queue_size)

        # 队列处理任务 / Queue processing task
        self._queue_task: asyncio.Task[None] | None = None

        # 是否正在运行 / Is running
        self._running: bool = False

    def subscribe(
        self,
        event_type: type[E],
        handler: EventHandler[E],
        priority: int = 0,
        filter_func: EventFilter[E] | None = None,
    ) -> Callable[[], None]:
        """
        订阅事件
        Subscribe to event

        Args:
            event_type: 事件类型 / Event type
            handler: 异步处理函数 / Async handler function
            priority: 优先级，数值越小越先执行 / Priority, lower = earlier
            filter_func: 事件过滤器 / Event filter

        Returns:
            取消订阅的函数 / Unsubscribe function

        Example:
            >>> unsubscribe = bus.subscribe(MyEvent, my_handler, priority=10)
            >>> # 稍后取消订阅 / Later unsubscribe
            >>> unsubscribe()
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        entry = _HandlerEntry(
            handler=handler,
            priority=priority,
            filter_func=filter_func,
        )
        self._handlers[event_type].append(entry)

        # 按优先级排序（数值越小越先执行）
        # Sort by priority (lower = earlier)
        self._handlers[event_type].sort(key=lambda e: e.priority)

        # 返回取消订阅函数 / Return unsubscribe function
        def unsubscribe() -> None:
            if event_type in self._handlers:
                self._handlers[event_type] = [
                    e for e in self._handlers[event_type] if e.handler != handler
                ]

        return unsubscribe

    async def publish(self, event: Event) -> None:
        """
        发布事件（异步）
        Publish event (async)

        立即调用所有匹配的处理器。
        Immediately invokes all matching handlers.

        Args:
            event: 事件实例 / Event instance
        """
        event_type = type(event)

        # 获取此事件类型的所有处理器
        # Get all handlers for this event type
        handlers = self._handlers.get(event_type, [])

        for entry in handlers:
            # 应用过滤器 / Apply filter
            if entry.filter_func is not None and not entry.filter_func(event):
                continue

            # 调用处理器 / Invoke handler
            try:
                await entry.handler(event)
            except Exception as e:
                # 记录错误但不中断其他处理器
                # Log error but don't interrupt other handlers
                import structlog

                logger = structlog.get_logger("event_bus")
                logger.error(
                    "Handler error",
                    event_type=event_type.__name__,
                    error=str(e),
                )

    def publish_sync(self, event: Event) -> None:
        """
        发布事件（同步，加入队列）
        Publish event (sync, enqueue)

        将事件加入队列，由后台任务处理。
        Enqueues event for background processing.

        Args:
            event: 事件实例 / Event instance
        """
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            import structlog

            logger = structlog.get_logger("event_bus")
            logger.warning(
                "Event queue full, dropping event",
                event_type=type(event).__name__,
            )

    async def wait_for(
        self,
        event_type: type[E],
        timeout: float | None = None,
        filter_func: EventFilter[E] | None = None,
    ) -> E:
        """
        等待特定事件发生
        Wait for specific event

        Args:
            event_type: 事件类型 / Event type
            timeout: 超时时间（秒）/ Timeout in seconds
            filter_func: 事件过滤器 / Event filter

        Returns:
            匹配的事件实例 / Matching event instance

        Raises:
            asyncio.TimeoutError: 超时 / Timeout
        """
        result_event: E | None = None
        event_received = asyncio.Event()

        async def waiter(event: E) -> None:
            nonlocal result_event
            result_event = event
            event_received.set()

        # 订阅事件 / Subscribe to event
        unsubscribe = self.subscribe(
            event_type,
            waiter,
            priority=-1000,  # 高优先级确保先执行 / High priority
            filter_func=filter_func,
        )

        try:
            # 等待事件 / Wait for event
            await asyncio.wait_for(event_received.wait(), timeout=timeout)
            assert result_event is not None
            return result_event
        finally:
            # 取消订阅 / Unsubscribe
            unsubscribe()

    async def start_queue_processor(self) -> None:
        """
        启动队列处理器
        Start queue processor

        开始处理通过 publish_sync 加入队列的事件。
        Starts processing events enqueued via publish_sync.
        """
        if self._running:
            return

        self._running = True
        self._queue_task = asyncio.create_task(self._process_queue())

    async def stop_queue_processor(self) -> None:
        """
        停止队列处理器
        Stop queue processor

        停止处理队列中的事件。
        Stops processing queued events.
        """
        self._running = False
        if self._queue_task:
            self._queue_task.cancel()
            try:
                await self._queue_task
            except asyncio.CancelledError:
                pass
            self._queue_task = None

    async def _process_queue(self) -> None:
        """
        队列处理循环（内部使用）
        Queue processing loop (internal use)
        """
        while self._running:
            try:
                # 从队列获取事件 / Get event from queue
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self.publish(event)
            except asyncio.TimeoutError:
                # 超时继续循环 / Timeout, continue loop
                continue
            except asyncio.CancelledError:
                break

    def clear(self) -> None:
        """
        清除所有订阅
        Clear all subscriptions
        """
        self._handlers.clear()

    def handler_count(self, event_type: type[Event] | None = None) -> int:
        """
        获取处理器数量
        Get handler count

        Args:
            event_type: 事件类型，None 表示所有 / Event type, None for all

        Returns:
            处理器数量 / Handler count
        """
        if event_type is None:
            return sum(len(handlers) for handlers in self._handlers.values())
        return len(self._handlers.get(event_type, []))
