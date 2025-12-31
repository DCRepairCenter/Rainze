"""
场景分类器
Scene Classifier

本模块负责将用户交互分类到不同场景类型，决定使用哪个 Tier 响应。
This module classifies user interactions into scene types to decide which Tier to use.

设计原则 / Design Principles:
- 无 API 调用: 纯规则匹配，保证低延迟
  No API calls: Pure rule matching for low latency
- 配置驱动: 场景-Tier 映射从 config/scene_tier_mapping.json 加载
  Config-driven: Scene-Tier mapping loaded from config

Reference:
    - PRD §0.3: 混合响应策略
    - MOD-Agent.md §3.4: SceneClassifier

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# ⭐ 从 core.contracts 导入共享类型，禁止重复定义
# Import shared types from core.contracts, NO duplicates allowed
from rainze.core.contracts import (
    InteractionSource,
    ResponseTier,
    SceneTierMapping,
    SceneType,
    get_scene_tier_table,
)


@dataclass
class ClassificationRule:
    """
    分类规则定义
    Classification rule definition

    Attributes:
        name: 规则名称 / Rule name
        conditions: 条件列表（AND关系）/ Condition list (AND relation)
        result_scene_id: 匹配后的场景ID / Scene ID when matched
        priority: 规则优先级，数值越大优先级越高 / Rule priority, higher = more priority
    """

    name: str
    conditions: List[str]
    result_scene_id: str
    priority: int = 0


@dataclass
class ClassificationResult:
    """
    分类结果
    Classification result

    Attributes:
        scene_id: 场景 ID / Scene ID
        scene_type: 场景类型 / Scene type
        mapping: 完整的场景配置 / Full scene configuration
        confidence: 分类置信度 / Classification confidence
        matched_rule: 匹配的规则名（如有）/ Matched rule name (if any)
    """

    scene_id: str
    scene_type: SceneType
    mapping: SceneTierMapping
    confidence: float = 1.0
    matched_rule: Optional[str] = None


class SceneClassifier:
    """
    场景分类器
    Scene Classifier

    在调用 LLM 前先判断场景复杂度，决定使用哪个 Tier 响应。
    Determine scene complexity before LLM call to decide response tier.

    分类规则（无 API 调用）/ Classification rules (no API calls):
    - SIMPLE: 高频简单交互（点击、拖拽、确认）
      High-frequency simple interactions (click, drag, confirm)
    - MEDIUM: 状态驱动事件（整点报时、系统警告）
      State-driven events (hourly chime, system warning)
    - COMPLEX: 需要上下文理解（自由对话、情感分析）
      Requires context understanding (free conversation, emotion analysis)

    Attributes:
        _tier_table: 场景-Tier 映射表 / Scene-Tier mapping table
        _custom_rules: 自定义分类规则 / Custom classification rules
        _simple_event_types: 简单事件类型集合 / Simple event types set
        _medium_event_types: 中等事件类型集合 / Medium event types set
        _complex_keywords: 复杂场景关键词 / Complex scene keywords
    """

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """
        初始化场景分类器，加载配置
        Initialize scene classifier, load configuration

        Args:
            config_path: 配置文件路径，默认使用 config/scene_tier_mapping.json
                         Config file path, defaults to config/scene_tier_mapping.json
        """
        # 加载场景-Tier 映射表 / Load scene-tier mapping table
        self._tier_table = get_scene_tier_table(config_path)

        # 自定义分类规则（按优先级排序）/ Custom rules (sorted by priority)
        self._custom_rules: List[ClassificationRule] = []

        # 简单事件类型 -> 直接判定为 SIMPLE
        # Simple event types -> directly classified as SIMPLE
        self._simple_event_types: Set[str] = {
            "click",
            "drag",
            "hover",
            "release",
            "double_click",
        }

        # 中等事件类型 -> 判定为 MEDIUM
        # Medium event types -> classified as MEDIUM
        self._medium_event_types: Set[str] = {
            "hourly_chime",
            "system_warning",
            "weather_update",
            "focus_warning",
            "focus_complete",
            "feed_response",
            "proactive_greeting",
            "tool_execution",
        }

        # 复杂场景关键词（触发 COMPLEX）
        # Complex scene keywords (triggers COMPLEX)
        self._complex_keywords: Set[str] = {
            "为什么",
            "怎么",
            "帮我",
            "记得",
            "之前",
            "上次",
            "你觉得",
            "你认为",
            "建议",
            "推荐",
            "聊聊",
            "想",
            "感觉",
        }

        # 编译复杂关键词正则表达式 / Compile complex keywords regex
        self._complex_pattern: re.Pattern[str] = re.compile(
            "|".join(re.escape(kw) for kw in self._complex_keywords)
        )

    def classify(
        self,
        source: InteractionSource,
        event_type: Optional[str] = None,
        user_input: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ClassificationResult:
        """
        分类场景复杂度
        Classify scene complexity

        Args:
            source: 交互来源 / Interaction source
            event_type: 事件类型（如 "click", "hourly_chime"）/ Event type
            user_input: 用户输入文本 / User input text
            context: 额外上下文信息 / Additional context

        Returns:
            ClassificationResult: 分类结果，包含场景类型和配置
                                  Classification result with scene type and config

        Example:
            >>> classifier.classify(InteractionSource.PASSIVE_TRIGGER, event_type="click")
            ClassificationResult(scene_id="click", scene_type=SceneType.SIMPLE, ...)

            >>> classifier.classify(
            ...     InteractionSource.CHAT_INPUT,
            ...     user_input="你觉得我今天穿什么好？"
            ... )
            ClassificationResult(scene_id="conversation", scene_type=SceneType.COMPLEX, ...)
        """
        context = context or {}

        # 1. 首先检查自定义规则 / First check custom rules
        custom_result = self._match_custom_rules(source, event_type, user_input, context)
        if custom_result:
            return custom_result

        # 2. 检查简单场景 / Check simple scenes
        if self._is_simple_scene(source, event_type, user_input):
            scene_id = event_type or "click"
            return self._build_result(scene_id, SceneType.SIMPLE, "simple_rule")

        # 3. 检查中等场景 / Check medium scenes
        if self._is_medium_scene(source, event_type, context):
            scene_id = event_type or "system_event"
            return self._build_result(scene_id, SceneType.MEDIUM, "medium_rule")

        # 4. 默认为复杂场景（对话）/ Default to complex scene (conversation)
        return self._build_result("conversation", SceneType.COMPLEX, "default_complex")

    def _is_simple_scene(
        self,
        source: InteractionSource,
        event_type: Optional[str],
        user_input: Optional[str],
    ) -> bool:
        """
        检查是否为简单场景
        Check if it's a simple scene

        条件（OR 关系）/ Conditions (OR relation):
        - source 是 PASSIVE_TRIGGER / source is PASSIVE_TRIGGER
        - event_type 在简单事件集合中 / event_type in simple event set

        ⚠️ CHAT_INPUT 永远不是简单场景，即使输入很短！
        CHAT_INPUT is NEVER simple, even with short input!

        Args:
            source: 交互来源 / Interaction source
            event_type: 事件类型 / Event type
            user_input: 用户输入 / User input

        Returns:
            是否为简单场景 / Whether it's a simple scene
        """
        # ⭐ CHAT_INPUT 来源永远不是简单场景，应该触发对话
        # CHAT_INPUT source is NEVER simple, should trigger conversation
        if source == InteractionSource.CHAT_INPUT:
            return False

        # 被动触发 -> 简单 / Passive trigger -> simple
        if source == InteractionSource.PASSIVE_TRIGGER:
            return True

        # 游戏交互 -> 简单 / Game interaction -> simple
        if source == InteractionSource.GAME_INTERACTION:
            return True

        # 事件类型在简单集合中 / Event type in simple set
        if event_type and event_type.lower() in self._simple_event_types:
            return True

        return False

    def _is_medium_scene(
        self,
        source: InteractionSource,
        event_type: Optional[str],
        context: Dict[str, Any],
    ) -> bool:
        """
        检查是否为中等场景
        Check if it's a medium scene

        条件（OR 关系）/ Conditions (OR relation):
        - event_type 在中等事件集合中 / event_type in medium event set
        - source 是 SYSTEM_EVENT / source is SYSTEM_EVENT
        - source 是 TOOL_RESULT / source is TOOL_RESULT
        - context 中 has_clear_trigger 为 true / has_clear_trigger in context

        Args:
            source: 交互来源 / Interaction source
            event_type: 事件类型 / Event type
            context: 上下文信息 / Context

        Returns:
            是否为中等场景 / Whether it's a medium scene
        """
        # 系统事件 / System event
        if source == InteractionSource.SYSTEM_EVENT:
            return True

        # 工具执行结果 / Tool result
        if source == InteractionSource.TOOL_RESULT:
            return True

        # 主动行为 / Proactive behavior
        if source == InteractionSource.PROACTIVE:
            return True

        # 事件类型在中等集合中 / Event type in medium set
        if event_type and event_type.lower() in self._medium_event_types:
            return True

        # 上下文标记有明确触发器 / Context has clear trigger
        if context.get("has_clear_trigger"):
            return True

        return False

    def _contains_complex_keyword(self, text: str) -> bool:
        """
        检查文本是否包含复杂场景关键词
        Check if text contains complex scene keywords

        Args:
            text: 待检查文本 / Text to check

        Returns:
            是否包含复杂关键词 / Whether contains complex keywords
        """
        return bool(self._complex_pattern.search(text))

    def _match_custom_rules(
        self,
        source: InteractionSource,
        event_type: Optional[str],
        user_input: Optional[str],
        context: Dict[str, Any],
    ) -> Optional[ClassificationResult]:
        """
        匹配自定义规则
        Match custom rules

        Args:
            source: 交互来源 / Interaction source
            event_type: 事件类型 / Event type
            user_input: 用户输入 / User input
            context: 上下文 / Context

        Returns:
            匹配结果，无匹配返回 None / Match result, None if no match
        """
        # 按优先级排序检查规则 / Check rules sorted by priority
        sorted_rules = sorted(self._custom_rules, key=lambda r: -r.priority)

        for rule in sorted_rules:
            if self._evaluate_rule(rule, source, event_type, user_input, context):
                # 根据 scene_id 确定 scene_type / Determine scene_type from scene_id
                if rule.result_scene_id in self._tier_table:
                    mapping = self._tier_table[rule.result_scene_id]
                    return ClassificationResult(
                        scene_id=rule.result_scene_id,
                        scene_type=mapping.scene_type,
                        mapping=mapping,
                        confidence=1.0,
                        matched_rule=rule.name,
                    )

        return None

    def _evaluate_rule(
        self,
        rule: ClassificationRule,
        source: InteractionSource,
        event_type: Optional[str],
        user_input: Optional[str],
        context: Dict[str, Any],
    ) -> bool:
        """
        评估单个规则是否匹配
        Evaluate if a single rule matches

        规则条件支持格式 / Rule condition formats:
        - "source == CHAT_INPUT"
        - "event_type == click"
        - "user_input contains 帮我"
        - "context.key == value"

        Args:
            rule: 要评估的规则 / Rule to evaluate
            source: 交互来源 / Interaction source
            event_type: 事件类型 / Event type
            user_input: 用户输入 / User input
            context: 上下文 / Context

        Returns:
            是否所有条件都满足 / Whether all conditions are met
        """
        # 条件之间是 AND 关系 / Conditions are AND relation
        for condition in rule.conditions:
            if not self._evaluate_condition(
                condition, source, event_type, user_input, context
            ):
                return False
        return True

    def _evaluate_condition(
        self,
        condition: str,
        source: InteractionSource,
        event_type: Optional[str],
        user_input: Optional[str],
        context: Dict[str, Any],
    ) -> bool:
        """
        评估单个条件
        Evaluate a single condition

        Args:
            condition: 条件字符串 / Condition string
            source: 交互来源 / Interaction source
            event_type: 事件类型 / Event type
            user_input: 用户输入 / User input
            context: 上下文 / Context

        Returns:
            条件是否满足 / Whether condition is met
        """
        # 简单条件解析 / Simple condition parsing
        if "==" in condition:
            left, right = [s.strip() for s in condition.split("==", 1)]

            if left == "source":
                try:
                    expected = InteractionSource[right]
                    return source == expected
                except KeyError:
                    return False

            if left == "event_type":
                return event_type == right

            if left.startswith("context."):
                key = left[8:]
                return context.get(key) == right

        elif "contains" in condition:
            left, right = [s.strip() for s in condition.split("contains", 1)]

            if left == "user_input" and user_input:
                return right in user_input

        return False

    def _build_result(
        self,
        scene_id: str,
        scene_type: SceneType,
        matched_rule: str,
    ) -> ClassificationResult:
        """
        构建分类结果
        Build classification result

        Args:
            scene_id: 场景 ID / Scene ID
            scene_type: 场景类型 / Scene type
            matched_rule: 匹配的规则 / Matched rule

        Returns:
            分类结果 / Classification result
        """
        # 从映射表获取配置，不存在则使用默认
        # Get config from mapping table, use default if not exists
        if scene_id in self._tier_table:
            mapping = self._tier_table[scene_id]
        else:
            # 根据 scene_type 创建默认映射
            # Create default mapping based on scene_type
            mapping = self._get_default_mapping(scene_type)

        return ClassificationResult(
            scene_id=scene_id,
            scene_type=scene_type,
            mapping=mapping,
            confidence=1.0,
            matched_rule=matched_rule,
        )

    def _get_default_mapping(self, scene_type: SceneType) -> SceneTierMapping:
        """
        获取默认场景映射
        Get default scene mapping

        Args:
            scene_type: 场景类型 / Scene type

        Returns:
            默认的场景映射配置 / Default scene mapping config
        """
        if scene_type == SceneType.SIMPLE:
            return SceneTierMapping(
                scene_type=scene_type,
                default_tier=ResponseTier.TIER1_TEMPLATE,
                timeout_ms=50,
                memory_retrieval="none",
                fallback_chain=[],
            )
        elif scene_type == SceneType.MEDIUM:
            return SceneTierMapping(
                scene_type=scene_type,
                default_tier=ResponseTier.TIER2_RULE,
                timeout_ms=100,
                memory_retrieval="facts_summary",
                fallback_chain=[ResponseTier.TIER1_TEMPLATE],
            )
        else:  # COMPLEX
            return SceneTierMapping(
                scene_type=scene_type,
                default_tier=ResponseTier.TIER3_LLM,
                timeout_ms=3000,
                memory_retrieval="full",
                fallback_chain=[ResponseTier.TIER2_RULE, ResponseTier.TIER1_TEMPLATE],
            )

    def add_rule(self, rule: ClassificationRule) -> None:
        """
        添加自定义分类规则
        Add custom classification rule

        Args:
            rule: 分类规则 / Classification rule
        """
        self._custom_rules.append(rule)

    def remove_rule(self, name: str) -> bool:
        """
        移除分类规则
        Remove classification rule

        Args:
            name: 规则名称 / Rule name

        Returns:
            是否成功移除 / Whether successfully removed
        """
        for i, rule in enumerate(self._custom_rules):
            if rule.name == name:
                self._custom_rules.pop(i)
                return True
        return False

    def add_simple_event_type(self, event_type: str) -> None:
        """
        添加简单事件类型
        Add simple event type

        Args:
            event_type: 事件类型 / Event type
        """
        self._simple_event_types.add(event_type.lower())

    def add_medium_event_type(self, event_type: str) -> None:
        """
        添加中等事件类型
        Add medium event type

        Args:
            event_type: 事件类型 / Event type
        """
        self._medium_event_types.add(event_type.lower())

    def add_complex_keyword(self, keyword: str) -> None:
        """
        添加复杂场景关键词
        Add complex scene keyword

        Args:
            keyword: 关键词 / Keyword
        """
        self._complex_keywords.add(keyword)
        # 重新编译正则 / Recompile regex
        self._complex_pattern = re.compile(
            "|".join(re.escape(kw) for kw in self._complex_keywords)
        )
