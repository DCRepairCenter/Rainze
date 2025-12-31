"""
EmotionTag 三层降级场景测试
EmotionTag Three-Layer Fallback Scenario Tests

分别测试三种情感推断场景：
1. LLM 标签解析成功
2. SnowNLP 情感分析降级
3. 规则推断降级

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# 日志配置
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

RUN_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"emotion_fallback_test_{RUN_TIMESTAMP}.log"
RESULT_FILE = LOG_DIR / f"emotion_fallback_results_{RUN_TIMESTAMP}.json"

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
RESULTS: list[Dict[str, Any]] = []


def save_results() -> None:
    """保存测试结果"""
    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(RESULTS, f, ensure_ascii=False, indent=2, default=str)


async def test_scenario_1_llm_tag_parsing() -> Dict[str, Any]:
    """
    场景 1: LLM 标签解析成功
    Scenario 1: LLM tag parsing success
    
    测试 LLM 输出包含 [EMOTION:tag:intensity] 标签时的解析
    """
    logger.info("=" * 70)
    logger.info("场景 1: LLM 标签解析成功")
    logger.info("Scenario 1: LLM Tag Parsing Success")
    logger.info("=" * 70)
    
    from rainze.ai.emotion_inferrer import EmotionInferrer
    
    # 创建推断器（启用所有降级）
    inferrer = EmotionInferrer(enable_snownlp=True, enable_rule_fallback=True)
    
    # 模拟 LLM 输出（包含情感标签）
    test_cases = [
        "今天天气真好呢~ [EMOTION:happy:0.8]",
        "哎呀，你看起来有点累... [EMOTION:anxious:0.5]",
        "什么！真的吗？ [EMOTION:surprised:0.9]",
        "人家害羞啦~ [EMOTION:shy:0.6]",
        "嗯，好的 [EMOTION:neutral:0.4]",
    ]
    
    results = []
    for text in test_cases:
        clean_text, emotion = inferrer.infer(text)
        result = {
            "input": text,
            "clean_text": clean_text,
            "emotion_tag": emotion.tag,
            "emotion_intensity": emotion.intensity,
            "method": "LLM_TAG_PARSING",
        }
        results.append(result)
        logger.info(f"  输入: {text}")
        logger.info(f"  输出: text='{clean_text}', emotion={emotion.tag}:{emotion.intensity}")
        logger.info("")
    
    scenario_result = {
        "scenario": "1_LLM_TAG_PARSING",
        "description": "LLM 输出包含 [EMOTION:tag:intensity] 标签",
        "timestamp": datetime.now().isoformat(),
        "results": results,
    }
    
    logger.info("✓ 场景 1 测试完成")
    return scenario_result


async def test_scenario_2_snownlp_fallback() -> Dict[str, Any]:
    """
    场景 2: SnowNLP 情感分析降级
    Scenario 2: SnowNLP sentiment analysis fallback
    
    测试 LLM 输出不包含标签时，使用 SnowNLP 进行情感分析
    """
    logger.info("=" * 70)
    logger.info("场景 2: SnowNLP 情感分析降级")
    logger.info("Scenario 2: SnowNLP Sentiment Analysis Fallback")
    logger.info("=" * 70)
    
    from rainze.ai.emotion_inferrer import EmotionInferrer
    
    # 创建推断器（启用 SnowNLP，禁用规则降级以隔离测试）
    inferrer = EmotionInferrer(enable_snownlp=True, enable_rule_fallback=False)
    
    if not inferrer._snownlp_available:
        logger.warning("SnowNLP 不可用，跳过此场景")
        return {
            "scenario": "2_SNOWNLP_FALLBACK",
            "description": "SnowNLP 不可用",
            "skipped": True,
        }
    
    # 模拟 LLM 输出（不包含情感标签，需要 SnowNLP 分析）
    test_cases = [
        ("这个产品非常棒，我特别喜欢！", "positive"),
        ("今天心情很好，阳光明媚", "positive"),
        ("服务态度太差了，很失望", "negative"),
        ("工作好累，想休息", "negative"),
        ("嗯，知道了", "neutral"),
        ("哇，太神奇了！", "surprise"),
    ]
    
    results = []
    for text, expected_sentiment in test_cases:
        clean_text, emotion = inferrer.infer(text)
        
        # 获取 SnowNLP 原始分数
        try:
            from snownlp import SnowNLP
            s = SnowNLP(text)
            raw_sentiment = s.sentiments
        except Exception:
            raw_sentiment = None
        
        result = {
            "input": text,
            "expected_sentiment": expected_sentiment,
            "snownlp_raw_score": raw_sentiment,
            "emotion_tag": emotion.tag,
            "emotion_intensity": emotion.intensity,
            "method": "SNOWNLP_FALLBACK",
        }
        results.append(result)
        
        logger.info(f"  输入: {text}")
        logger.info(f"  SnowNLP 原始分数: {raw_sentiment:.3f}" if raw_sentiment else "  SnowNLP: N/A")
        logger.info(f"  映射结果: {emotion.tag}:{emotion.intensity}")
        logger.info("")
    
    scenario_result = {
        "scenario": "2_SNOWNLP_FALLBACK",
        "description": "LLM 输出不包含标签，使用 SnowNLP 情感分析",
        "timestamp": datetime.now().isoformat(),
        "results": results,
    }
    
    logger.info("✓ 场景 2 测试完成")
    return scenario_result


async def test_scenario_3_rule_fallback() -> Dict[str, Any]:
    """
    场景 3: 规则推断降级
    Scenario 3: Rule-based inference fallback
    
    测试 LLM 和 SnowNLP 都不可用时，使用规则推断
    """
    logger.info("=" * 70)
    logger.info("场景 3: 规则推断降级")
    logger.info("Scenario 3: Rule-Based Inference Fallback")
    logger.info("=" * 70)
    
    from rainze.ai.emotion_inferrer import EmotionInferrer
    
    # 创建推断器（禁用 SnowNLP，仅使用规则）
    inferrer = EmotionInferrer(enable_snownlp=False, enable_rule_fallback=True)
    
    # 测试规则推断
    test_cases = [
        # 正面关键词
        ("太开心了！", "happy", "正面关键词 + 感叹号"),
        ("哈哈哈，真棒", "happy", "正面关键词"),
        ("谢谢你~", "happy", "正面关键词 + 波浪号"),
        
        # 负面关键词
        ("好难过啊...", "sad", "负面关键词 + 省略号"),
        ("太累了", "sad", "负面关键词"),
        ("有点担心", "sad", "负面关键词"),
        
        # 惊讶关键词
        ("哇！什么情况？", "surprised", "惊讶关键词"),
        ("天哪，不会吧", "surprised", "惊讶关键词"),
        
        # 害羞关键词
        ("人家不好意思嘛", "shy", "害羞关键词"),
        
        # 无关键词 → 默认
        ("嗯", "neutral", "无关键词"),
        ("好的", "neutral", "无关键词"),
    ]
    
    results = []
    for text, expected_tag, reason in test_cases:
        clean_text, emotion = inferrer.infer(text)
        
        match = emotion.tag == expected_tag
        result = {
            "input": text,
            "reason": reason,
            "expected_tag": expected_tag,
            "actual_tag": emotion.tag,
            "intensity": emotion.intensity,
            "match": match,
            "method": "RULE_FALLBACK",
        }
        results.append(result)
        
        status = "✓" if match else "✗"
        logger.info(f"  {status} '{text}'")
        logger.info(f"    原因: {reason}")
        logger.info(f"    期望: {expected_tag}, 实际: {emotion.tag}:{emotion.intensity}")
        logger.info("")
    
    # 统计
    total = len(results)
    passed = sum(1 for r in results if r["match"])
    
    scenario_result = {
        "scenario": "3_RULE_FALLBACK",
        "description": "SnowNLP 不可用，使用规则推断",
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "accuracy": f"{passed/total*100:.1f}%",
        },
    }
    
    logger.info(f"✓ 场景 3 测试完成: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    return scenario_result


async def test_scenario_4_full_tier3_integration() -> Dict[str, Any]:
    """
    场景 4: 完整 Tier3 集成测试
    Scenario 4: Full Tier3 Integration Test
    
    测试真实 LLM 调用场景下的情感推断
    """
    logger.info("=" * 70)
    logger.info("场景 4: 完整 Tier3 集成测试")
    logger.info("Scenario 4: Full Tier3 Integration Test")
    logger.info("=" * 70)
    
    from rainze.agent import SceneClassifier, TierHandlerRegistry
    from rainze.core.contracts import InteractionRequest, InteractionSource
    
    classifier = SceneClassifier()
    handlers = TierHandlerRegistry()
    
    # 测试用例
    test_cases = [
        "你好呀！今天心情怎么样？",
        "帮我想想晚饭吃什么",
        "今天加班好累...",
        "哇，你好聪明！",
    ]
    
    results = []
    for user_input in test_cases:
        logger.info(f"  用户输入: {user_input}")
        
        request = InteractionRequest.create(
            source=InteractionSource.CHAT_INPUT,
            payload={"text": user_input},
        )
        
        classification = classifier.classify(
            source=request.source,
            user_input=user_input,
        )
        
        start_time = datetime.now()
        response = await handlers.handle_with_fallback(
            request=request,
            classification=classification,
            context={"current_hour": datetime.now().hour},
        )
        latency_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        result = {
            "user_input": user_input,
            "response_text": response.text,
            "emotion_tag": response.emotion.tag if response.emotion else None,
            "emotion_intensity": response.emotion.intensity if response.emotion else None,
            "tier_used": response.tier_used.name if response.tier_used else None,
            "latency_ms": latency_ms,
            "fallback_used": response.fallback_used,
        }
        results.append(result)
        
        logger.info(f"  响应: {response.text}")
        if response.emotion:
            logger.info(f"  情感: {response.emotion.tag}:{response.emotion.intensity}")
        logger.info(f"  Tier: {response.tier_used.name if response.tier_used else 'N/A'}")
        logger.info(f"  延迟: {latency_ms:.0f}ms")
        logger.info("")
    
    scenario_result = {
        "scenario": "4_FULL_TIER3_INTEGRATION",
        "description": "完整 Tier3 LLM 调用 + 情感推断",
        "timestamp": datetime.now().isoformat(),
        "results": results,
    }
    
    logger.info("✓ 场景 4 测试完成")
    return scenario_result


async def main() -> None:
    """运行所有测试场景"""
    logger.info("=" * 70)
    logger.info("EmotionTag 三层降级场景测试")
    logger.info("EmotionTag Three-Layer Fallback Scenario Tests")
    logger.info("=" * 70)
    logger.info("")
    
    # 场景 1: LLM 标签解析
    result1 = await test_scenario_1_llm_tag_parsing()
    RESULTS.append(result1)
    logger.info("")
    
    # 场景 2: SnowNLP 降级
    result2 = await test_scenario_2_snownlp_fallback()
    RESULTS.append(result2)
    logger.info("")
    
    # 场景 3: 规则降级
    result3 = await test_scenario_3_rule_fallback()
    RESULTS.append(result3)
    logger.info("")
    
    # 场景 4: 完整 Tier3 集成
    result4 = await test_scenario_4_full_tier3_integration()
    RESULTS.append(result4)
    logger.info("")
    
    # 保存结果
    save_results()
    
    logger.info("=" * 70)
    logger.info("所有测试完成！")
    logger.info(f"日志文件: {LOG_FILE}")
    logger.info(f"结果文件: {RESULT_FILE}")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
