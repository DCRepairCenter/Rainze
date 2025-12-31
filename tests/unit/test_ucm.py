"""
UCM 单元测试
UCM Unit Tests

测试统一上下文管理器的核心逻辑。
Tests Unified Context Manager core logic.

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import json
import logging

import pytest

# 配置详细日志 / Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class TestSceneClassification:
    """
    场景分类测试
    Scene Classification Tests
    """

    def test_chat_input_classification(self) -> None:
        """
        测试聊天输入场景分类
        Test chat input scene classification
        """
        logger.info("=" * 60)
        logger.info("测试: 聊天输入场景分类 / Test: Chat input scene classification")
        logger.info("=" * 60)

        from rainze.agent import SceneClassifier
        from rainze.core.contracts import InteractionSource

        classifier = SceneClassifier()

        # 测试用户对话输入 / Test user chat input
        result = classifier.classify(
            source=InteractionSource.CHAT_INPUT,
            user_input="你好呀，今天过得怎么样？",
        )

        logger.info("=" * 40)
        logger.info("分类结果详细信息:")
        logger.info(f"  scene_id: {result.scene_id}")
        logger.info(f"  scene_type: {result.scene_type.name}")
        logger.info(f"  default_tier: {result.mapping.default_tier.name}")
        logger.info(f"  mapping: {result.mapping}")
        logger.info("=" * 40)

        assert result is not None
        assert result.scene_id is not None
        logger.info("✓ 聊天输入分类成功")

    def test_passive_trigger_classification(self) -> None:
        """
        测试被动触发场景分类
        Test passive trigger scene classification
        """
        logger.info("=" * 60)
        logger.info("测试: 被动触发场景分类 / Test: Passive trigger scene classification")
        logger.info("=" * 60)

        from rainze.agent import SceneClassifier
        from rainze.core.contracts import InteractionSource

        classifier = SceneClassifier()

        # 测试点击事件 / Test click event
        result = classifier.classify(
            source=InteractionSource.PASSIVE_TRIGGER,
            event_type="click",
        )

        logger.info("=" * 40)
        logger.info("分类结果详细信息:")
        logger.info(f"  scene_id: {result.scene_id}")
        logger.info(f"  scene_type: {result.scene_type.name}")
        logger.info(f"  default_tier: {result.mapping.default_tier.name}")
        logger.info(f"  memory_retrieval: {result.mapping.memory_retrieval}")
        logger.info("=" * 40)

        assert result is not None
        logger.info("✓ 被动触发分类成功")

    def test_system_event_classification(self) -> None:
        """
        测试系统事件场景分类
        Test system event scene classification
        """
        logger.info("=" * 60)
        logger.info("测试: 系统事件场景分类 / Test: System event scene classification")
        logger.info("=" * 60)

        from rainze.agent import SceneClassifier
        from rainze.core.contracts import InteractionSource

        classifier = SceneClassifier()

        # 测试整点报时 / Test hourly chime
        result = classifier.classify(
            source=InteractionSource.SYSTEM_EVENT,
            event_type="hourly_chime",
            context={"hour": 14},
        )

        logger.info("=" * 40)
        logger.info("分类结果详细信息:")
        logger.info(f"  scene_id: {result.scene_id}")
        logger.info(f"  scene_type: {result.scene_type.name}")
        logger.info(f"  default_tier: {result.mapping.default_tier.name}")
        logger.info("=" * 40)

        assert result is not None
        logger.info("✓ 系统事件分类成功")


class TestTierHandlers:
    """
    层级处理器测试
    Tier Handler Tests
    """

    def test_tier1_template_handler(self) -> None:
        """
        测试 Tier1 模板处理器
        Test Tier1 template handler
        """
        logger.info("=" * 60)
        logger.info("测试: Tier1 模板处理器 / Test: Tier1 template handler")
        logger.info("=" * 60)

        from rainze.agent import Tier1TemplateHandler
        from rainze.core.contracts import InteractionRequest, InteractionSource, ResponseTier

        handler = Tier1TemplateHandler()

        # 创建点击请求 / Create click request
        request = InteractionRequest.create(
            source=InteractionSource.PASSIVE_TRIGGER,
            payload={"event_type": "click"},
        )

        logger.info(f"请求 source: {request.source.name}")
        logger.info(f"请求 payload: {request.payload}")
        logger.info(f"handler.tier: {handler.tier.name}")
        logger.info(f"handler.timeout_ms: {handler.timeout_ms}")

        assert handler.tier == ResponseTier.TIER1_TEMPLATE
        logger.info("✓ Tier1 处理器测试通过")

    def test_tier2_rule_handler(self) -> None:
        """
        测试 Tier2 规则处理器
        Test Tier2 rule handler
        """
        logger.info("=" * 60)
        logger.info("测试: Tier2 规则处理器 / Test: Tier2 rule handler")
        logger.info("=" * 60)

        from rainze.agent import Tier2RuleHandler
        from rainze.core.contracts import InteractionRequest, InteractionSource, ResponseTier

        handler = Tier2RuleHandler()

        # 创建系统事件请求 / Create system event request
        request = InteractionRequest.create(
            source=InteractionSource.SYSTEM_EVENT,
            payload={"event_type": "hourly_chime", "hour": 14},
        )

        logger.info(f"请求 source: {request.source.name}")
        logger.info(f"请求 payload: {request.payload}")
        logger.info(f"handler.tier: {handler.tier.name}")
        logger.info(f"handler.timeout_ms: {handler.timeout_ms}")

        assert handler.tier == ResponseTier.TIER2_RULE
        logger.info("✓ Tier2 处理器测试通过")


class TestUCMProcessInteraction:
    """
    UCM process_interaction 测试
    UCM process_interaction Tests
    """

    @pytest.mark.asyncio
    async def test_ucm_initialization(self) -> None:
        """
        测试 UCM 初始化
        Test UCM initialization
        """
        logger.info("=" * 60)
        logger.info("测试: UCM 初始化 / Test: UCM initialization")
        logger.info("=" * 60)

        from rainze.agent import UnifiedContextManager

        ucm = UnifiedContextManager()

        # 获取上下文摘要 / Get context summary
        summary = await ucm.get_context_summary()

        logger.info("=" * 40)
        logger.info("UCM 上下文摘要:")
        logger.info(json.dumps(summary, indent=2, ensure_ascii=False))
        logger.info("=" * 40)

        assert summary["interaction_count"] == 0
        assert "tier_handlers" in summary
        assert "memory_policies" in summary
        logger.info("✓ UCM 初始化成功")

    @pytest.mark.asyncio
    async def test_process_chat_input(self) -> None:
        """
        测试处理聊天输入
        Test process chat input
        """
        logger.info("=" * 60)
        logger.info("测试: 处理聊天输入 / Test: Process chat input")
        logger.info("=" * 60)

        from rainze.agent import UnifiedContextManager
        from rainze.core.contracts import InteractionRequest, InteractionSource

        ucm = UnifiedContextManager()

        # 创建聊天请求 / Create chat request
        request = InteractionRequest.create(
            source=InteractionSource.CHAT_INPUT,
            payload={"text": "你好呀！"},
        )

        logger.info("=" * 40)
        logger.info("请求详细信息:")
        logger.info(f"  request_id: {request.request_id}")
        logger.info(f"  source: {request.source.name}")
        logger.info(f"  payload: {request.payload}")
        logger.info(f"  timestamp: {request.timestamp}")
        logger.info("=" * 40)

        # 处理交互 / Process interaction
        response = await ucm.process_interaction(request)

        logger.info("=" * 40)
        logger.info("响应详细信息:")
        logger.info(f"  request_id: {response.request_id}")
        logger.info(f"  success: {response.success}")
        logger.info(f"  response_text: {response.response_text}")
        logger.info(f"  emotion: {response.emotion}")
        logger.info(f"  state_changes: {response.state_changes}")
        logger.info(f"  error_message: {response.error_message}")
        logger.info("=" * 40)

        # 验证 / Verify
        assert response.request_id == request.request_id
        logger.info("✓ 聊天输入处理完成")

    @pytest.mark.asyncio
    async def test_process_passive_trigger(self) -> None:
        """
        测试处理被动触发
        Test process passive trigger
        """
        logger.info("=" * 60)
        logger.info("测试: 处理被动触发 / Test: Process passive trigger")
        logger.info("=" * 60)

        from rainze.agent import UnifiedContextManager
        from rainze.core.contracts import InteractionRequest, InteractionSource

        ucm = UnifiedContextManager()

        # 创建点击请求 / Create click request
        request = InteractionRequest.create(
            source=InteractionSource.PASSIVE_TRIGGER,
            payload={"event_type": "click"},
        )

        logger.info("=" * 40)
        logger.info("请求详细信息:")
        logger.info(f"  request_id: {request.request_id}")
        logger.info(f"  source: {request.source.name}")
        logger.info(f"  payload: {request.payload}")
        logger.info("=" * 40)

        # 处理交互 / Process interaction
        response = await ucm.process_interaction(request)

        logger.info("=" * 40)
        logger.info("响应详细信息:")
        logger.info(f"  request_id: {response.request_id}")
        logger.info(f"  success: {response.success}")
        logger.info(f"  response_text: {response.response_text}")
        logger.info(f"  state_changes: {response.state_changes}")
        logger.info("=" * 40)

        # 验证 / Verify
        assert response.request_id == request.request_id
        # Tier1 应该很快响应 / Tier1 should respond quickly
        if response.success:
            tier_used = response.state_changes.get("tier_used")
            logger.info(f"使用的 Tier: {tier_used}")
        logger.info("✓ 被动触发处理完成")

    @pytest.mark.asyncio
    async def test_interaction_count_increments(self) -> None:
        """
        测试交互计数递增
        Test interaction count increments
        """
        logger.info("=" * 60)
        logger.info("测试: 交互计数递增 / Test: Interaction count increments")
        logger.info("=" * 60)

        from rainze.agent import UnifiedContextManager
        from rainze.core.contracts import InteractionRequest, InteractionSource

        ucm = UnifiedContextManager()

        # 初始计数 / Initial count
        summary_before = await ucm.get_context_summary()
        logger.info(f"初始交互计数: {summary_before['interaction_count']}")

        # 处理多个交互 / Process multiple interactions
        for i in range(3):
            request = InteractionRequest.create(
                source=InteractionSource.PASSIVE_TRIGGER,
                payload={"event_type": "click"},
            )
            await ucm.process_interaction(request)

        # 验证计数 / Verify count
        summary_after = await ucm.get_context_summary()
        logger.info(f"处理后交互计数: {summary_after['interaction_count']}")

        assert summary_after["interaction_count"] == 3
        logger.info("✓ 交互计数正确递增")
