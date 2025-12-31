"""
Tier3 LLM 响应生成器
Tier3 LLM Response Generator

本模块实现基于 LLM 的智能响应生成（500-2000ms）。
This module implements LLM-based intelligent response generation (500-2000ms).

适用场景 / Use Cases:
    - 自由对话 / Free conversation
    - 情感支持 / Emotional support
    - 复杂查询 / Complex queries

Reference:
    - PRD §0.3: 混合响应策略
    - MOD-AI.md §3.4: Tier3LLMGenerator

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from rainze.ai.exceptions import GenerationError, LLMAPIError
from rainze.ai.generation.strategy import GeneratedResponse
from rainze.core.contracts import EmotionTag, ResponseTier

if TYPE_CHECKING:
    from rainze.ai.llm.client import LLMClient


# 情感标签正则表达式 / Emotion tag regex pattern
EMOTION_TAG_PATTERN = re.compile(r"\[EMOTION:(\w+):([\d.]+)\]")

# 默认系统提示词 / Default system prompt
DEFAULT_SYSTEM_PROMPT = """你是 Rainze，一个可爱的桌面宠物 AI 伴侣。

你的性格特点：
- 温柔可爱，对主人充满关心
- 有点小调皮，偶尔会撒娇
- 知识渊博但不炫耀
- 会关心主人的身心健康

回复规则：
1. 使用轻松自然的语气，像朋友一样对话
2. 回复简短精炼，通常不超过 50 字
3. 可以使用一些可爱的语气词，如"呢"、"哦"、"~"
4. 在回复末尾添加情感标签，格式: [EMOTION:标签:强度]
   - 标签可选: happy, excited, sad, angry, shy, surprised, tired, anxious, neutral
   - 强度范围: 0.0-1.0

示例回复：
- "今天天气真好呢~ 要不要出去走走？ [EMOTION:happy:0.7]"
- "哎呀，你看起来有点累... 要休息一下吗？ [EMOTION:anxious:0.5]"
"""


class Tier3LLMGenerator:
    """
    Tier3 LLM 响应生成器
    Tier3 LLM Response Generator

    调用 LLM API 生成智能响应。
    Calls LLM API to generate intelligent responses.

    性能目标 / Performance Target: 500-2000ms

    Attributes:
        _llm_client: LLM 客户端 / LLM client
        _system_prompt: 系统提示词 / System prompt
        _default_model: 默认模型 / Default model
        _default_temperature: 默认温度 / Default temperature
        _default_max_tokens: 默认最大 Token 数 / Default max tokens
        _timeout_seconds: 超时时间 / Timeout in seconds
    """

    def __init__(
        self,
        llm_client: "LLMClient",
        system_prompt: Optional[str] = None,
        default_model: str = "claude-sonnet-4-20250514",
        default_temperature: float = 0.8,
        default_max_tokens: int = 150,
        timeout_seconds: float = 3.0,
    ) -> None:
        """
        初始化 LLM 生成器
        Initialize LLM generator

        Args:
            llm_client: LLM 客户端实例 / LLM client instance
            system_prompt: 系统提示词 / System prompt
            default_model: 默认模型 / Default model
            default_temperature: 默认温度 / Default temperature
            default_max_tokens: 默认最大 Token 数 / Default max tokens
            timeout_seconds: 超时时间（秒）/ Timeout in seconds
        """
        self._llm_client = llm_client
        self._system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self._default_model = default_model
        self._default_temperature = default_temperature
        self._default_max_tokens = default_max_tokens
        self._timeout_seconds = timeout_seconds

    async def generate(
        self,
        scene_type: str,
        context: Dict[str, Any],
        user_input: Optional[str] = None,
    ) -> GeneratedResponse:
        """
        调用 LLM 生成响应
        Generate response using LLM

        Args:
            scene_type: 场景类型 / Scene type
            context: 上下文数据 / Context data
            user_input: 用户输入 / User input

        Returns:
            生成的响应 / Generated response

        Raises:
            GenerationError: 生成失败 / Generation failed
        """
        start_time = time.perf_counter()

        # 构建消息 / Build messages
        messages = self._build_messages(scene_type, context, user_input)

        # 构建请求 / Build request
        from rainze.ai.llm.client import LLMRequest

        request = LLMRequest(
            system=self._build_system_prompt(scene_type, context),
            messages=messages,
            model=self._default_model,
            temperature=self._default_temperature,
            max_tokens=self._default_max_tokens,
            timeout_seconds=self._timeout_seconds,
        )

        try:
            # 调用 LLM / Call LLM
            llm_response = await self._llm_client.generate(request)
            content = llm_response.content

            # 解析响应 / Parse response
            clean_text, emotion_tag, intensity = self._parse_emotion_tag(content)

            # 创建情感标签 / Create emotion tag
            emotion: Optional[EmotionTag] = None
            if emotion_tag:
                emotion = EmotionTag(tag=emotion_tag, intensity=intensity)

            latency_ms = (time.perf_counter() - start_time) * 1000

            return GeneratedResponse(
                text=clean_text,
                emotion_tag=emotion,
                tier_used=ResponseTier.TIER3_LLM,
                latency_ms=latency_ms,
                metadata={
                    "model": llm_response.model,
                    "input_tokens": llm_response.input_tokens,
                    "output_tokens": llm_response.output_tokens,
                    "finish_reason": llm_response.finish_reason,
                    "llm_latency_ms": llm_response.latency_ms,
                },
            )

        except LLMAPIError as e:
            raise GenerationError(
                f"LLM API error: {e} / LLM API 错误: {e}",
                tier="TIER3_LLM",
            ) from e

        except Exception as e:
            raise GenerationError(
                f"Unexpected error: {e} / 意外错误: {e}",
                tier="TIER3_LLM",
            ) from e

    def _build_system_prompt(
        self,
        scene_type: str,
        context: Dict[str, Any],
    ) -> str:
        """
        构建系统提示词
        Build system prompt

        Args:
            scene_type: 场景类型 / Scene type
            context: 上下文 / Context

        Returns:
            系统提示词 / System prompt
        """
        # 基础系统提示词 / Base system prompt
        prompt = self._system_prompt

        # 添加场景特定指令 / Add scene-specific instructions
        scene_instructions = self._get_scene_instructions(scene_type)
        if scene_instructions:
            prompt += f"\n\n当前场景指令:\n{scene_instructions}"

        # 添加上下文信息 / Add context information
        if context:
            context_str = self._format_context(context)
            if context_str:
                prompt += f"\n\n当前上下文:\n{context_str}"

        return prompt

    def _get_scene_instructions(self, scene_type: str) -> str:
        """
        获取场景特定指令
        Get scene-specific instructions
        """
        instructions: Dict[str, str] = {
            "conversation": "这是一次自由对话，请自然地回应用户。",
            "emotional_support": "用户可能需要情感支持，请温柔关心。",
            "complex_query": "用户在询问复杂问题，请尽量帮助解答。",
            "story_telling": "用户想听故事，请发挥创意。",
        }
        return instructions.get(scene_type, "")

    def _format_context(self, context: Dict[str, Any]) -> str:
        """
        格式化上下文
        Format context
        """
        formatted_parts: List[str] = []

        # 用户状态 / User state
        if "user_mood" in context:
            formatted_parts.append(f"用户心情: {context['user_mood']}")

        # 宠物状态 / Pet state
        if "pet_state" in context:
            formatted_parts.append(f"宠物状态: {context['pet_state']}")

        # 时间 / Time
        if "current_time" in context:
            formatted_parts.append(f"当前时间: {context['current_time']}")

        # 主题 / Topic
        if "topic" in context:
            formatted_parts.append(f"话题: {context['topic']}")

        return "\n".join(formatted_parts)

    def _build_messages(
        self,
        scene_type: str,
        context: Dict[str, Any],
        user_input: Optional[str],
    ) -> List[Dict[str, str]]:
        """
        构建消息列表
        Build message list

        Args:
            scene_type: 场景类型 / Scene type
            context: 上下文 / Context
            user_input: 用户输入 / User input

        Returns:
            消息列表 / Message list
        """
        messages: List[Dict[str, str]] = []

        # 添加对话历史 / Add conversation history
        history = context.get("conversation_history", [])
        for msg in history[-10:]:  # 最近 10 条 / Last 10 messages
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

        # 添加当前用户输入 / Add current user input
        if user_input:
            messages.append({
                "role": "user",
                "content": user_input,
            })
        elif not messages:
            # 如果没有输入，添加一个默认触发 / If no input, add default trigger
            messages.append({
                "role": "user",
                "content": f"[场景触发: {scene_type}]",
            })

        return messages

    def _parse_emotion_tag(self, text: str) -> Tuple[str, Optional[str], float]:
        """
        解析情感标签
        Parse emotion tag

        从 LLM 响应中提取情感标签。
        Extract emotion tag from LLM response.

        格式 / Format: [EMOTION:tag:intensity]

        Args:
            text: LLM 响应文本 / LLM response text

        Returns:
            (clean_text, emotion_tag, intensity) 元组
            - clean_text: 移除标签后的文本 / Text with tag removed
            - emotion_tag: 情感标签（如 "happy"）/ Emotion tag (e.g., "happy")
            - intensity: 强度 (0.0-1.0) / Intensity
        """
        match = EMOTION_TAG_PATTERN.search(text)

        if not match:
            # 未找到标签 / No tag found
            return text.strip(), None, 0.5

        # 提取标签和强度 / Extract tag and intensity
        emotion_tag = match.group(1).lower()
        try:
            intensity = float(match.group(2))
            intensity = max(0.0, min(1.0, intensity))
        except ValueError:
            intensity = 0.5

        # 移除标签 / Remove tag
        clean_text = EMOTION_TAG_PATTERN.sub("", text).strip()

        return clean_text, emotion_tag, intensity

    def set_system_prompt(self, prompt: str) -> None:
        """
        设置系统提示词
        Set system prompt

        Args:
            prompt: 新的系统提示词 / New system prompt
        """
        self._system_prompt = prompt

    def set_default_model(self, model: str) -> None:
        """
        设置默认模型
        Set default model

        Args:
            model: 模型名称 / Model name
        """
        self._default_model = model

    def set_timeout(self, timeout_seconds: float) -> None:
        """
        设置超时时间
        Set timeout

        Args:
            timeout_seconds: 超时时间（秒）/ Timeout in seconds
        """
        self._timeout_seconds = max(1.0, timeout_seconds)
