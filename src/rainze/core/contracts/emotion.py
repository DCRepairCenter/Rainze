"""
情感标签契约
Emotion Tag Contract

本模块定义统一的情感标签数据结构，所有模块必须使用此定义。
This module defines unified emotion tag structure, all modules MUST use this.

Reference:
    - PRD §0.15: 跨模块契约
    - MOD-Core.md §11.1: EmotionTag

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar, Optional, Set


@dataclass(frozen=True)
class EmotionTag:
    """
    统一情感标签数据结构
    Unified emotion tag data structure

    所有模块（AI/State/Animation）必须使用此定义。
    All modules (AI/State/Animation) MUST use this definition.

    Attributes:
        tag: 情感类型 / Emotion type (happy/sad/angry/shy/etc.)
        intensity: 强度 / Intensity [0.0, 1.0]

    Example:
        >>> emotion = EmotionTag(tag="happy", intensity=0.8)
        >>> print(emotion.to_string())
        [EMOTION:happy:0.80]
        >>> parsed = EmotionTag.parse("你好呀~ [EMOTION:happy:0.8]")
        >>> print(parsed.tag)
        happy
    """

    # 类变量 / Class variables
    PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"\[EMOTION:(\w+):([\d.]+)\]")
    VALID_TAGS: ClassVar[Set[str]] = {
        "happy",
        "excited",
        "sad",
        "angry",
        "shy",
        "surprised",
        "tired",
        "anxious",
        "neutral",
    }

    tag: str
    intensity: float

    def __post_init__(self) -> None:
        """
        验证标签和强度
        Validate tag and intensity
        """
        # 使用 object.__setattr__ 因为 frozen=True
        # Use object.__setattr__ because frozen=True
        if self.tag not in self.VALID_TAGS:
            # 对于无效标签，回退到 neutral
            # For invalid tags, fallback to neutral
            object.__setattr__(self, "tag", "neutral")

        # 确保强度在 [0.0, 1.0] 范围内
        # Ensure intensity is in [0.0, 1.0] range
        clamped = max(0.0, min(1.0, self.intensity))
        if clamped != self.intensity:
            object.__setattr__(self, "intensity", clamped)

    def to_string(self) -> str:
        """
        序列化为标签格式
        Serialize to tag format

        Returns:
            格式化的情感标签字符串 / Formatted emotion tag string
            如 / Like: [EMOTION:happy:0.80]
        """
        return f"[EMOTION:{self.tag}:{self.intensity:.2f}]"

    @classmethod
    def parse(cls, text: str) -> Optional["EmotionTag"]:
        """
        从文本解析情感标签
        Parse emotion tag from text

        Args:
            text: 包含情感标签的文本 / Text containing emotion tag

        Returns:
            解析的 EmotionTag，无标签返回 None
            Parsed EmotionTag, None if no tag found
        """
        match = cls.PATTERN.search(text)
        if not match:
            return None

        tag = match.group(1).lower()
        try:
            intensity = float(match.group(2))
        except ValueError:
            intensity = 0.5

        return cls(tag=tag, intensity=intensity)

    @classmethod
    def strip_from_text(cls, text: str) -> str:
        """
        移除文本中的情感标签
        Remove emotion tag from text

        Args:
            text: 原始文本 / Original text

        Returns:
            移除标签后的文本 / Text with tag removed
        """
        return cls.PATTERN.sub("", text).strip()

    @classmethod
    def default(cls) -> "EmotionTag":
        """
        返回默认情感标签
        Return default emotion tag

        Returns:
            默认的 neutral 情感 / Default neutral emotion
        """
        return cls(tag="neutral", intensity=0.5)
