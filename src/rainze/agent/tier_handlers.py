"""
响应层级处理器
Response Tier Handlers

本模块实现 3 层响应策略的处理器：
This module implements handlers for 3-tier response strategy:

- Tier1TemplateHandler: 模板响应 (<50ms) - 点击、拖拽
  Template response - click, drag
- Tier2RuleHandler: 规则生成 (<100ms) - 整点报时、系统警告
  Rule-based generation - hourly chime, system warning
- Tier3LLMHandler: LLM 生成 (<3s) - 对话、情感分析
  LLM generation - conversation, emotion analysis

Reference:
    - PRD §0.3: 混合响应策略
    - MOD-Agent.md §3.1: UnifiedContextManager

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import asyncio
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

# ⭐ 从 core.contracts 导入共享类型，禁止重复定义
# Import shared types from core.contracts, NO duplicates allowed
from rainze.core.contracts import (
    EmotionTag,
    InteractionRequest,
    ResponseTier,
)

if TYPE_CHECKING:
    from rainze.agent.scene_classifier import ClassificationResult


@dataclass
class TierResponse:
    """
    层级处理器响应
    Tier handler response

    Attributes:
        success: 是否成功 / Whether successful
        text: 响应文本 / Response text
        emotion: 情感标签 / Emotion tag
        tier_used: 实际使用的层级 / Actually used tier
        latency_ms: 响应延迟（毫秒）/ Response latency in ms
        fallback_used: 是否使用了降级 / Whether fallback was used
    """

    success: bool
    text: Optional[str] = None
    emotion: Optional[EmotionTag] = None
    tier_used: Optional[ResponseTier] = None
    latency_ms: int = 0
    fallback_used: bool = False


class BaseTierHandler(ABC):
    """
    层级处理器基类
    Base tier handler

    所有层级处理器必须继承此类并实现 handle 方法。
    All tier handlers must inherit this class and implement handle method.

    Attributes:
        tier: 处理器对应的层级 / Handler's tier
        timeout_ms: 超时时间（毫秒）/ Timeout in ms
    """

    tier: ResponseTier

    def __init__(self, timeout_ms: int = 3000) -> None:
        """
        初始化处理器
        Initialize handler

        Args:
            timeout_ms: 超时时间（毫秒）/ Timeout in ms
        """
        self._timeout_ms = timeout_ms

    @property
    def timeout_ms(self) -> int:
        """获取超时时间 / Get timeout"""
        return self._timeout_ms

    @abstractmethod
    async def handle(
        self,
        request: InteractionRequest,
        classification: "ClassificationResult",
        context: Optional[Dict[str, Any]] = None,
    ) -> TierResponse:
        """
        处理交互请求
        Handle interaction request

        Args:
            request: 交互请求 / Interaction request
            classification: 场景分类结果 / Scene classification result
            context: 额外上下文（如记忆检索结果）
                     Additional context (e.g., memory retrieval results)

        Returns:
            TierResponse: 处理响应 / Handler response
        """
        pass

    async def handle_with_timeout(
        self,
        request: InteractionRequest,
        classification: "ClassificationResult",
        context: Optional[Dict[str, Any]] = None,
    ) -> TierResponse:
        """
        带超时的处理方法
        Handle with timeout

        Args:
            request: 交互请求 / Interaction request
            classification: 场景分类结果 / Scene classification result
            context: 额外上下文 / Additional context

        Returns:
            TierResponse: 处理响应 / Handler response
        """
        start_time = datetime.now()
        try:
            timeout_seconds = self._timeout_ms / 1000.0
            response = await asyncio.wait_for(
                self.handle(request, classification, context),
                timeout=timeout_seconds,
            )
            # 计算延迟 / Calculate latency
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            response.latency_ms = latency_ms
            return response
        except asyncio.TimeoutError:
            # 超时返回失败响应 / Return failure on timeout
            return TierResponse(
                success=False,
                text=None,
                tier_used=self.tier,
                latency_ms=self._timeout_ms,
            )


class Tier1TemplateHandler(BaseTierHandler):
    """
    Tier1 模板响应处理器
    Tier1 Template Response Handler

    用于高频简单交互，直接从预设模板中选择响应。
    For high-frequency simple interactions, select response from templates.

    特点 / Features:
    - 响应时间 <50ms / Response time <50ms
    - 无 API 调用 / No API calls
    - 随机选择模板增加自然感 / Random template selection for naturalness
    """

    tier = ResponseTier.TIER1_TEMPLATE

    def __init__(self, timeout_ms: int = 50) -> None:
        """
        初始化 Tier1 处理器
        Initialize Tier1 handler

        Args:
            timeout_ms: 超时时间，默认 50ms / Timeout, default 50ms
        """
        super().__init__(timeout_ms)

        # 模板库：场景ID -> (文本模板列表, 情感标签)
        # Template library: scene_id -> (text templates, emotion tag)
        self._templates: Dict[str, tuple[list[str], EmotionTag]] = {
            "click": (
                ["嗯？", "有事吗~", "怎么啦？", "你戳我干嘛~", "嘿嘿"],
                EmotionTag(tag="happy", intensity=0.5),
            ),
            "drag": (
                [
                    "哇！别拖我！",
                    "要去哪里呀~",
                    "轻点轻点！",
                    "我晕了...",
                    "放开我！",
                ],
                EmotionTag(tag="surprised", intensity=0.6),
            ),
            "hover": (
                ["...？", "你在看我吗？", "嗯~"],
                EmotionTag(tag="neutral", intensity=0.3),
            ),
            "double_click": (
                ["双击！", "什么什么？", "有急事？"],
                EmotionTag(tag="excited", intensity=0.6),
            ),
            "game_interaction": (
                ["好的！", "来吧！", "准备好了！", "我要赢！"],
                EmotionTag(tag="excited", intensity=0.7),
            ),
        }

        # 默认模板 / Default templates
        self._default_templates: tuple[list[str], EmotionTag] = (
            ["嗯？", "怎么了？", "..."],
            EmotionTag(tag="neutral", intensity=0.4),
        )

    async def handle(
        self,
        request: InteractionRequest,
        classification: "ClassificationResult",
        context: Optional[Dict[str, Any]] = None,
    ) -> TierResponse:
        """
        从模板库选择响应
        Select response from template library

        Args:
            request: 交互请求 / Interaction request
            classification: 场景分类结果 / Scene classification result
            context: 额外上下文 / Additional context

        Returns:
            TierResponse: 模板响应 / Template response
        """
        scene_id = classification.scene_id

        # 获取对应模板 / Get corresponding templates
        if scene_id in self._templates:
            templates, emotion = self._templates[scene_id]
        else:
            templates, emotion = self._default_templates

        # 随机选择模板 / Randomly select template
        text = random.choice(templates)

        return TierResponse(
            success=True,
            text=text,
            emotion=emotion,
            tier_used=self.tier,
        )

    def add_template(
        self,
        scene_id: str,
        templates: List[str],
        emotion: Optional[EmotionTag] = None,
    ) -> None:
        """
        添加或更新模板
        Add or update templates

        Args:
            scene_id: 场景 ID / Scene ID
            templates: 文本模板列表 / Text template list
            emotion: 情感标签，默认 neutral / Emotion tag, defaults to neutral
        """
        if emotion is None:
            emotion = EmotionTag.default()
        self._templates[scene_id] = (templates, emotion)


class Tier2RuleHandler(BaseTierHandler):
    """
    Tier2 规则生成处理器
    Tier2 Rule-based Response Handler

    用于状态驱动事件，根据规则和上下文生成响应。
    For state-driven events, generate responses based on rules and context.

    特点 / Features:
    - 响应时间 <100ms / Response time <100ms
    - 无 LLM 调用，使用规则引擎 / No LLM calls, use rule engine
    - 支持简单的变量替换 / Support simple variable substitution
    """

    tier = ResponseTier.TIER2_RULE

    def __init__(self, timeout_ms: int = 100) -> None:
        """
        初始化 Tier2 处理器
        Initialize Tier2 handler

        Args:
            timeout_ms: 超时时间，默认 100ms / Timeout, default 100ms
        """
        super().__init__(timeout_ms)

        # 规则库：场景ID -> 规则生成函数
        # Rule library: scene_id -> rule generator function
        self._rules: Dict[str, Callable[[Dict[str, Any]], tuple[str, EmotionTag]]] = {
            "hourly_chime": self._rule_hourly_chime,
            "system_warning": self._rule_system_warning,
            "weather_update": self._rule_weather_update,
            "proactive_greeting": self._rule_proactive_greeting,
            "tool_execution": self._rule_tool_execution,
        }

    async def handle(
        self,
        request: InteractionRequest,
        classification: "ClassificationResult",
        context: Optional[Dict[str, Any]] = None,
    ) -> TierResponse:
        """
        根据规则生成响应
        Generate response based on rules

        Args:
            request: 交互请求 / Interaction request
            classification: 场景分类结果 / Scene classification result
            context: 额外上下文 / Additional context

        Returns:
            TierResponse: 规则生成的响应 / Rule-generated response
        """
        context = context or {}
        scene_id = classification.scene_id

        # 合并请求 payload 到上下文 / Merge request payload into context
        merged_context = {**context, **request.payload}

        # 获取规则函数 / Get rule function
        if scene_id in self._rules:
            text, emotion = self._rules[scene_id](merged_context)
        else:
            # 默认规则 / Default rule
            text, emotion = self._rule_default(merged_context)

        return TierResponse(
            success=True,
            text=text,
            emotion=emotion,
            tier_used=self.tier,
        )

    def _rule_hourly_chime(
        self, context: Dict[str, Any]
    ) -> tuple[str, EmotionTag]:
        """
        整点报时规则
        Hourly chime rule

        Args:
            context: 上下文信息 / Context info

        Returns:
            (响应文本, 情感标签) / (response text, emotion tag)
        """
        hour = context.get("hour", datetime.now().hour)

        # 根据时间段生成不同问候 / Generate different greetings by time period
        if 6 <= hour < 9:
            templates = [
                f"现在是早上 {hour} 点啦！今天也要元气满满哦~",
                f"早安！{hour} 点了，新的一天开始了！",
            ]
            emotion = EmotionTag(tag="happy", intensity=0.7)
        elif 9 <= hour < 12:
            templates = [
                f"上午 {hour} 点了，工作顺利吗？",
                f"{hour} 点啦，记得喝水哦~",
            ]
            emotion = EmotionTag(tag="happy", intensity=0.5)
        elif 12 <= hour < 14:
            templates = [
                f"中午 {hour} 点了！该吃饭啦~",
                f"{hour} 点了，午餐时间！别饿着自己~",
            ]
            emotion = EmotionTag(tag="happy", intensity=0.6)
        elif 14 <= hour < 18:
            templates = [
                f"下午 {hour} 点了，继续加油！",
                f"{hour} 点啦，要不要休息一下？",
            ]
            emotion = EmotionTag(tag="neutral", intensity=0.5)
        elif 18 <= hour < 21:
            templates = [
                f"晚上 {hour} 点了，辛苦啦~",
                f"{hour} 点了，晚饭吃了吗？",
            ]
            emotion = EmotionTag(tag="happy", intensity=0.5)
        elif 21 <= hour < 24:
            templates = [
                f"已经 {hour} 点了，早点休息吧~",
                f"夜深了...{hour} 点了哦",
            ]
            emotion = EmotionTag(tag="tired", intensity=0.5)
        else:  # 0-6 点 / 0-6 o'clock
            templates = [
                f"凌晨 {hour} 点了...你还不睡吗？",
                f"都 {hour} 点了！快去睡觉！",
            ]
            emotion = EmotionTag(tag="anxious", intensity=0.6)

        return random.choice(templates), emotion

    def _rule_system_warning(
        self, context: Dict[str, Any]
    ) -> tuple[str, EmotionTag]:
        """
        系统警告规则
        System warning rule

        Args:
            context: 上下文信息 / Context info

        Returns:
            (响应文本, 情感标签) / (response text, emotion tag)
        """
        warning_type = context.get("warning_type", "unknown")
        value = context.get("value", 0)

        if warning_type == "cpu_high":
            text = f"电脑好热！CPU 使用率 {value}%，要不要休息一下？"
            emotion = EmotionTag(tag="anxious", intensity=0.6)
        elif warning_type == "memory_high":
            text = f"内存快满了（{value}%），关掉一些程序吧~"
            emotion = EmotionTag(tag="anxious", intensity=0.5)
        elif warning_type == "battery_low":
            text = f"电量只剩 {value}% 了！快充电！"
            emotion = EmotionTag(tag="anxious", intensity=0.7)
        else:
            text = "系统好像有点问题..."
            emotion = EmotionTag(tag="anxious", intensity=0.4)

        return text, emotion

    def _rule_weather_update(
        self, context: Dict[str, Any]
    ) -> tuple[str, EmotionTag]:
        """
        天气更新规则
        Weather update rule

        Args:
            context: 上下文信息 / Context info

        Returns:
            (响应文本, 情感标签) / (response text, emotion tag)
        """
        weather = context.get("weather", "未知")
        temp = context.get("temperature", "?")

        weather_responses = {
            "晴": (f"今天天气真好！{temp}℃，适合出门~", EmotionTag(tag="happy", intensity=0.7)),
            "多云": (f"多云天气，{temp}℃，挺舒服的~", EmotionTag(tag="neutral", intensity=0.5)),
            "阴": (f"今天阴天，{temp}℃，心情可别阴哦~", EmotionTag(tag="neutral", intensity=0.4)),
            "雨": (f"下雨了！{temp}℃，记得带伞~", EmotionTag(tag="sad", intensity=0.4)),
            "雪": (f"下雪啦！{temp}℃，好冷...", EmotionTag(tag="surprised", intensity=0.6)),
        }

        return weather_responses.get(
            weather, (f"天气：{weather}，{temp}℃", EmotionTag.default())
        )

    def _rule_proactive_greeting(
        self, context: Dict[str, Any]
    ) -> tuple[str, EmotionTag]:
        """
        主动问候规则
        Proactive greeting rule

        Args:
            context: 上下文信息 / Context info

        Returns:
            (响应文本, 情感标签) / (response text, emotion tag)
        """
        idle_minutes = context.get("idle_minutes", 0)

        if idle_minutes > 60:
            templates = [
                "好久没说话了，你在忙什么呀？",
                "我有点无聊...你在吗？",
                "一个人待着好寂寞...",
            ]
            emotion = EmotionTag(tag="sad", intensity=0.4)
        else:
            templates = [
                "在想什么呢？",
                "嘿嘿~",
                "有什么有趣的事吗？",
            ]
            emotion = EmotionTag(tag="happy", intensity=0.5)

        return random.choice(templates), emotion

    def _rule_tool_execution(
        self, context: Dict[str, Any]
    ) -> tuple[str, EmotionTag]:
        """
        工具执行结果规则
        Tool execution result rule

        Args:
            context: 上下文信息 / Context info

        Returns:
            (响应文本, 情感标签) / (response text, emotion tag)
        """
        tool_name = context.get("tool_name", "工具")
        success = context.get("success", True)
        result = context.get("result", "")

        if success:
            text = f"{tool_name} 执行成功！{result}"
            emotion = EmotionTag(tag="happy", intensity=0.6)
        else:
            error = context.get("error", "未知错误")
            text = f"{tool_name} 执行失败了...{error}"
            emotion = EmotionTag(tag="sad", intensity=0.5)

        return text, emotion

    def _rule_default(self, context: Dict[str, Any]) -> tuple[str, EmotionTag]:
        """
        默认规则
        Default rule

        Args:
            context: 上下文信息 / Context info

        Returns:
            (响应文本, 情感标签) / (response text, emotion tag)
        """
        return "嗯...", EmotionTag.default()

    def register_rule(
        self,
        scene_id: str,
        rule_func: Callable[[Dict[str, Any]], tuple[str, EmotionTag]],
    ) -> None:
        """
        注册自定义规则
        Register custom rule

        Args:
            scene_id: 场景 ID / Scene ID
            rule_func: 规则函数 / Rule function
        """
        self._rules[scene_id] = rule_func


class Tier3LLMHandler(BaseTierHandler):
    """
    Tier3 LLM 生成处理器
    Tier3 LLM Generation Handler

    用于复杂场景，调用 LLM 生成响应。
    For complex scenes, call LLM to generate responses.

    特点 / Features:
    - 响应时间 <3s / Response time <3s
    - 调用 AI 服务 / Call AI service
    - 支持记忆检索增强 / Support memory retrieval augmentation
    """

    tier = ResponseTier.TIER3_LLM

    def __init__(self, timeout_ms: int = 3000) -> None:
        """
        初始化 Tier3 处理器
        Initialize Tier3 handler

        Args:
            timeout_ms: 超时时间，默认 3000ms / Timeout, default 3000ms
        """
        super().__init__(timeout_ms)

        # AI 服务引用（延迟注入）/ AI service reference (lazy injection)
        self._ai_service: Optional[Any] = None

        # 兜底模板（当 LLM 不可用时）/ Fallback templates (when LLM unavailable)
        self._fallback_templates: List[str] = [
            "嗯...让我想想...",
            "抱歉，我现在有点迷糊...",
            "呃...你能再说一遍吗？",
            "我的脑子好像卡住了...",
        ]

    def set_ai_service(self, ai_service: Any) -> None:
        """
        设置 AI 服务
        Set AI service

        Args:
            ai_service: AI 服务实例 / AI service instance
        """
        self._ai_service = ai_service

    async def handle(
        self,
        request: InteractionRequest,
        classification: "ClassificationResult",
        context: Optional[Dict[str, Any]] = None,
    ) -> TierResponse:
        """
        调用 LLM 生成响应
        Call LLM to generate response

        Args:
            request: 交互请求 / Interaction request
            classification: 场景分类结果 / Scene classification result
            context: 额外上下文（包含记忆检索结果）
                     Additional context (including memory retrieval results)

        Returns:
            TierResponse: LLM 生成的响应 / LLM generated response
        """
        context = context or {}

        # 获取用户输入 / Get user input
        user_input = request.payload.get("text", "")

        # TODO: 当 AI 服务模块实现后，取消下面注释
        # When AI service module is implemented, uncomment below
        #
        # if self._ai_service is None:
        #     return self._fallback_response()
        #
        # try:
        #     # 构建提示词 / Build prompt
        #     memory_context = context.get("memory_context", "")
        #     state_context = context.get("state_context", "")
        #
        #     # 调用 AI 服务 / Call AI service
        #     result = await self._ai_service.generate_response(
        #         user_input=user_input,
        #         memory_context=memory_context,
        #         state_context=state_context,
        #     )
        #
        #     # 解析情感标签 / Parse emotion tag
        #     emotion = EmotionTag.parse(result.text) or EmotionTag.default()
        #     clean_text = EmotionTag.strip_from_text(result.text)
        #
        #     return TierResponse(
        #         success=True,
        #         text=clean_text,
        #         emotion=emotion,
        #         tier_used=self.tier,
        #     )
        # except Exception:
        #     return self._fallback_response()

        # 临时实现：使用占位响应 / Temporary: use placeholder response
        return self._placeholder_response(user_input)

    def _placeholder_response(self, user_input: str) -> TierResponse:
        """
        占位响应（AI 服务未实现时使用）
        Placeholder response (used when AI service not implemented)

        Args:
            user_input: 用户输入 / User input

        Returns:
            占位响应 / Placeholder response
        """
        # 简单的关键词响应映射 / Simple keyword response mapping
        if "你好" in user_input or "嗨" in user_input:
            text = "你好呀！今天过得怎么样？"
            emotion = EmotionTag(tag="happy", intensity=0.7)
        elif "再见" in user_input or "拜拜" in user_input:
            text = "再见啦！下次见~"
            emotion = EmotionTag(tag="sad", intensity=0.3)
        elif "开心" in user_input or "高兴" in user_input:
            text = "太好了！看到你开心我也很开心~"
            emotion = EmotionTag(tag="happy", intensity=0.8)
        elif "难过" in user_input or "伤心" in user_input:
            text = "怎么了？有什么事可以跟我说说~"
            emotion = EmotionTag(tag="sad", intensity=0.5)
        elif "?" in user_input or "？" in user_input:
            text = "这是个好问题...让我想想..."
            emotion = EmotionTag(tag="neutral", intensity=0.5)
        else:
            text = "嗯嗯，我在听你说~"
            emotion = EmotionTag(tag="neutral", intensity=0.5)

        return TierResponse(
            success=True,
            text=text,
            emotion=emotion,
            tier_used=self.tier,
        )

    def _fallback_response(self) -> TierResponse:
        """
        兜底响应
        Fallback response

        Returns:
            兜底响应 / Fallback response
        """
        return TierResponse(
            success=False,
            text=random.choice(self._fallback_templates),
            emotion=EmotionTag(tag="neutral", intensity=0.3),
            tier_used=self.tier,
            fallback_used=True,
        )


class TierHandlerRegistry:
    """
    层级处理器注册表
    Tier Handler Registry

    管理所有层级处理器，支持按层级获取和降级链处理。
    Manage all tier handlers, support tier lookup and fallback chain.

    Attributes:
        _handlers: 层级 -> 处理器映射 / Tier -> handler mapping
    """

    def __init__(self) -> None:
        """
        初始化注册表，注册默认处理器
        Initialize registry, register default handlers
        """
        self._handlers: Dict[ResponseTier, BaseTierHandler] = {}

        # 注册默认处理器 / Register default handlers
        self.register(Tier1TemplateHandler())
        self.register(Tier2RuleHandler())
        self.register(Tier3LLMHandler())

    def register(self, handler: BaseTierHandler) -> None:
        """
        注册处理器
        Register handler

        Args:
            handler: 层级处理器 / Tier handler
        """
        self._handlers[handler.tier] = handler

    def get(self, tier: ResponseTier) -> Optional[BaseTierHandler]:
        """
        获取指定层级的处理器
        Get handler for specified tier

        Args:
            tier: 响应层级 / Response tier

        Returns:
            处理器实例，不存在返回 None / Handler instance, None if not exists
        """
        return self._handlers.get(tier)

    async def handle_with_fallback(
        self,
        request: InteractionRequest,
        classification: "ClassificationResult",
        context: Optional[Dict[str, Any]] = None,
    ) -> TierResponse:
        """
        带降级链的处理
        Handle with fallback chain

        按照场景配置的降级链依次尝试处理，直到成功或所有层级都失败。
        Try handlers in fallback chain order until success or all tiers fail.

        Args:
            request: 交互请求 / Interaction request
            classification: 场景分类结果 / Scene classification result
            context: 额外上下文 / Additional context

        Returns:
            TierResponse: 最终响应 / Final response
        """
        mapping = classification.mapping

        # 首先尝试默认层级 / First try default tier
        tiers_to_try = [mapping.default_tier] + mapping.fallback_chain

        for tier in tiers_to_try:
            handler = self.get(tier)
            if handler is None:
                continue

            # 使用带超时的处理方法 / Use handler with timeout
            response = await handler.handle_with_timeout(
                request, classification, context
            )

            if response.success:
                # 标记是否使用了降级 / Mark if fallback was used
                if tier != mapping.default_tier:
                    response.fallback_used = True
                return response

        # 所有层级都失败，返回最后的失败响应或默认失败
        # All tiers failed, return last failure or default failure
        return TierResponse(
            success=False,
            text="抱歉，我现在无法回应...",
            emotion=EmotionTag.default(),
            tier_used=tiers_to_try[-1] if tiers_to_try else None,
            fallback_used=True,
        )

    def get_tier1_handler(self) -> Tier1TemplateHandler:
        """获取 Tier1 处理器 / Get Tier1 handler"""
        handler = self._handlers.get(ResponseTier.TIER1_TEMPLATE)
        if isinstance(handler, Tier1TemplateHandler):
            return handler
        raise ValueError("Tier1 handler not registered or wrong type")

    def get_tier2_handler(self) -> Tier2RuleHandler:
        """获取 Tier2 处理器 / Get Tier2 handler"""
        handler = self._handlers.get(ResponseTier.TIER2_RULE)
        if isinstance(handler, Tier2RuleHandler):
            return handler
        raise ValueError("Tier2 handler not registered or wrong type")

    def get_tier3_handler(self) -> Tier3LLMHandler:
        """获取 Tier3 处理器 / Get Tier3 handler"""
        handler = self._handlers.get(ResponseTier.TIER3_LLM)
        if isinstance(handler, Tier3LLMHandler):
            return handler
        raise ValueError("Tier3 handler not registered or wrong type")
