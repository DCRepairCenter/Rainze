"""
响应生成策略
Response Generation Strategy

本模块定义响应生成的核心数据结构和协调器。
This module defines core data structures and coordinator for response generation.

Reference:
    - PRD §0.3: 混合响应策略
    - MOD-AI.md §3.4: ResponseGenerator

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, Optional

from rainze.ai.exceptions import GenerationError

# ⭐ 从 core.contracts 导入统一类型，禁止本模块重复定义
# Import unified types from core.contracts, NO duplicates allowed
from rainze.core.contracts import EmotionTag, ResponseTier

if TYPE_CHECKING:
    from rainze.ai.generation.tier1_template import Tier1TemplateGenerator
    from rainze.ai.generation.tier2_rule import Tier2RuleGenerator
    from rainze.ai.generation.tier3_llm import Tier3LLMGenerator


@dataclass
class GeneratedResponse:
    """
    生成的响应数据结构
    Generated Response Data Structure

    封装响应生成结果，包括文本、情感和元数据。
    Encapsulates response generation result including text, emotion, and metadata.

    Attributes:
        text: 响应文本 / Response text
        emotion_tag: 情感标签 / Emotion tag (from core.contracts)
        action_hint: 动作提示 / Action hint
        tier_used: 实际使用的响应层级 / Actual response tier used
        latency_ms: 响应延迟（毫秒）/ Response latency in ms
        from_cache: 是否来自缓存 / Whether from cache
        metadata: 额外元数据 / Additional metadata
    """

    text: str
    emotion_tag: Optional[EmotionTag] = None
    action_hint: Optional[str] = None
    tier_used: ResponseTier = ResponseTier.TIER3_LLM
    latency_ms: float = 0.0
    from_cache: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        验证响应数据
        Validate response data
        """
        # 确保文本不为空 / Ensure text is not empty
        if not self.text:
            self.text = ""

    @classmethod
    def create_empty(
        cls, tier: ResponseTier = ResponseTier.TIER1_TEMPLATE
    ) -> "GeneratedResponse":
        """
        创建空响应（用于错误情况）
        Create empty response (for error cases)

        Args:
            tier: 响应层级 / Response tier

        Returns:
            空响应 / Empty response
        """
        return cls(
            text="",
            tier_used=tier,
            metadata={"error": True},
        )


# 场景类型到响应层级的默认映射 / Default mapping from scene type to response tier
_SCENE_TIER_MAPPING: Dict[str, ResponseTier] = {
    # Tier1 场景 / Tier1 scenes
    "click": ResponseTier.TIER1_TEMPLATE,
    "drag": ResponseTier.TIER1_TEMPLATE,
    "double_click": ResponseTier.TIER1_TEMPLATE,
    "hover": ResponseTier.TIER1_TEMPLATE,
    "game_interaction": ResponseTier.TIER1_TEMPLATE,
    # Tier2 场景 / Tier2 scenes
    "hourly_chime": ResponseTier.TIER2_RULE,
    "system_warning": ResponseTier.TIER2_RULE,
    "low_battery": ResponseTier.TIER2_RULE,
    "high_cpu": ResponseTier.TIER2_RULE,
    "daily_greeting": ResponseTier.TIER2_RULE,
    # Tier3 场景 / Tier3 scenes
    "conversation": ResponseTier.TIER3_LLM,
    "emotional_support": ResponseTier.TIER3_LLM,
    "complex_query": ResponseTier.TIER3_LLM,
    "story_telling": ResponseTier.TIER3_LLM,
}


class ResponseGenerator:
    """
    响应生成协调器
    Response Generation Coordinator

    统一管理 3 个 Tier 的响应生成策略。
    Manages all 3 tiers of response generation strategies.

    Attributes:
        _tier1: Tier1 模板生成器 / Tier1 template generator
        _tier2: Tier2 规则生成器 / Tier2 rule generator
        _tier3: Tier3 LLM 生成器 / Tier3 LLM generator

    Example:
        >>> generator = ResponseGenerator(tier1, tier2, tier3)
        >>> response = await generator.generate(
        ...     scene_type="conversation",
        ...     scene_context={"topic": "weather"},
        ...     user_input="今天天气怎么样？"
        ... )
        >>> print(response.text)
    """

    def __init__(
        self,
        tier1: "Tier1TemplateGenerator",
        tier2: "Tier2RuleGenerator",
        tier3: "Tier3LLMGenerator",
    ) -> None:
        """
        初始化响应生成器
        Initialize response generator

        Args:
            tier1: Tier1 模板生成器 / Tier1 template generator
            tier2: Tier2 规则生成器 / Tier2 rule generator
            tier3: Tier3 LLM 生成器 / Tier3 LLM generator
        """
        self._tier1 = tier1
        self._tier2 = tier2
        self._tier3 = tier3

    async def generate(
        self,
        scene_type: str,
        scene_context: Dict[str, Any],
        forced_tier: Optional[ResponseTier] = None,
        user_input: Optional[str] = None,
    ) -> GeneratedResponse:
        """
        生成响应
        Generate response

        根据场景类型自动选择响应层级，或使用强制指定的层级。
        Auto-select response tier based on scene type, or use forced tier.

        Args:
            scene_type: 场景类型（如 "click", "conversation"）/ Scene type
            scene_context: 场景上下文 / Scene context
            forced_tier: 强制使用指定层级 / Force specific tier
            user_input: 用户输入（Tier3 需要）/ User input (required for Tier3)

        Returns:
            生成的响应 / Generated response

        Raises:
            GenerationError: 生成失败 / Generation failed
        """
        start_time = time.perf_counter()

        # 确定使用的层级 / Determine tier to use
        tier = forced_tier or self._determine_tier(scene_type)

        try:
            response: GeneratedResponse

            if tier == ResponseTier.TIER1_TEMPLATE:
                response = await self._tier1.generate(scene_type, scene_context)
            elif tier == ResponseTier.TIER2_RULE:
                response = await self._tier2.generate(scene_type, scene_context)
            else:  # TIER3_LLM
                response = await self._tier3.generate(
                    scene_type, scene_context, user_input
                )

            # 更新延迟 / Update latency
            response.latency_ms = (time.perf_counter() - start_time) * 1000

            return response

        except Exception as e:
            # 记录错误并尝试降级 / Log error and try fallback
            latency_ms = (time.perf_counter() - start_time) * 1000

            # 尝试降级 / Try fallback
            fallback_response = await self._try_fallback(
                tier, scene_type, scene_context, e
            )
            if fallback_response is not None:
                fallback_response.latency_ms = latency_ms
                return fallback_response

            # 所有降级都失败 / All fallbacks failed
            raise GenerationError(
                f"Failed to generate response for scene '{scene_type}' / "
                f"无法为场景 '{scene_type}' 生成响应",
                tier=tier.name,
            ) from e

    def _determine_tier(self, scene_type: str) -> ResponseTier:
        """
        根据场景类型确定响应层级
        Determine response tier based on scene type

        Args:
            scene_type: 场景类型 / Scene type

        Returns:
            响应层级 / Response tier
        """
        return _SCENE_TIER_MAPPING.get(scene_type, ResponseTier.TIER3_LLM)

    async def _try_fallback(
        self,
        failed_tier: ResponseTier,
        scene_type: str,
        scene_context: Dict[str, Any],
        original_error: Exception,
    ) -> Optional[GeneratedResponse]:
        """
        尝试降级响应
        Try fallback response

        Args:
            failed_tier: 失败的层级 / Failed tier
            scene_type: 场景类型 / Scene type
            scene_context: 场景上下文 / Scene context
            original_error: 原始错误 / Original error

        Returns:
            降级响应，如果降级也失败则返回 None
            Fallback response, or None if fallback also fails
        """
        # 降级链: Tier3 -> Tier2 -> Tier1 / Fallback chain
        fallback_tiers: list[ResponseTier] = []

        if failed_tier == ResponseTier.TIER3_LLM:
            fallback_tiers = [ResponseTier.TIER2_RULE, ResponseTier.TIER1_TEMPLATE]
        elif failed_tier == ResponseTier.TIER2_RULE:
            fallback_tiers = [ResponseTier.TIER1_TEMPLATE]

        for tier in fallback_tiers:
            try:
                if tier == ResponseTier.TIER2_RULE:
                    response = await self._tier2.generate(scene_type, scene_context)
                else:  # TIER1_TEMPLATE
                    response = await self._tier1.generate(scene_type, scene_context)

                # 标记为降级响应 / Mark as fallback response
                response.metadata["fallback"] = True
                response.metadata["original_tier"] = failed_tier.name
                response.metadata["original_error"] = str(original_error)

                return response

            except Exception:
                # 继续尝试下一个降级 / Continue to next fallback
                continue

        return None
