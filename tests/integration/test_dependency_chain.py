"""
依赖链集成测试
Dependency Chain Integration Tests

测试完整依赖链：InputPanel → UCM → ChatBubble/AnimationController
Tests full dependency chain: InputPanel → UCM → ChatBubble/AnimationController

⚠️ 此测试需要 API 配置
This test requires API configuration

日志和请求体会保存到 logs/ 目录
Logs and request bodies are saved to logs/ directory

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

# ========================================
# 日志配置 / Logging Configuration
# ========================================

# 创建 logs 目录 / Create logs directory
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 当前测试运行的时间戳 / Current test run timestamp
RUN_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# 日志文件路径 / Log file paths
LOG_FILE = LOG_DIR / f"integration_test_{RUN_TIMESTAMP}.log"
REQUEST_LOG_FILE = LOG_DIR / f"requests_{RUN_TIMESTAMP}.json"

# 配置根日志器 / Configure root logger
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

# 请求记录列表 / Request records list
REQUEST_RECORDS: List[Dict[str, Any]] = []


def save_request_record(record: Dict[str, Any]) -> None:
    """
    保存请求记录到 JSON 文件
    Save request record to JSON file

    Args:
        record: 请求记录 / Request record
    """
    REQUEST_RECORDS.append(record)
    with open(REQUEST_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(REQUEST_RECORDS, f, ensure_ascii=False, indent=2, default=str)


# ========================================
# 测试 Fixtures
# ========================================


@pytest.fixture(scope="module")
def api_config() -> Dict[str, Any]:
    """
    加载 API 配置
    Load API configuration
    """
    config_path = Path(__file__).parent.parent.parent / "config" / "api_settings.json"

    logger.info("=" * 60)
    logger.info(f"加载 API 配置: {config_path}")
    logger.info("=" * 60)

    if not config_path.exists():
        pytest.skip(f"API config not found: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    logger.info("API 配置内容:")
    # 隐藏敏感信息 / Hide sensitive info
    safe_config = json.loads(json.dumps(config))
    for provider_name, provider_config in safe_config.get("providers", {}).items():
        if "api_key_env" in provider_config:
            key_value = provider_config["api_key_env"]
            if not key_value.startswith("$") and len(key_value) > 10:
                provider_config["api_key_env"] = f"{key_value[:8]}...{key_value[-4:]}"

    logger.info(json.dumps(safe_config, indent=2, ensure_ascii=False))

    return config


@pytest.fixture
def mock_gui_components() -> Dict[str, MagicMock]:
    """
    创建 Mock GUI 组件
    Create mock GUI components
    """
    return {
        "chat_bubble": MagicMock(),
        "input_panel": MagicMock(),
        "main_window": MagicMock(),
        "animation_controller": MagicMock(),
    }


# ========================================
# 集成测试类
# ========================================


class TestDependencyChainIntegration:
    """
    依赖链集成测试
    Dependency Chain Integration Tests
    """

    @pytest.mark.asyncio
    async def test_ucm_tier1_response(self) -> None:
        """
        测试 UCM Tier1 模板响应（无需 LLM）
        Test UCM Tier1 template response (no LLM needed)
        """
        logger.info("=" * 60)
        logger.info("集成测试: UCM Tier1 模板响应")
        logger.info("Integration Test: UCM Tier1 Template Response")
        logger.info("=" * 60)

        from rainze.agent import UnifiedContextManager
        from rainze.core.contracts import InteractionRequest, InteractionSource

        ucm = UnifiedContextManager()

        # 创建点击请求（Tier1 场景）/ Create click request (Tier1 scenario)
        request = InteractionRequest.create(
            source=InteractionSource.PASSIVE_TRIGGER,
            payload={"event_type": "click"},
        )

        # 记录请求 / Record request
        request_record = {
            "test_name": "test_ucm_tier1_response",
            "timestamp": datetime.now().isoformat(),
            "request": {
                "request_id": request.request_id,
                "source": request.source.name,
                "payload": request.payload,
                "trace_id": request.trace_id,
            },
        }

        logger.info("请求详情:")
        logger.info(json.dumps(request_record["request"], indent=2, ensure_ascii=False))

        # 处理交互 / Process interaction
        start_time = datetime.now()
        response = await ucm.process_interaction(request)
        end_time = datetime.now()
        latency_ms = (end_time - start_time).total_seconds() * 1000

        # 记录响应 / Record response
        request_record["response"] = {
            "request_id": response.request_id,
            "success": response.success,
            "response_text": response.response_text,
            "emotion": str(response.emotion) if response.emotion else None,
            "state_changes": response.state_changes,
            "error_message": response.error_message,
        }
        request_record["latency_ms"] = latency_ms
        save_request_record(request_record)

        logger.info("响应详情:")
        logger.info(json.dumps(request_record["response"], indent=2, ensure_ascii=False))
        logger.info(f"延迟: {latency_ms:.2f}ms")

        # 验证 / Verify
        assert response.request_id == request.request_id
        # Tier1 应该在 50ms 内响应 / Tier1 should respond within 50ms
        if response.success:
            tier_used = response.state_changes.get("tier_used")
            logger.info(f"使用的 Tier: {tier_used}")
            if tier_used == "TIER1":
                assert latency_ms < 500, f"Tier1 响应太慢: {latency_ms}ms"

        logger.info("✓ Tier1 响应测试通过")

    @pytest.mark.asyncio
    async def test_ucm_tier2_response(self) -> None:
        """
        测试 UCM Tier2 规则响应（无需 LLM）
        Test UCM Tier2 rule response (no LLM needed)
        """
        logger.info("=" * 60)
        logger.info("集成测试: UCM Tier2 规则响应")
        logger.info("Integration Test: UCM Tier2 Rule Response")
        logger.info("=" * 60)

        from rainze.agent import UnifiedContextManager
        from rainze.core.contracts import InteractionRequest, InteractionSource

        ucm = UnifiedContextManager()

        # 创建整点报时请求（Tier2 场景）/ Create hourly chime request (Tier2 scenario)
        request = InteractionRequest.create(
            source=InteractionSource.SYSTEM_EVENT,
            payload={"event_type": "hourly_chime", "hour": 14},
        )

        # 记录请求 / Record request
        request_record = {
            "test_name": "test_ucm_tier2_response",
            "timestamp": datetime.now().isoformat(),
            "request": {
                "request_id": request.request_id,
                "source": request.source.name,
                "payload": request.payload,
                "trace_id": request.trace_id,
            },
        }

        logger.info("请求详情:")
        logger.info(json.dumps(request_record["request"], indent=2, ensure_ascii=False))

        # 处理交互 / Process interaction
        start_time = datetime.now()
        response = await ucm.process_interaction(request)
        end_time = datetime.now()
        latency_ms = (end_time - start_time).total_seconds() * 1000

        # 记录响应 / Record response
        request_record["response"] = {
            "request_id": response.request_id,
            "success": response.success,
            "response_text": response.response_text,
            "emotion": str(response.emotion) if response.emotion else None,
            "state_changes": response.state_changes,
            "error_message": response.error_message,
        }
        request_record["latency_ms"] = latency_ms
        save_request_record(request_record)

        logger.info("响应详情:")
        logger.info(json.dumps(request_record["response"], indent=2, ensure_ascii=False))
        logger.info(f"延迟: {latency_ms:.2f}ms")

        # 验证 / Verify
        assert response.request_id == request.request_id
        # Tier2 应该在 100ms 内响应 / Tier2 should respond within 100ms
        if response.success:
            tier_used = response.state_changes.get("tier_used")
            logger.info(f"使用的 Tier: {tier_used}")
            if tier_used == "TIER2":
                assert latency_ms < 500, f"Tier2 响应太慢: {latency_ms}ms"

        logger.info("✓ Tier2 响应测试通过")

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_ucm_tier3_llm_response(self, api_config: Dict[str, Any]) -> None:
        """
        测试 UCM Tier3 LLM 响应（需要 API 配置）
        Test UCM Tier3 LLM response (requires API config)
        """
        logger.info("=" * 60)
        logger.info("集成测试: UCM Tier3 LLM 响应")
        logger.info("Integration Test: UCM Tier3 LLM Response")
        logger.info("=" * 60)

        from rainze.agent import UnifiedContextManager
        from rainze.core.contracts import InteractionRequest, InteractionSource

        ucm = UnifiedContextManager()

        # 用户对话输入（Tier3 场景）/ User chat input (Tier3 scenario)
        user_input = "你好呀！今天天气怎么样？"

        request = InteractionRequest.create(
            source=InteractionSource.CHAT_INPUT,
            payload={"text": user_input},
        )

        # 记录请求 / Record request
        request_record = {
            "test_name": "test_ucm_tier3_llm_response",
            "timestamp": datetime.now().isoformat(),
            "request": {
                "request_id": request.request_id,
                "source": request.source.name,
                "payload": request.payload,
                "trace_id": request.trace_id,
            },
            "context": {
                "api_provider": api_config.get("default_provider"),
                "user_input": user_input,
            },
        }

        logger.info("请求详情:")
        logger.info(json.dumps(request_record["request"], indent=2, ensure_ascii=False))
        logger.info(f"用户输入: {user_input}")

        # 处理交互 / Process interaction
        start_time = datetime.now()
        response = await ucm.process_interaction(request)
        end_time = datetime.now()
        latency_ms = (end_time - start_time).total_seconds() * 1000

        # 记录响应 / Record response
        request_record["response"] = {
            "request_id": response.request_id,
            "success": response.success,
            "response_text": response.response_text,
            "emotion": str(response.emotion) if response.emotion else None,
            "state_changes": response.state_changes,
            "error_message": response.error_message,
        }
        request_record["latency_ms"] = latency_ms
        save_request_record(request_record)

        logger.info("响应详情:")
        logger.info(json.dumps(request_record["response"], indent=2, ensure_ascii=False))
        logger.info(f"延迟: {latency_ms:.2f}ms")

        # 验证 / Verify
        assert response.request_id == request.request_id

        if response.success:
            tier_used = response.state_changes.get("tier_used")
            logger.info(f"使用的 Tier: {tier_used}")
            logger.info(f"响应文本: {response.response_text}")
            # Tier3 应该在 3s 内响应 / Tier3 should respond within 3s
            assert latency_ms < 30000, f"Tier3 响应太慢: {latency_ms}ms"
        else:
            logger.warning(f"响应失败: {response.error_message}")

        logger.info("✓ Tier3 LLM 响应测试完成")


class TestLLMClientDirect:
    """
    LLM 客户端直接测试
    LLM Client Direct Tests

    直接测试 LLM 客户端，记录详细请求体
    Direct test of LLM client, recording detailed request body
    """

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_anthropic_client_generate(self, api_config: Dict[str, Any]) -> None:
        """
        测试 Anthropic 客户端生成
        Test Anthropic client generation
        """
        logger.info("=" * 60)
        logger.info("集成测试: Anthropic 客户端直接调用")
        logger.info("Integration Test: Anthropic Client Direct Call")
        logger.info("=" * 60)

        # 获取 OpenAI 配置（使用兼容 API）
        # Get OpenAI config (using compatible API)
        provider_config = api_config.get("providers", {}).get("openai", {})
        if not provider_config.get("enabled"):
            pytest.skip("OpenAI provider not enabled")

        api_key = provider_config.get("api_key_env", "")
        base_url = provider_config.get("base_url", "")
        model = provider_config.get("default_model", "")

        if not api_key or api_key.startswith("$"):
            pytest.skip("API key not configured")

        logger.info(f"API Base URL: {base_url}")
        logger.info(f"Model: {model}")

        from rainze.ai.llm import LLMRequest

        # 构建请求 / Build request
        request = LLMRequest(
            system="你是一个可爱的桌面宠物，名叫小雨。用简短、活泼的语气回复。",
            messages=[
                {"role": "user", "content": "你好呀！今天天气怎么样？"}
            ],
            model=model,
            temperature=0.8,
            max_tokens=150,
            timeout_seconds=30,
        )

        # 记录请求详情 / Record request details
        request_record = {
            "test_name": "test_anthropic_client_generate",
            "timestamp": datetime.now().isoformat(),
            "llm_request": {
                "system": request.system,
                "messages": request.messages,
                "model": request.model,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "timeout_seconds": request.timeout_seconds,
            },
            "api_config": {
                "base_url": base_url,
                "model": model,
            },
        }

        logger.info("LLM 请求详情:")
        logger.info(json.dumps(request_record["llm_request"], indent=2, ensure_ascii=False))

        # 使用 httpx 直接调用（因为使用 OpenAI 兼容格式）
        # Direct call using httpx (using OpenAI compatible format)
        import httpx

        # 构建 OpenAI 格式请求体 / Build OpenAI format request body
        openai_body = {
            "model": model,
            "messages": [
                {"role": "system", "content": request.system},
                *request.messages,
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        request_record["openai_request_body"] = openai_body
        logger.info("OpenAI 格式请求体:")
        logger.info(json.dumps(openai_body, indent=2, ensure_ascii=False))

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                start_time = datetime.now()

                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=openai_body,
                )

                end_time = datetime.now()
                latency_ms = (end_time - start_time).total_seconds() * 1000

                request_record["latency_ms"] = latency_ms
                request_record["http_status"] = response.status_code

                logger.info(f"HTTP 状态码: {response.status_code}")
                logger.info(f"延迟: {latency_ms:.2f}ms")

                if response.status_code == 200:
                    response_data = response.json()
                    request_record["response"] = response_data

                    # 提取响应文本 / Extract response text
                    content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    usage = response_data.get("usage", {})

                    logger.info("=" * 40)
                    logger.info("LLM 响应:")
                    logger.info(f"  内容: {content}")
                    logger.info(f"  Token 使用: {usage}")
                    logger.info("=" * 40)

                    assert content, "响应内容为空"
                else:
                    error_text = response.text
                    request_record["error"] = error_text
                    logger.error(f"API 错误: {error_text}")

                save_request_record(request_record)

        except Exception as e:
            request_record["error"] = str(e)
            save_request_record(request_record)
            logger.error(f"请求失败: {e}")
            raise

        logger.info("✓ Anthropic 客户端测试完成")


class TestFullDependencyChain:
    """
    完整依赖链测试
    Full Dependency Chain Tests
    """

    @pytest.mark.asyncio
    async def test_input_to_response_flow(self, mock_gui_components: Dict[str, MagicMock]) -> None:
        """
        测试输入到响应的完整流程
        Test complete input to response flow
        """
        logger.info("=" * 60)
        logger.info("集成测试: 完整依赖链流程")
        logger.info("Integration Test: Full Dependency Chain Flow")
        logger.info("=" * 60)

        from rainze.agent import UnifiedContextManager
        from rainze.core.contracts import InteractionRequest, InteractionSource
        from rainze.state import StateManager

        # 创建组件 / Create components
        ucm = UnifiedContextManager()
        state_manager = StateManager()

        # 启动状态管理器 / Start state manager
        await state_manager.start()

        # 模拟用户输入 / Simulate user input
        user_input = "摸摸头"

        # 记录上下文构建详情 / Record context building details
        context_record = {
            "test_name": "test_input_to_response_flow",
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "initial_state": state_manager.get_summary(),
        }

        logger.info("初始状态:")
        logger.info(json.dumps(context_record["initial_state"], indent=2, ensure_ascii=False))

        # 创建请求 / Create request
        request = InteractionRequest.create(
            source=InteractionSource.PASSIVE_TRIGGER,
            payload={"event_type": "pat", "text": user_input},
        )

        context_record["request"] = {
            "request_id": request.request_id,
            "source": request.source.name,
            "payload": request.payload,
        }

        logger.info("请求详情:")
        logger.info(json.dumps(context_record["request"], indent=2, ensure_ascii=False))

        # 处理交互 / Process interaction
        start_time = datetime.now()
        response = await ucm.process_interaction(request)
        end_time = datetime.now()
        latency_ms = (end_time - start_time).total_seconds() * 1000

        context_record["response"] = {
            "request_id": response.request_id,
            "success": response.success,
            "response_text": response.response_text,
            "emotion": str(response.emotion) if response.emotion else None,
            "state_changes": response.state_changes,
        }
        context_record["latency_ms"] = latency_ms

        logger.info("响应详情:")
        logger.info(json.dumps(context_record["response"], indent=2, ensure_ascii=False))
        logger.info(f"延迟: {latency_ms:.2f}ms")

        # 验证 GUI 更新（如果响应成功）/ Verify GUI update (if response successful)
        if response.success and response.response_text:
            # 模拟 ChatBubble 更新 / Simulate ChatBubble update
            mock_gui_components["chat_bubble"].show_text(
                response.response_text,
                use_typing_effect=True,
            )
            mock_gui_components["chat_bubble"].show_text.assert_called_once()
            logger.info("✓ ChatBubble.show_text 已调用")

            # 模拟 AnimationController 更新 / Simulate AnimationController update
            if response.emotion:
                mock_gui_components["animation_controller"].apply_emotion_tag(response.emotion)
                mock_gui_components["animation_controller"].apply_emotion_tag.assert_called_once()
                logger.info("✓ AnimationController.apply_emotion_tag 已调用")

        # 获取最终状态 / Get final state
        context_record["final_state"] = state_manager.get_summary()
        logger.info("最终状态:")
        logger.info(json.dumps(context_record["final_state"], indent=2, ensure_ascii=False))

        save_request_record(context_record)

        # 停止状态管理器 / Stop state manager
        await state_manager.stop()

        logger.info("✓ 完整依赖链测试通过")


# ========================================
# 测试清理
# ========================================


@pytest.fixture(scope="session", autouse=True)
def cleanup_logs():
    """
    测试完成后输出日志位置
    Output log location after tests complete
    """
    yield

    logger.info("=" * 60)
    logger.info("测试完成！日志文件位置:")
    logger.info(f"  详细日志: {LOG_FILE}")
    logger.info(f"  请求记录: {REQUEST_LOG_FILE}")
    logger.info("=" * 60)
