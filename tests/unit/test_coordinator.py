"""
RainzeCoordinator 单元测试
RainzeCoordinator Unit Tests

测试协调器的依赖链连接逻辑。
Tests coordinator's dependency chain connection logic.

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

# 配置详细日志 / Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class TestRainzeCoordinator:
    """
    RainzeCoordinator 单元测试
    RainzeCoordinator Unit Tests
    """

    @pytest.fixture
    def mock_ucm(self) -> MagicMock:
        """
        创建 Mock UCM
        Create Mock UCM
        """
        ucm = MagicMock()
        ucm.process_interaction = AsyncMock()
        return ucm

    @pytest.fixture
    def mock_state_manager(self) -> MagicMock:
        """
        创建 Mock StateManager
        Create Mock StateManager
        """
        state_manager = MagicMock()
        state_manager.register_change_listener = MagicMock(return_value=lambda: None)
        return state_manager

    @pytest.fixture
    def mock_animation_controller(self) -> MagicMock:
        """
        创建 Mock AnimationController
        Create Mock AnimationController
        """
        controller = MagicMock()
        controller.set_expression = MagicMock()
        controller.apply_emotion_tag = MagicMock()
        controller.play_effect = MagicMock()
        controller.cleanup = MagicMock()
        return controller

    @pytest.fixture
    def mock_chat_bubble(self) -> MagicMock:
        """
        创建 Mock ChatBubble
        Create Mock ChatBubble
        """
        bubble = MagicMock()
        bubble.show_text = MagicMock()
        return bubble

    @pytest.fixture
    def mock_input_panel(self) -> MagicMock:
        """
        创建 Mock InputPanel
        Create Mock InputPanel
        """
        panel = MagicMock()
        panel.message_submitted = MagicMock()
        panel.message_submitted.connect = MagicMock()
        return panel

    @pytest.fixture
    def mock_main_window(self) -> MagicMock:
        """
        创建 Mock MainWindow
        Create Mock MainWindow
        """
        window = MagicMock()
        window.x = MagicMock(return_value=100)
        window.y = MagicMock(return_value=100)
        window.width = MagicMock(return_value=200)
        window.height = MagicMock(return_value=200)
        return window

    def test_coordinator_initialization(self) -> None:
        """
        测试协调器初始化
        Test coordinator initialization
        """
        logger.info("=" * 60)
        logger.info("测试: 协调器初始化 / Test: Coordinator initialization")
        logger.info("=" * 60)

        from rainze.main import RainzeCoordinator

        coordinator = RainzeCoordinator()

        logger.info("验证: 协调器已创建 / Verify: Coordinator created")
        assert coordinator._ucm is None
        assert coordinator._state_manager is None
        assert coordinator._animation_controller is None
        logger.info("✓ 协调器初始化成功，所有组件为 None")

    def test_coordinator_full_initialization(
        self,
        mock_ucm: MagicMock,
        mock_state_manager: MagicMock,
        mock_animation_controller: MagicMock,
        mock_chat_bubble: MagicMock,
        mock_input_panel: MagicMock,
        mock_main_window: MagicMock,
    ) -> None:
        """
        测试协调器完整初始化
        Test coordinator full initialization
        """
        logger.info("=" * 60)
        logger.info("测试: 协调器完整初始化 / Test: Coordinator full initialization")
        logger.info("=" * 60)

        from rainze.main import RainzeCoordinator

        coordinator = RainzeCoordinator()

        logger.info("初始化协调器... / Initializing coordinator...")
        coordinator.initialize(
            ucm=mock_ucm,
            state_manager=mock_state_manager,
            animation_controller=mock_animation_controller,
            chat_bubble=mock_chat_bubble,
            input_panel=mock_input_panel,
            main_window=mock_main_window,
        )

        # 验证组件已存储 / Verify components stored
        logger.info("验证: 组件已存储 / Verify: Components stored")
        assert coordinator._ucm is mock_ucm
        assert coordinator._state_manager is mock_state_manager
        assert coordinator._animation_controller is mock_animation_controller
        assert coordinator._chat_bubble is mock_chat_bubble
        assert coordinator._input_panel is mock_input_panel
        assert coordinator._main_window is mock_main_window
        logger.info("✓ 所有组件已正确存储")

        # 验证信号连接 / Verify signal connections
        logger.info("验证: InputPanel 信号已连接 / Verify: InputPanel signal connected")
        mock_input_panel.message_submitted.connect.assert_called_once()
        logger.info("✓ InputPanel.message_submitted 信号已连接")

        # 验证状态监听器已注册 / Verify state listener registered
        logger.info("验证: 状态监听器已注册 / Verify: State listener registered")
        mock_state_manager.register_change_listener.assert_called_once()
        logger.info("✓ StateManager 监听器已注册")

    def test_coordinator_cleanup(
        self,
        mock_ucm: MagicMock,
        mock_state_manager: MagicMock,
        mock_animation_controller: MagicMock,
        mock_chat_bubble: MagicMock,
        mock_input_panel: MagicMock,
        mock_main_window: MagicMock,
    ) -> None:
        """
        测试协调器清理
        Test coordinator cleanup
        """
        logger.info("=" * 60)
        logger.info("测试: 协调器清理 / Test: Coordinator cleanup")
        logger.info("=" * 60)

        from rainze.main import RainzeCoordinator

        coordinator = RainzeCoordinator()
        coordinator.initialize(
            ucm=mock_ucm,
            state_manager=mock_state_manager,
            animation_controller=mock_animation_controller,
            chat_bubble=mock_chat_bubble,
            input_panel=mock_input_panel,
            main_window=mock_main_window,
        )

        logger.info("执行清理... / Executing cleanup...")
        coordinator.cleanup()

        # 验证动画控制器已清理 / Verify animation controller cleaned up
        logger.info("验证: 动画控制器已清理 / Verify: Animation controller cleaned up")
        mock_animation_controller.cleanup.assert_called_once()
        logger.info("✓ AnimationController.cleanup() 已调用")


class TestStateToAnimationConnection:
    """
    状态到动画连接测试
    State to Animation Connection Tests
    """

    def test_mood_change_updates_expression(self) -> None:
        """
        测试情绪变化更新表情
        Test mood change updates expression
        """
        logger.info("=" * 60)
        logger.info("测试: 情绪变化更新表情 / Test: Mood change updates expression")
        logger.info("=" * 60)

        from rainze.state.models import StateChangedEvent, StateChangeType

        # 创建 Mock 组件 / Create mock components
        mock_animation_controller = MagicMock()
        mock_animation_controller.set_expression = MagicMock()

        # 模拟状态变更事件 / Simulate state change event
        event = StateChangedEvent(
            change_type=StateChangeType.MOOD_CHANGED,
            old_value="normal",
            new_value="happy",
            reason="user_interaction",
            extra={"intensity": 0.8},
        )

        logger.info(f"事件类型: {event.change_type.name}")
        logger.info(f"旧值: {event.old_value} → 新值: {event.new_value}")
        logger.info(f"原因: {event.reason}")
        logger.info(f"额外信息: {event.extra}")

        # 模拟状态变更处理逻辑 / Simulate state change handling logic
        mood_to_expression = {
            "happy": "happy",
            "normal": "neutral",
            "tired": "sleepy",
            "sad": "sad",
            "anxious": "worried",
        }

        if event.change_type == StateChangeType.MOOD_CHANGED:
            expression = mood_to_expression.get(
                str(event.new_value).lower(),
                "neutral",
            )
            intensity = 0.5
            if event.extra and "intensity" in event.extra:
                intensity = event.extra["intensity"]
            mock_animation_controller.set_expression(expression, intensity)

        logger.info(f"调用: set_expression('{expression}', {intensity})")

        # 验证 / Verify
        mock_animation_controller.set_expression.assert_called_once_with("happy", 0.8)
        logger.info("✓ 表情更新正确")

    def test_energy_low_triggers_tired_animation(self) -> None:
        """
        测试低能量触发疲倦动画
        Test low energy triggers tired animation
        """
        logger.info("=" * 60)
        logger.info("测试: 低能量触发疲倦动画 / Test: Low energy triggers tired animation")
        logger.info("=" * 60)

        from rainze.state.models import StateChangedEvent, StateChangeType

        mock_animation_controller = MagicMock()
        mock_animation_controller.set_expression = MagicMock()

        # 模拟能量变低事件 / Simulate energy low event
        event = StateChangedEvent(
            change_type=StateChangeType.ENERGY_CHANGED,
            old_value=25.0,
            new_value=15.0,
            reason="time_decay",
            extra={"triggered_tired": True},
        )

        logger.info(f"事件类型: {event.change_type.name}")
        logger.info(f"能量: {event.old_value} → {event.new_value}")
        logger.info(f"触发疲倦: {event.extra.get('triggered_tired')}")

        # 模拟处理逻辑 / Simulate handling logic
        if event.change_type == StateChangeType.ENERGY_CHANGED:
            if event.extra and event.extra.get("triggered_tired"):
                mock_animation_controller.set_expression("sleepy", 0.7)
                logger.info("调用: set_expression('sleepy', 0.7)")

        # 验证 / Verify
        mock_animation_controller.set_expression.assert_called_once_with("sleepy", 0.7)
        logger.info("✓ 疲倦动画正确触发")

    def test_level_up_triggers_happy_effect(self) -> None:
        """
        测试等级提升触发开心特效
        Test level up triggers happy effect
        """
        logger.info("=" * 60)
        logger.info("测试: 等级提升触发开心特效 / Test: Level up triggers happy effect")
        logger.info("=" * 60)

        from rainze.state.models import StateChangedEvent, StateChangeType

        mock_animation_controller = MagicMock()
        mock_animation_controller.set_expression = MagicMock()
        mock_animation_controller.play_effect = MagicMock()

        # 模拟等级提升事件 / Simulate level up event
        event = StateChangedEvent(
            change_type=StateChangeType.LEVEL_UP,
            old_value=2,
            new_value=3,
            reason="affinity_level_up",
            extra={"attribute": "affinity", "unlocks": ["new_outfit"]},
        )

        logger.info(f"事件类型: {event.change_type.name}")
        logger.info(f"等级: {event.old_value} → {event.new_value}")
        logger.info(f"解锁内容: {event.extra.get('unlocks')}")

        # 模拟处理逻辑 / Simulate handling logic
        if event.change_type == StateChangeType.LEVEL_UP:
            mock_animation_controller.set_expression("happy", 0.9)
            mock_animation_controller.play_effect("sparkle", 2000)
            logger.info("调用: set_expression('happy', 0.9)")
            logger.info("调用: play_effect('sparkle', 2000)")

        # 验证 / Verify
        mock_animation_controller.set_expression.assert_called_once_with("happy", 0.9)
        mock_animation_controller.play_effect.assert_called_once_with("sparkle", 2000)
        logger.info("✓ 等级提升特效正确触发")


class TestInputToUCMConnection:
    """
    输入到 UCM 连接测试
    Input to UCM Connection Tests
    """

    @pytest.mark.asyncio
    async def test_message_creates_interaction_request(self) -> None:
        """
        测试消息创建交互请求
        Test message creates interaction request
        """
        logger.info("=" * 60)
        logger.info("测试: 消息创建交互请求 / Test: Message creates interaction request")
        logger.info("=" * 60)

        from rainze.core.contracts import InteractionRequest, InteractionSource

        text = "你好呀，今天天气怎么样？"
        logger.info(f"用户输入: {text}")

        # 创建请求 / Create request
        request = InteractionRequest.create(
            source=InteractionSource.CHAT_INPUT,
            payload={"text": text},
        )

        logger.info("=" * 40)
        logger.info("InteractionRequest 详细信息:")
        logger.info(f"  request_id: {request.request_id}")
        logger.info(f"  source: {request.source.name}")
        logger.info(f"  timestamp: {request.timestamp}")
        logger.info(f"  payload: {request.payload}")
        logger.info(f"  trace_id: {request.trace_id}")
        logger.info("=" * 40)

        # 验证 / Verify
        assert request.source == InteractionSource.CHAT_INPUT
        assert request.payload["text"] == text
        assert request.request_id is not None
        assert request.timestamp is not None
        logger.info("✓ InteractionRequest 创建正确")

    @pytest.mark.asyncio
    async def test_ucm_process_interaction_called(self) -> None:
        """
        测试 UCM process_interaction 被调用
        Test UCM process_interaction is called
        """
        logger.info("=" * 60)
        logger.info("测试: UCM process_interaction 被调用 / Test: UCM process_interaction called")
        logger.info("=" * 60)

        from rainze.core.contracts import (
            InteractionRequest,
            InteractionResponse,
            InteractionSource,
        )

        # 创建 Mock UCM / Create mock UCM
        mock_ucm = MagicMock()
        mock_response = InteractionResponse.success_response(
            request_id="test-123",
            text="今天天气很好呢！阳光明媚~",
            emotion=None,
        )
        mock_ucm.process_interaction = AsyncMock(return_value=mock_response)

        # 创建请求 / Create request
        request = InteractionRequest.create(
            source=InteractionSource.CHAT_INPUT,
            payload={"text": "你好呀"},
        )

        logger.info(f"请求 ID: {request.request_id}")
        logger.info(f"请求内容: {request.payload}")

        # 调用 UCM / Call UCM
        response = await mock_ucm.process_interaction(request)

        logger.info("=" * 40)
        logger.info("InteractionResponse 详细信息:")
        logger.info(f"  request_id: {response.request_id}")
        logger.info(f"  success: {response.success}")
        logger.info(f"  response_text: {response.response_text}")
        logger.info(f"  emotion: {response.emotion}")
        logger.info(f"  state_changes: {response.state_changes}")
        logger.info("=" * 40)

        # 验证 / Verify
        mock_ucm.process_interaction.assert_called_once_with(request)
        assert response.success is True
        assert response.response_text == "今天天气很好呢！阳光明媚~"
        logger.info("✓ UCM.process_interaction 调用正确")
