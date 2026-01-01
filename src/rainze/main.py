"""
Rainze 应用主入口
Rainze Application Main Entry

本模块提供应用的命令行入口点，初始化完整的依赖链。
This module provides the CLI entry point, initializing the full dependency chain.

依赖链架构 / Dependency Chain Architecture:
    InputPanel.message_submitted → UCM.process_interaction
    UCM 响应 → ChatBubble.show_text + AnimationController.set_expression
    StateManager 变更 → AnimationController 动画切换

Usage / 使用方式:
    $ rainze              # 启动应用 / Start application
    $ python -m rainze    # 模块方式启动 / Start as module

Reference:
    - TECH: .github/techstacks/TECH-Rainze.md §7.2
    - MOD: .github/prds/modules/MOD-Core.md
    - PRD §0.5a: 统一上下文管理器 (UCM)

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import asyncio
import sys
import threading
from pathlib import Path
from collections.abc import Coroutine
from typing import TYPE_CHECKING, Any, Callable, Optional

from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from rainze.animation import AnimationController
    from rainze.agent import UnifiedContextManager
    from rainze.core.contracts import InteractionResponse
    from rainze.gui import ChatBubble, InputPanel, MainWindow
    from rainze.state import StateManager


# ========================================
# 异步任务运行器 / Async Task Runner
# ========================================


def run_async_in_thread(
    coro: Coroutine[None, None, None],
    callback: Callable[[], None] | None = None,
    error_callback: Callable[[Exception], None] | None = None,
) -> None:
    """
    在单独线程中运行异步任务
    Run async coroutine in separate thread

    Args:
        coro: 协程对象 / Coroutine object
        callback: 成功回调 / Success callback
        error_callback: 错误回调 / Error callback
    """
    def _run() -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(coro)
            if callback:
                callback()
        except Exception as e:
            if error_callback:
                error_callback(e)
        finally:
            loop.close()

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()


# ========================================
# 应用协调器 / Application Coordinator
# ========================================


class RainzeCoordinator(QObject):
    """
    应用协调器 - 管理完整依赖链
    Application Coordinator - Manages full dependency chain

    职责 / Responsibilities:
    - 初始化所有核心组件 / Initialize all core components
    - 连接信号和槽 / Connect signals and slots
    - 处理 GUI ↔ UCM 之间的异步桥接 / Bridge async between GUI and UCM

    ⭐ 所有用户交互必须通过 UCM，此类确保该规则
    All user interactions MUST go through UCM, this class enforces that rule

    Signals:
        response_ready: 响应准备完成（在后台线程中发出）
        error_occurred: 发生错误

    Attributes:
        _ucm: 统一上下文管理器 / Unified Context Manager
        _state_manager: 状态管理器 / State Manager
        _animation_controller: 动画控制器 / Animation Controller
        _chat_bubble: 聊天气泡 / Chat Bubble
        _input_panel: 输入面板 / Input Panel
        _main_window: 主窗口 / Main Window
        _event_loop: asyncio 事件循环 / asyncio event loop
    """

    # 信号定义（用于线程间通信）/ Signals for cross-thread communication
    response_ready = Signal(object)  # InteractionResponse
    error_occurred = Signal(str)  # Error message

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """
        初始化协调器
        Initialize coordinator
        """
        super().__init__(parent)

        # 组件引用（延迟初始化）/ Component references (lazy init)
        self._ucm: Optional["UnifiedContextManager"] = None
        self._state_manager: Optional["StateManager"] = None
        self._animation_controller: Optional["AnimationController"] = None
        self._chat_bubble: Optional["ChatBubble"] = None
        self._input_panel: Optional["InputPanel"] = None
        self._main_window: Optional["MainWindow"] = None

        # asyncio 事件循环 / asyncio event loop
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None

        # 状态变更监听器取消函数 / State change listener unregister function
        self._unregister_state_listener: Optional[Callable[[], None]] = None

        # 是否正在处理请求（思考状态）/ Whether processing request (thinking state)
        self._is_processing: bool = False

        # 连接信号到槽 / Connect signals to slots
        self.response_ready.connect(self._on_response_ready)
        self.error_occurred.connect(self._on_error_occurred)

    @property
    def is_processing(self) -> bool:
        """
        是否正在处理请求（思考状态）
        Whether currently processing a request (thinking state)
        """
        return self._is_processing

    def initialize(
        self,
        ucm: "UnifiedContextManager",
        state_manager: "StateManager",
        animation_controller: "AnimationController",
        chat_bubble: "ChatBubble",
        input_panel: "InputPanel",
        main_window: "MainWindow",
    ) -> None:
        """
        初始化所有组件并连接信号
        Initialize all components and connect signals

        Args:
            ucm: 统一上下文管理器 / Unified Context Manager
            state_manager: 状态管理器 / State Manager
            animation_controller: 动画控制器 / Animation Controller
            chat_bubble: 聊天气泡 / Chat Bubble
            input_panel: 输入面板 / Input Panel
            main_window: 主窗口 / Main Window
        """
        # 存储组件引用 / Store component references
        self._ucm = ucm
        self._state_manager = state_manager
        self._animation_controller = animation_controller
        self._chat_bubble = chat_bubble
        self._input_panel = input_panel
        self._main_window = main_window

        # 获取或创建事件循环 / Get or create event loop
        try:
            self._event_loop = asyncio.get_running_loop()
        except RuntimeError:
            self._event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._event_loop)

        # 待处理的响应（用于线程间通信）/ Pending response for thread communication
        self._pending_response: Optional["InteractionResponse"] = None

        # 连接依赖链 / Connect dependency chain
        self._connect_input_to_ucm()
        self._connect_state_to_animation()

    def _connect_input_to_ucm(self) -> None:
        """
        连接 InputPanel.message_submitted → UCM.process_interaction
        Connect InputPanel.message_submitted → UCM.process_interaction

        信号是同步的，UCM 是异步的，需要桥接。
        Signal is sync, UCM is async, needs bridging.
        """
        if not self._input_panel or not self._ucm:
            return

        def on_message_submitted(text: str) -> None:
            """
            处理用户消息提交
            Handle user message submission

            Args:
                text: 用户输入的文本 / User input text
            """
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"收到用户输入: {text}")

            # 显示思考状态 / Show thinking state
            self._show_thinking_state()

            # 在后台线程中运行异步任务
            # Run async task in background thread
            thread = threading.Thread(
                target=self._run_async_handler,
                args=(text,),
                daemon=True,
            )
            thread.start()

        self._input_panel.message_submitted.connect(on_message_submitted)

    def _show_thinking_state(self) -> None:
        """
        显示思考状态
        Show thinking state
        """
        from PySide6.QtCore import QPoint

        # 设置处理中标志 / Set processing flag
        self._is_processing = True

        # 切换到思考动画 / Switch to thinking animation
        if self._animation_controller:
            self._animation_controller.set_animation("thinking")

        # 显示思考气泡 / Show thinking bubble
        if self._chat_bubble and self._main_window:
            anchor = QPoint(
                self._main_window.x() + self._main_window.width() // 2,
                self._main_window.y(),
            )
            self._chat_bubble.show_text(
                "让我想想...",
                use_typing_effect=False,
                anchor_point=anchor,
            )

    def _run_async_handler(self, text: str) -> None:
        """
        在后台线程中运行异步处理
        Run async handler in background thread

        Args:
            text: 用户输入文本 / User input text
        """
        import logging
        logger = logging.getLogger(__name__)

        # 创建新的事件循环 / Create new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # 运行异步处理 / Run async handler
            response = loop.run_until_complete(self._handle_user_message(text))

            # 使用 Qt 信号在主线程中更新 GUI（线程安全）
            # Use Qt signal to update GUI in main thread (thread-safe)
            if response:
                logger.info("发出 response_ready 信号")
                self.response_ready.emit(response)

        except Exception as e:
            logger.error(f"异步处理失败: {e}")
            self.error_occurred.emit(str(e))

        finally:
            loop.close()

    def _on_response_ready(self, response: "InteractionResponse") -> None:
        """
        响应准备完成槽函数（在主线程中调用）
        Response ready slot (called in main thread)

        Args:
            response: UCM 响应 / UCM response
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"_on_response_ready: {response.response_text[:50] if response.response_text else 'None'}...")
        self._display_response(response)

        # 清除处理中标志 / Clear processing flag
        self._is_processing = False

        # 恢复 idle 动画 / Restore idle animation
        if self._animation_controller:
            logger.info("恢复 idle 动画")
            self._animation_controller.set_animation("idle")

    def _on_error_occurred(self, error: str) -> None:
        """
        错误发生槽函数（在主线程中调用）
        Error occurred slot (called in main thread)

        Args:
            error: 错误信息 / Error message
        """
        self._show_error_message(error)

        # 清除处理中标志 / Clear processing flag
        self._is_processing = False

        # 恢复 idle 动画 / Restore idle animation
        if self._animation_controller:
            self._animation_controller.set_animation("idle")

    async def _handle_user_message(self, text: str) -> Optional["InteractionResponse"]:
        """
        异步处理用户消息
        Async handle user message

        流程 / Flow:
        1. 创建 InteractionRequest
        2. 调用 UCM.process_interaction
        3. 返回响应

        Args:
            text: 用户输入文本 / User input text

        Returns:
            InteractionResponse 或 None
        """
        import logging
        logger = logging.getLogger(__name__)

        if not self._ucm:
            logger.error("UCM 未初始化")
            return None

        # 延迟导入避免循环依赖 / Lazy import to avoid circular deps
        from rainze.core.contracts import InteractionRequest, InteractionSource

        # 1. 创建交互请求 / Create interaction request
        request = InteractionRequest.create(
            source=InteractionSource.CHAT_INPUT,
            payload={"text": text},
        )

        logger.info(f"创建交互请求: {request.request_id}")

        try:
            # 2. 通过 UCM 处理（所有交互的唯一入口）
            # Process through UCM (single entry for all interactions)
            response = await self._ucm.process_interaction(request)
            logger.info(f"UCM 响应: success={response.success}, text={response.response_text[:50] if response.response_text else 'None'}...")
            return response

        except Exception as e:
            logger.error(f"UCM 处理异常: {e}")
            raise

    def _display_response(self, response: "InteractionResponse") -> None:
        """
        显示 UCM 响应到 GUI
        Display UCM response to GUI

        连接: UCM 响应 → ChatBubble.show_text + AnimationController.set_expression

        Args:
            response: UCM 响应 / UCM response
        """
        # 延迟导入 / Lazy import
        from PySide6.QtCore import QPoint

        from rainze.core.contracts import InteractionResponse

        if not isinstance(response, InteractionResponse):
            return

        if not response.success:
            self._show_error_message(response.error_message or "处理失败")
            return

        # 显示文本到气泡 / Show text to bubble
        if self._chat_bubble and self._main_window and response.response_text:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"显示气泡: {response.response_text[:50]}...")

            anchor = QPoint(
                self._main_window.x() + self._main_window.width() // 2,
                self._main_window.y(),
            )
            self._chat_bubble.show_text(
                response.response_text,
                use_typing_effect=True,
                anchor_point=anchor,
            )

        # 更新表情 / Update expression
        if self._animation_controller and response.emotion:
            self._animation_controller.apply_emotion_tag(response.emotion)

    def _show_error_message(self, error: str) -> None:
        """
        显示错误消息
        Show error message

        Args:
            error: 错误信息 / Error message
        """
        from PySide6.QtCore import QPoint

        if self._chat_bubble and self._main_window:
            anchor = QPoint(
                self._main_window.x() + self._main_window.width() // 2,
                self._main_window.y(),
            )
            self._chat_bubble.show_text(
                f"呜...出错了: {error}",
                use_typing_effect=False,
                anchor_point=anchor,
            )

    def _connect_state_to_animation(self) -> None:
        """
        连接 StateManager 变更 → AnimationController 动画切换
        Connect StateManager changes → AnimationController animation switch

        状态变化时自动更新角色表情和动画。
        Auto-update character expression and animation on state changes.
        """
        if not self._state_manager or not self._animation_controller:
            return

        # 延迟导入 / Lazy import
        from rainze.state.models import StateChangedEvent, StateChangeType

        def on_state_changed(event: StateChangedEvent) -> None:
            """
            状态变更回调
            State change callback

            Args:
                event: 状态变更事件 / State change event
            """
            if not self._animation_controller:
                return

            # 情绪变化 → 更新表情 / Mood change → update expression
            if event.change_type == StateChangeType.MOOD_CHANGED:
                # event.new_value 是 MoodState 的字符串值
                # event.new_value is string value of MoodState
                mood_to_expression = {
                    "happy": "happy",
                    "normal": "neutral",
                    "tired": "sleepy",
                    "sad": "sad",
                    "anxious": "worried",
                }
                expression = mood_to_expression.get(
                    str(event.new_value).lower(),
                    "neutral",
                )
                # 从 extra 获取强度 / Get intensity from extra
                intensity = 0.5
                if event.extra and "intensity" in event.extra:
                    intensity = event.extra["intensity"]
                self._animation_controller.set_expression(expression, intensity)

            # 能量低 → 切换到疲倦动画 / Low energy → switch to tired animation
            elif event.change_type == StateChangeType.ENERGY_CHANGED:
                if event.extra and event.extra.get("triggered_tired"):
                    self._animation_controller.set_expression("sleepy", 0.7)

            # 好感度提升 → 播放开心特效 / Affinity up → play happy effect
            elif event.change_type == StateChangeType.LEVEL_UP:
                self._animation_controller.set_expression("happy", 0.9)
                self._animation_controller.play_effect("sparkle", 2000)

        # 注册监听器 / Register listener
        self._unregister_state_listener = self._state_manager.register_change_listener(
            on_state_changed
        )

    def cleanup(self) -> None:
        """
        清理资源
        Cleanup resources
        """
        # 取消状态监听 / Unregister state listener
        if self._unregister_state_listener:
            self._unregister_state_listener()
            self._unregister_state_listener = None

        # 清理动画控制器 / Cleanup animation controller
        if self._animation_controller:
            self._animation_controller.cleanup()


# ========================================
# 全局协调器实例 / Global Coordinator Instance
# ========================================

_coordinator: Optional[RainzeCoordinator] = None


def get_coordinator() -> RainzeCoordinator:
    """
    获取全局协调器实例
    Get global coordinator instance

    Returns:
        协调器实例 / Coordinator instance
    """
    global _coordinator
    if _coordinator is None:
        _coordinator = RainzeCoordinator()
    return _coordinator


# ========================================
# 主入口 / Main Entry
# ========================================


def main() -> int:
    """
    应用主入口函数
    Application main entry function

    初始化完整依赖链并运行 Rainze 应用。
    Initializes full dependency chain and runs Rainze application.

    依赖链 / Dependency Chain:
    1. InputPanel.message_submitted → UCM.process_interaction
    2. UCM 响应 → ChatBubble.show_text + AnimationController.set_expression
    3. StateManager 变更 → AnimationController 动画切换

    Returns:
        退出码 / Exit code (0 = 成功 / success)
    """
    # 加载环境变量（从 .env 文件）/ Load environment variables from .env
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass  # dotenv 是可选的 / dotenv is optional

    # 导入 PySide6
    # Import PySide6 (lazy import for faster startup)
    from PySide6.QtCore import QPoint
    from PySide6.QtGui import QFontDatabase
    from PySide6.QtWidgets import QApplication

    from rainze.agent import UnifiedContextManager
    from rainze.animation import AnimationController
    from rainze.core import EventBus
    from rainze.gui import ChatBubble, InputPanel, MainWindow, SystemTray
    from rainze.state import StateManager

    # 1. 创建 Qt 应用 / Create Qt application
    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("Rainze")
    qt_app.setApplicationVersion("0.1.0")
    qt_app.setQuitOnLastWindowClosed(False)  # 托盘模式 / Tray mode

    # 1.1 加载自定义字体 / Load custom fonts
    fonts_dir = Path(__file__).parent.parent.parent / "assets" / "fonts"
    if fonts_dir.exists():
        for font_file in fonts_dir.glob("*.ttf"):
            font_id = QFontDatabase.addApplicationFont(str(font_file))
            if font_id < 0:
                print(f"Warning: Failed to load font {font_file.name}")

    # 2. 确定配置目录 / Determine config directory
    config_dir = Path("./config")
    if not config_dir.exists():
        config_dir.mkdir(parents=True, exist_ok=True)

    # 2.1 加载应用配置 / Load app settings
    import json
    app_settings_path = config_dir / "app_settings.json"
    app_settings: dict[str, Any] = {}
    if app_settings_path.exists():
        with open(app_settings_path, encoding="utf-8") as f:
            app_settings = json.load(f)

    # 3. 创建事件总线 / Create event bus
    event_bus = EventBus()

    # ========================================
    # 4. 创建核心组件（依赖链）/ Create core components (dependency chain)
    # ========================================

    assets_dir = Path("./assets")

    # 4.1 状态管理器 / State Manager
    state_manager = StateManager()

    # 4.2 动画控制器 / Animation Controller
    animation_controller = AnimationController(
        event_bus=event_bus,
        resource_path=str(assets_dir / "animations"),
        fps=30,
        canvas_size=(256, 256),
    )

    # 4.3 统一上下文管理器 (UCM) - 所有交互的唯一入口
    # Unified Context Manager - Single entry point for all interactions
    ucm = UnifiedContextManager()

    # ========================================
    # 5. 创建 GUI 组件 / Create GUI components
    # ========================================

    # 5.1 主窗口 / Main window
    main_window = MainWindow(
        event_bus=event_bus,
        default_size=(200, 200),
        assets_dir=assets_dir,
    )

    # 5.2 聊天气泡 / Chat bubble
    chat_bubble = ChatBubble(
        show_feedback_buttons=False,
        auto_hide_ms=10000,
        typing_speed_ms=50,
    )

    # 5.3 输入面板 / Input panel
    input_config = app_settings.get("input", {})
    input_panel = InputPanel(
        max_history=input_config.get("max_history", 50),
        placeholder="和我聊聊吧~",
        max_length=input_config.get("max_length", 1000),
        show_send_button=True,
    )
    input_panel.setFixedWidth(300)

    # 5.4 系统托盘 / System tray
    system_tray = SystemTray(
        event_bus=event_bus,
        icon_path=assets_dir / "ui" / "icons" / "tray_icon.png",
        app_name="Rainze",
    )

    # ========================================
    # 6. 初始化协调器并连接依赖链
    # Initialize coordinator and connect dependency chain
    # ========================================

    coordinator = get_coordinator()
    coordinator.initialize(
        ucm=ucm,
        state_manager=state_manager,
        animation_controller=animation_controller,
        chat_bubble=chat_bubble,
        input_panel=input_panel,
        main_window=main_window,
    )

    # ========================================
    # 7. 连接 GUI 信号 / Connect GUI signals
    # ========================================

    # 连接动画帧更新到主窗口 / Connect animation frame update to main window
    animation_controller.frame_ready.connect(main_window.update_frame)

    # 窗口显示/隐藏 / Window show/hide
    def on_show_requested() -> None:
        main_window.show()
        system_tray.update_toggle_text(True)

    def on_hide_requested() -> None:
        main_window.hide()
        system_tray.update_toggle_text(False)

    system_tray.show_requested.connect(on_show_requested)
    system_tray.hide_requested.connect(on_hide_requested)
    system_tray.quit_requested.connect(qt_app.quit)

    # 点击显示气泡和输入面板 / Click shows bubble and input panel
    def on_pet_clicked() -> None:
        # 如果正在处理请求，不要覆盖思考状态的气泡
        # Don't override thinking bubble if processing
        if coordinator.is_processing:
            return

        # 在桌宠头顶显示气泡 / Show bubble above pet
        anchor = QPoint(
            main_window.x() + main_window.width() // 2,
            main_window.y(),
        )
        chat_bubble.show_text(
            "你好呀~ 点击我可以和我聊天哦！喵~",
            use_typing_effect=True,
            anchor_point=anchor,
        )
        # 显示输入面板 / Show input panel
        input_anchor = QPoint(
            main_window.x() + main_window.width() // 2,
            main_window.y() + main_window.height() + 10,
        )
        input_panel.show_panel(input_anchor)

    main_window.pet_clicked.connect(on_pet_clicked)

    # 双击切换模式 / Double click toggles mode
    main_window.pet_double_clicked.connect(main_window.toggle_display_mode)

    # 气泡隐藏时，仅当用户未在输入时隐藏输入面板
    # Hide input panel when bubble hides, only if user is not typing
    def on_bubble_hidden() -> None:
        # 如果输入框有内容，说明用户正在输入，不隐藏
        # If input has content, user is typing, don't hide
        if input_panel.get_text().strip():
            return
        input_panel.hide_panel()

    chat_bubble.hidden_signal.connect(on_bubble_hidden)

    # ========================================
    # 8. 启动应用 / Start application
    # ========================================

    # 显示窗口 / Show window
    main_window.move_to_corner("bottom_right")
    main_window.show()
    system_tray.show()

    # 加载初始动画并启动渲染循环 / Load initial animation and start render loop
    animation_controller.set_animation("idle")
    animation_controller.start_render_loop()

    # 显示欢迎消息 / Show welcome message
    system_tray.show_notification(
        "Rainze",
        "桌宠已启动！点击我开始互动吧~ 喵~",
    )

    # ========================================
    # 9. 运行事件循环 / Run event loop
    # ========================================

    # 清理回调 / Cleanup callback
    def cleanup() -> None:
        coordinator.cleanup()
        animation_controller.cleanup()

    qt_app.aboutToQuit.connect(cleanup)

    return qt_app.exec()


if __name__ == "__main__":
    sys.exit(main())
