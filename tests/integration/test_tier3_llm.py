"""
Tier3 LLM 完整集成测试
Tier3 LLM Full Integration Tests

测试 Tier3LLMHandler 的完整 LLM 调用流程，记录详细日志。
Tests Tier3LLMHandler's full LLM call flow with detailed logging.

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pytest

# ========================================
# 日志配置 / Logging Configuration
# ========================================

LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

RUN_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"tier3_test_{RUN_TIMESTAMP}.log"
REQUEST_LOG_FILE = LOG_DIR / f"tier3_requests_{RUN_TIMESTAMP}.json"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)
REQUEST_RECORDS: list[Dict[str, Any]] = []


def save_request_record(record: Dict[str, Any]) -> None:
    """保存请求记录"""
    REQUEST_RECORDS.append(record)
    with open(REQUEST_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(REQUEST_RECORDS, f, ensure_ascii=False, indent=2, default=str)


class TestTier3LLMHandler:
    """
    Tier3 LLM Handler 完整测试
    Tier3 LLM Handler Full Tests
    """

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_tier3_conversation_with_llm(self) -> None:
        """
        测试 Tier3 对话场景的完整 LLM 调用
        Test Tier3 conversation scene with full LLM call
        """
        logger.info("=" * 60)
        logger.info("集成测试: Tier3 对话场景 LLM 调用")
        logger.info("Integration Test: Tier3 Conversation LLM Call")
        logger.info("=" * 60)

        from rainze.agent import SceneClassifier, TierHandlerRegistry
        from rainze.core.contracts import InteractionRequest, InteractionSource

        # 创建组件 / Create components
        classifier = SceneClassifier()
        handlers = TierHandlerRegistry()

        # 用户对话输入 / User chat input
        user_input = "你好呀！今天天气怎么样？我想出去走走。"

        # 创建请求 / Create request
        request = InteractionRequest.create(
            source=InteractionSource.CHAT_INPUT,
            payload={"text": user_input},
        )

        # 场景分类 / Scene classification
        classification = classifier.classify(
            source=request.source,
            user_input=user_input,
        )

        # 记录请求详情 / Record request details
        record = {
            "test_name": "test_tier3_conversation_with_llm",
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "request": {
                "request_id": request.request_id,
                "source": request.source.name,
                "payload": request.payload,
            },
            "classification": {
                "scene_id": classification.scene_id,
                "scene_type": classification.scene_type.name,
                "default_tier": classification.mapping.default_tier.name,
            },
        }

        logger.info("请求详情:")
        logger.info(json.dumps(record["request"], indent=2, ensure_ascii=False))
        logger.info("分类结果:")
        logger.info(json.dumps(record["classification"], indent=2, ensure_ascii=False))

        # 调用 Tier3 处理器 / Call Tier3 handler
        start_time = datetime.now()

        # 构建上下文 / Build context
        context = {
            "memory_context": {},
            "current_hour": datetime.now().hour,
            "pet_mood": "happy",
            "pet_energy": 80,
        }

        response = await handlers.handle_with_fallback(
            request=request,
            classification=classification,
            context=context,
        )

        end_time = datetime.now()
        latency_ms = (end_time - start_time).total_seconds() * 1000

        # 记录响应 / Record response
        record["context"] = context
        record["response"] = {
            "success": response.success,
            "text": response.text,
            "emotion": str(response.emotion) if response.emotion else None,
            "tier_used": response.tier_used.name if response.tier_used else None,
            "latency_ms": response.latency_ms,
            "fallback_used": response.fallback_used,
        }
        record["total_latency_ms"] = latency_ms

        save_request_record(record)

        logger.info("=" * 40)
        logger.info("响应详情:")
        logger.info(json.dumps(record["response"], indent=2, ensure_ascii=False))
        logger.info(f"总延迟: {latency_ms:.2f}ms")
        logger.info("=" * 40)

        # 验证 / Verify
        assert response.success or response.fallback_used
        assert response.text is not None and len(response.text) > 0
        logger.info(f"✓ Tier3 对话测试完成，响应: {response.text[:50]}...")

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_tier3_emotional_conversation(self) -> None:
        """
        测试 Tier3 情感对话
        Test Tier3 emotional conversation
        """
        logger.info("=" * 60)
        logger.info("集成测试: Tier3 情感对话")
        logger.info("Integration Test: Tier3 Emotional Conversation")
        logger.info("=" * 60)

        from rainze.agent import SceneClassifier, TierHandlerRegistry
        from rainze.core.contracts import InteractionRequest, InteractionSource

        classifier = SceneClassifier()
        handlers = TierHandlerRegistry()

        # 情感对话输入 / Emotional conversation input
        user_input = "今天工作好累啊，感觉有点沮丧..."

        request = InteractionRequest.create(
            source=InteractionSource.CHAT_INPUT,
            payload={"text": user_input},
        )

        classification = classifier.classify(
            source=request.source,
            user_input=user_input,
        )

        record = {
            "test_name": "test_tier3_emotional_conversation",
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "classification": {
                "scene_id": classification.scene_id,
                "scene_type": classification.scene_type.name,
            },
        }

        logger.info(f"用户输入: {user_input}")

        context = {
            "current_hour": datetime.now().hour,
            "pet_mood": "anxious",  # 宠物感知到用户情绪
        }

        start_time = datetime.now()
        response = await handlers.handle_with_fallback(
            request=request,
            classification=classification,
            context=context,
        )
        latency_ms = (datetime.now() - start_time).total_seconds() * 1000

        record["response"] = {
            "success": response.success,
            "text": response.text,
            "emotion": str(response.emotion) if response.emotion else None,
            "tier_used": response.tier_used.name if response.tier_used else None,
        }
        record["latency_ms"] = latency_ms

        save_request_record(record)

        logger.info(f"响应: {response.text}")
        if response.emotion:
            logger.info(f"情感: {response.emotion.tag} (强度: {response.emotion.intensity})")
        logger.info(f"延迟: {latency_ms:.2f}ms")

        assert response.success or response.fallback_used
        logger.info("✓ 情感对话测试完成")

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_tier3_complex_query(self) -> None:
        """
        测试 Tier3 复杂查询
        Test Tier3 complex query
        """
        logger.info("=" * 60)
        logger.info("集成测试: Tier3 复杂查询")
        logger.info("Integration Test: Tier3 Complex Query")
        logger.info("=" * 60)

        from rainze.agent import SceneClassifier, TierHandlerRegistry
        from rainze.core.contracts import InteractionRequest, InteractionSource

        classifier = SceneClassifier()
        handlers = TierHandlerRegistry()

        # 复杂查询 / Complex query
        user_input = "你觉得我应该怎么安排今天下午的时间？有什么好建议吗？"

        request = InteractionRequest.create(
            source=InteractionSource.CHAT_INPUT,
            payload={"text": user_input},
        )

        classification = classifier.classify(
            source=request.source,
            user_input=user_input,
        )

        record = {
            "test_name": "test_tier3_complex_query",
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
        }

        logger.info(f"用户输入: {user_input}")

        start_time = datetime.now()
        response = await handlers.handle_with_fallback(
            request=request,
            classification=classification,
            context={"current_hour": 14},
        )
        latency_ms = (datetime.now() - start_time).total_seconds() * 1000

        record["response"] = {
            "success": response.success,
            "text": response.text,
            "tier_used": response.tier_used.name if response.tier_used else None,
        }
        record["latency_ms"] = latency_ms

        save_request_record(record)

        logger.info(f"响应: {response.text}")
        logger.info(f"使用的 Tier: {response.tier_used.name if response.tier_used else 'N/A'}")
        logger.info(f"延迟: {latency_ms:.2f}ms")

        assert response.success or response.fallback_used
        logger.info("✓ 复杂查询测试完成")

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_tier3_with_memory_context(self) -> None:
        """
        测试带记忆上下文的 Tier3 响应
        Test Tier3 response with memory context
        """
        logger.info("=" * 60)
        logger.info("集成测试: Tier3 带记忆上下文")
        logger.info("Integration Test: Tier3 with Memory Context")
        logger.info("=" * 60)

        from rainze.agent import SceneClassifier, TierHandlerRegistry
        from rainze.core.contracts import InteractionRequest, InteractionSource

        classifier = SceneClassifier()
        handlers = TierHandlerRegistry()

        user_input = "你还记得我之前说过什么吗？"

        request = InteractionRequest.create(
            source=InteractionSource.CHAT_INPUT,
            payload={"text": user_input},
        )

        classification = classifier.classify(
            source=request.source,
            user_input=user_input,
        )

        # 模拟记忆上下文 / Simulate memory context
        context = {
            "memory_context": {
                "relevant_memories": [
                    "用户昨天说今天要加班",
                    "用户喜欢喝咖啡",
                    "用户最近在学习编程",
                ],
                "user_preferences": "喜欢简短的回复",
            },
            "conversation_history": [
                {"role": "user", "content": "早上好！"},
                {"role": "assistant", "content": "早上好呀！今天感觉怎么样？"},
            ],
        }

        record = {
            "test_name": "test_tier3_with_memory_context",
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "context": context,
        }

        logger.info(f"用户输入: {user_input}")
        logger.info(f"记忆上下文: {json.dumps(context['memory_context'], ensure_ascii=False)}")

        start_time = datetime.now()
        response = await handlers.handle_with_fallback(
            request=request,
            classification=classification,
            context=context,
        )
        latency_ms = (datetime.now() - start_time).total_seconds() * 1000

        record["response"] = {
            "success": response.success,
            "text": response.text,
            "tier_used": response.tier_used.name if response.tier_used else None,
        }
        record["latency_ms"] = latency_ms

        save_request_record(record)

        logger.info(f"响应: {response.text}")
        logger.info(f"延迟: {latency_ms:.2f}ms")

        assert response.success or response.fallback_used
        logger.info("✓ 带记忆上下文测试完成")


class TestTier3FallbackChain:
    """
    Tier3 降级链测试
    Tier3 Fallback Chain Tests
    """

    @pytest.mark.asyncio
    async def test_tier3_fallback_to_tier2(self) -> None:
        """
        测试 Tier3 降级到 Tier2
        Test Tier3 fallback to Tier2
        """
        logger.info("=" * 60)
        logger.info("集成测试: Tier3 降级到 Tier2")
        logger.info("Integration Test: Tier3 Fallback to Tier2")
        logger.info("=" * 60)

        from rainze.agent import (
            SceneClassifier,
            Tier3LLMHandler,
            TierHandlerRegistry,
        )
        from rainze.core.contracts import (
            InteractionRequest,
            InteractionSource,
            ResponseTier,
        )

        # 创建一个会失败的 Tier3 处理器（使用无效配置）
        # Create a Tier3 handler that will fail (using invalid config)
        tier3_handler = Tier3LLMHandler(
            timeout_ms=100,  # 非常短的超时
            api_config_path="./nonexistent/config.json",  # 无效路径
        )

        # 创建注册表并替换 Tier3 / Create registry and replace Tier3
        registry = TierHandlerRegistry()
        registry._handlers[ResponseTier.TIER3_LLM] = tier3_handler

        classifier = SceneClassifier()

        user_input = "这是一个会触发降级的测试"
        request = InteractionRequest.create(
            source=InteractionSource.CHAT_INPUT,
            payload={"text": user_input},
        )

        classification = classifier.classify(
            source=request.source,
            user_input=user_input,
        )

        record = {
            "test_name": "test_tier3_fallback_to_tier2",
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "expected": "fallback to lower tier",
        }

        logger.info(f"用户输入: {user_input}")
        logger.info("预期: Tier3 失败后降级到 Tier2 或 Tier1")

        response = await registry.handle_with_fallback(
            request=request,
            classification=classification,
            context={},
        )

        record["response"] = {
            "success": response.success,
            "text": response.text,
            "tier_used": response.tier_used.name if response.tier_used else None,
            "fallback_used": response.fallback_used,
        }

        save_request_record(record)

        logger.info(f"响应: {response.text}")
        logger.info(f"使用的 Tier: {response.tier_used.name if response.tier_used else 'N/A'}")
        logger.info(f"降级使用: {response.fallback_used}")

        # 验证响应成功（可能是通过降级）/ Verify success (possibly via fallback)
        assert response.text is not None
        logger.info("✓ 降级链测试完成")


@pytest.fixture(scope="session", autouse=True)
def cleanup_logs():
    """测试完成后输出日志位置"""
    yield
    logger.info("=" * 60)
    logger.info("Tier3 测试完成！日志文件位置:")
    logger.info(f"  详细日志: {LOG_FILE}")
    logger.info(f"  请求记录: {REQUEST_LOG_FILE}")
    logger.info("=" * 60)
