"""
情感推断器
Emotion Inferrer

本模块提供 EmotionTag 的多层降级推断策略。
This module provides multi-layer fallback inference strategy for EmotionTag.

降级链 / Fallback Chain:
1. LLM 输出解析 [EMOTION:tag:intensity]
2. SnowNLP 情感分析 → 映射到 EmotionTag
3. 规则推断（关键词/标点符号）
4. 默认值 neutral:0.5

⚠️ SnowNLP 注意事项:
- 基于预训练模型，可能不适用于所有类型文本
- 处理 Unicode 编码，需注意编码问题
- 对于特定领域文本可能需要额外训练

Reference:
    - PRD §6.0: EmotionTag 降级策略
    - PRD §0.3: 混合响应策略

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import logging
import re
from typing import Optional, Tuple

from rainze.core.contracts import EmotionTag

logger = logging.getLogger(__name__)

# ========================================
# 常量定义 / Constants
# ========================================

# 情感标签正则表达式 / Emotion tag regex pattern
EMOTION_TAG_PATTERN = re.compile(r"\[EMOTION:(\w+):([\d.]+)\]")

# 有效情感标签列表 / Valid emotion tags
VALID_EMOTION_TAGS = {
    "happy", "excited", "sad", "angry", "shy",
    "surprised", "tired", "anxious", "neutral",
    "curious", "annoyed",
}

# ========================================
# 规则推断配置 / Rule inference config
# ========================================

# 正面关键词 → happy / Positive keywords
# 注意：避免单字符匹配导致误判（如"好"会匹配"好难过"）
POSITIVE_KEYWORDS = {
    "开心", "高兴", "快乐", "喜欢", "爱",
    "太好了", "真棒", "厉害", "哈哈", "嘻嘻", "嘿嘿",
    "谢谢", "感谢", "喵", "♪", "♥",
    "真好", "好棒", "好开心", "好高兴",
}

# 负面关键词 → sad/anxious / Negative keywords
NEGATIVE_KEYWORDS = {
    "难过", "伤心", "哭", "累", "烦", "讨厌", "不好",
    "唉", "呜", "呃", "糟糕", "抱歉", "对不起",
    "担心", "焦虑", "害怕", "好难过", "好伤心",
}

# 惊讶关键词 → surprised / Surprise keywords
SURPRISE_KEYWORDS = {
    "哇", "啊", "咦", "诶", "天哪", "什么", "真的吗",
    "不会吧", "居然", "竟然",
}

# 害羞关键词 → shy / Shy keywords
SHY_KEYWORDS = {
    "害羞", "脸红", "不好意思", "嘛", "人家",
    "讨厌啦", "哼",
}

# 标点符号强度调整 / Punctuation intensity adjustments
PUNCTUATION_ADJUSTMENTS = {
    "!": 0.15,
    "！": 0.15,
    "?": 0.05,
    "？": 0.05,
    "~": 0.1,
    "...": -0.15,
    "。。。": -0.15,
}


class EmotionInferrer:
    """
    情感推断器
    Emotion Inferrer

    提供多层降级的情感推断策略。
    Provides multi-layer fallback emotion inference strategy.

    使用方式 / Usage:
        inferrer = EmotionInferrer()
        text, emotion = inferrer.infer("今天天气真好呢~ [EMOTION:happy:0.7]")
        # text = "今天天气真好呢~"
        # emotion = EmotionTag(tag="happy", intensity=0.7)

    Attributes:
        _snownlp_available: SnowNLP 是否可用 / Whether SnowNLP is available
        _enable_snownlp: 是否启用 SnowNLP / Whether to enable SnowNLP
        _enable_rule_fallback: 是否启用规则降级 / Whether to enable rule fallback
    """

    def __init__(
        self,
        enable_snownlp: bool = True,
        enable_rule_fallback: bool = True,
    ) -> None:
        """
        初始化情感推断器
        Initialize emotion inferrer

        Args:
            enable_snownlp: 是否启用 SnowNLP / Whether to enable SnowNLP
            enable_rule_fallback: 是否启用规则降级 / Whether to enable rule fallback
        """
        self._enable_snownlp = enable_snownlp
        self._enable_rule_fallback = enable_rule_fallback
        self._snownlp_available = False

        # 尝试导入 SnowNLP / Try importing SnowNLP
        if enable_snownlp:
            try:
                from snownlp import SnowNLP  # type: ignore[import-untyped]  # noqa: F401
                self._snownlp_available = True
                logger.info("SnowNLP 可用，启用情感分析降级")
            except ImportError:
                logger.warning("SnowNLP 未安装，跳过情感分析降级")

    def infer(self, text: str) -> Tuple[str, EmotionTag]:
        """
        推断文本的情感标签
        Infer emotion tag from text

        降级链 / Fallback chain:
        1. 解析 [EMOTION:tag:intensity] 标签
        2. SnowNLP 情感分析
        3. 规则推断（关键词/标点）
        4. 默认值

        Args:
            text: 输入文本（可能包含情感标签）/ Input text (may contain emotion tag)

        Returns:
            (clean_text, emotion_tag) 元组
            - clean_text: 移除标签后的文本 / Text with tag removed
            - emotion_tag: 推断的情感标签 / Inferred emotion tag
        """
        # Step 1: 尝试解析 LLM 输出的标签 / Try parsing LLM output tag
        clean_text, emotion = self._parse_llm_tag(text)
        if emotion is not None:
            logger.debug(f"LLM 标签解析成功: {emotion.tag}:{emotion.intensity}")
            return clean_text, emotion

        # Step 2: 尝试 SnowNLP 情感分析 / Try SnowNLP sentiment analysis
        if self._enable_snownlp and self._snownlp_available:
            emotion = self._infer_with_snownlp(clean_text)
            if emotion is not None:
                logger.debug(f"SnowNLP 推断成功: {emotion.tag}:{emotion.intensity}")
                return clean_text, emotion

        # Step 3: 规则推断 / Rule-based inference
        if self._enable_rule_fallback:
            emotion = self._infer_with_rules(clean_text)
            logger.debug(f"规则推断: {emotion.tag}:{emotion.intensity}")
            return clean_text, emotion

        # Step 4: 默认值 / Default value
        logger.debug("使用默认情感标签")
        return clean_text, EmotionTag.default()

    def _parse_llm_tag(self, text: str) -> Tuple[str, Optional[EmotionTag]]:
        """
        解析 LLM 输出的情感标签
        Parse emotion tag from LLM output

        格式 / Format: [EMOTION:tag:intensity]

        Args:
            text: LLM 响应文本 / LLM response text

        Returns:
            (clean_text, emotion_tag) 元组，未找到标签时 emotion_tag 为 None
        """
        match = EMOTION_TAG_PATTERN.search(text)

        if not match:
            return text.strip(), None

        # 提取标签和强度 / Extract tag and intensity
        tag = match.group(1).lower()
        try:
            intensity = float(match.group(2))
            intensity = max(0.0, min(1.0, intensity))
        except ValueError:
            intensity = 0.5

        # 验证标签有效性 / Validate tag
        if tag not in VALID_EMOTION_TAGS:
            logger.warning(f"无效的情感标签: {tag}，使用 neutral")
            tag = "neutral"

        # 移除标签 / Remove tag
        clean_text = EMOTION_TAG_PATTERN.sub("", text).strip()

        return clean_text, EmotionTag(tag=tag, intensity=intensity)

    def _infer_with_snownlp(self, text: str) -> Optional[EmotionTag]:
        """
        使用 SnowNLP 推断情感
        Infer emotion using SnowNLP

        ⚠️ 注意:
        - SnowNLP 返回情感极性 (0-1)，0=负面，1=正面
        - 需要映射到具体的情感标签
        - 预训练模型可能不适用于所有文本类型
        - 处理 Unicode 编码

        Args:
            text: 输入文本 / Input text

        Returns:
            推断的情感标签，失败返回 None / Inferred emotion tag, None on failure
        """
        try:
            from snownlp import SnowNLP

            # 确保文本是 Unicode / Ensure text is Unicode
            if isinstance(text, bytes):
                text = text.decode("utf-8")

            # 过滤空文本 / Filter empty text
            if not text or len(text.strip()) < 2:
                return None

            # 分析情感 / Analyze sentiment
            s = SnowNLP(text)
            sentiment = s.sentiments  # 0-1, 0=负面, 1=正面

            # 映射到 EmotionTag / Map to EmotionTag
            return self._map_sentiment_to_emotion(sentiment, text)

        except Exception as e:
            logger.warning(f"SnowNLP 分析失败: {e}")
            return None

    def _map_sentiment_to_emotion(
        self,
        sentiment: float,
        text: str,
    ) -> EmotionTag:
        """
        将 SnowNLP 情感极性映射到 EmotionTag
        Map SnowNLP sentiment polarity to EmotionTag

        映射规则 / Mapping rules:
        - sentiment > 0.75: happy (高正面)
        - sentiment > 0.55: neutral 偏正 (轻微正面)
        - sentiment > 0.45: neutral (中性)
        - sentiment > 0.25: sad (轻微负面)
        - sentiment <= 0.25: anxious (高负面)

        同时检查关键词进行细化 / Also check keywords for refinement

        Args:
            sentiment: SnowNLP 情感极性 (0-1) / SnowNLP sentiment (0-1)
            text: 原始文本，用于关键词检测 / Original text for keyword detection

        Returns:
            映射后的情感标签 / Mapped emotion tag
        """
        # 检查特殊关键词进行细化 / Check special keywords for refinement

        # 惊讶检测 / Surprise detection
        if any(kw in text for kw in SURPRISE_KEYWORDS):
            return EmotionTag(tag="surprised", intensity=0.6 + sentiment * 0.2)

        # 害羞检测 / Shy detection
        if any(kw in text for kw in SHY_KEYWORDS):
            return EmotionTag(tag="shy", intensity=0.5 + sentiment * 0.2)

        # 基于情感极性映射 / Map based on sentiment polarity
        if sentiment > 0.75:
            # 高正面 → happy / High positive → happy
            intensity = 0.5 + (sentiment - 0.75) * 2  # 0.5-1.0
            return EmotionTag(tag="happy", intensity=min(1.0, intensity))

        elif sentiment > 0.55:
            # 轻微正面 → happy 低强度 / Slight positive → happy low intensity
            intensity = 0.3 + (sentiment - 0.55) * 1.5  # 0.3-0.6
            return EmotionTag(tag="happy", intensity=intensity)

        elif sentiment > 0.45:
            # 中性 / Neutral
            return EmotionTag(tag="neutral", intensity=0.5)

        elif sentiment > 0.25:
            # 轻微负面 → sad / Slight negative → sad
            intensity = 0.3 + (0.45 - sentiment) * 1.5  # 0.3-0.6
            return EmotionTag(tag="sad", intensity=intensity)

        else:
            # 高负面 → anxious / High negative → anxious
            intensity = 0.5 + (0.25 - sentiment) * 2  # 0.5-1.0
            return EmotionTag(tag="anxious", intensity=min(1.0, intensity))

    def _infer_with_rules(self, text: str) -> EmotionTag:
        """
        使用规则推断情感
        Infer emotion using rules

        PRD §6.0 降级策略:
        - 检测到"!"/"！" → intensity += 0.2
        - 检测到emoji → intensity += 0.1
        - 检测到"..."/"唔" → intensity -= 0.2
        - 默认值: emotion_tag = "neutral", intensity = 0.5

        Args:
            text: 输入文本 / Input text

        Returns:
            推断的情感标签 / Inferred emotion tag
        """
        # 默认值 / Default values
        tag = "neutral"
        intensity = 0.5

        # 统计关键词匹配 / Count keyword matches
        positive_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
        negative_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)
        surprise_count = sum(1 for kw in SURPRISE_KEYWORDS if kw in text)
        shy_count = sum(1 for kw in SHY_KEYWORDS if kw in text)

        # 确定主要情感 / Determine main emotion
        max_count = max(positive_count, negative_count, surprise_count, shy_count)

        if max_count > 0:
            if positive_count == max_count:
                tag = "happy"
                intensity = 0.5 + min(0.3, positive_count * 0.1)
            elif negative_count == max_count:
                tag = "sad" if negative_count <= 2 else "anxious"
                intensity = 0.5 + min(0.3, negative_count * 0.1)
            elif surprise_count == max_count:
                tag = "surprised"
                intensity = 0.6
            elif shy_count == max_count:
                tag = "shy"
                intensity = 0.5

        # 应用标点符号调整 / Apply punctuation adjustments
        for punct, adjustment in PUNCTUATION_ADJUSTMENTS.items():
            if punct in text:
                intensity += adjustment

        # 限制强度范围 / Clamp intensity
        intensity = max(0.1, min(1.0, intensity))

        return EmotionTag(tag=tag, intensity=round(intensity, 2))


# ========================================
# 便捷函数 / Convenience functions
# ========================================

# 全局实例 / Global instance
_default_inferrer: Optional[EmotionInferrer] = None


def get_emotion_inferrer() -> EmotionInferrer:
    """
    获取默认情感推断器实例
    Get default emotion inferrer instance

    Returns:
        情感推断器实例 / Emotion inferrer instance
    """
    global _default_inferrer
    if _default_inferrer is None:
        _default_inferrer = EmotionInferrer()
    return _default_inferrer


def infer_emotion(text: str) -> Tuple[str, EmotionTag]:
    """
    推断文本情感（便捷函数）
    Infer text emotion (convenience function)

    Args:
        text: 输入文本 / Input text

    Returns:
        (clean_text, emotion_tag) 元组
    """
    return get_emotion_inferrer().infer(text)
