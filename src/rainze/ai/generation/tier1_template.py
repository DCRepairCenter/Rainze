"""
Tier1 模板响应生成器
Tier1 Template Response Generator

本模块实现基于模板的快速响应生成（<50ms）。
This module implements template-based fast response generation (<50ms).

适用场景 / Use Cases:
    - 点击交互 / Click interaction
    - 拖拽交互 / Drag interaction
    - 简单游戏反馈 / Simple game feedback

Reference:
    - PRD §0.3: 混合响应策略
    - MOD-AI.md §3.4: Tier1TemplateGenerator

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import json
import random
import time
from pathlib import Path
from string import Template
from typing import Any, Dict, List, Optional

from rainze.ai.generation.strategy import GeneratedResponse
from rainze.core.contracts import EmotionTag, ResponseTier

# 默认模板（当配置文件不存在时使用）
# Default templates (used when config file doesn't exist)
_DEFAULT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "click": {
        "texts": [
            "嗯？怎么了~",
            "有什么事吗？",
            "我在呢！",
            "戳我干嘛~",
            "你好呀~",
        ],
        "emotion": {"tag": "happy", "intensity": 0.6},
    },
    "drag": {
        "texts": [
            "哇！你要带我去哪里~",
            "嘿嘿，飞起来了~",
            "放我下来啦~",
            "好晕~",
        ],
        "emotion": {"tag": "excited", "intensity": 0.7},
    },
    "double_click": {
        "texts": [
            "别点啦别点啦~",
            "好痒！",
            "你想干嘛？",
        ],
        "emotion": {"tag": "shy", "intensity": 0.5},
    },
    "hover": {
        "texts": [
            "...",
            "？",
            "嗯嗯",
        ],
        "emotion": {"tag": "neutral", "intensity": 0.3},
    },
    "game_interaction": {
        "texts": [
            "玩游戏~",
            "来玩呀！",
            "开始了！",
        ],
        "emotion": {"tag": "excited", "intensity": 0.8},
    },
    "_default": {
        "texts": [
            "嗯？",
            "...",
        ],
        "emotion": {"tag": "neutral", "intensity": 0.5},
    },
}


class Tier1TemplateGenerator:
    """
    Tier1 模板响应生成器
    Tier1 Template Response Generator

    从预定义模板中随机选择响应，支持变量替换。
    Selects responses randomly from predefined templates with variable substitution.

    性能目标 / Performance Target: <50ms

    Attributes:
        _templates: 模板字典 / Template dictionary
        _templates_path: 模板文件路径 / Template file path
    """

    def __init__(self, templates_path: Optional[str] = None) -> None:
        """
        初始化模板生成器
        Initialize template generator

        Args:
            templates_path: 模板配置文件路径 / Template config file path
                           如果为 None，使用默认模板 / If None, use default templates
        """
        self._templates_path = templates_path
        self._templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        加载模板配置
        Load template configuration

        Returns:
            模板字典 / Template dictionary
        """
        if self._templates_path is None:
            return _DEFAULT_TEMPLATES.copy()

        path = Path(self._templates_path)
        if not path.exists():
            # 配置文件不存在，使用默认模板
            # Config file doesn't exist, use default templates
            return _DEFAULT_TEMPLATES.copy()

        try:
            with open(path, encoding="utf-8") as f:
                loaded = json.load(f)
                # 合并默认模板和加载的模板 / Merge default and loaded templates
                templates = _DEFAULT_TEMPLATES.copy()
                templates.update(loaded)
                return templates
        except (json.JSONDecodeError, OSError):
            # 加载失败，使用默认模板 / Load failed, use default templates
            return _DEFAULT_TEMPLATES.copy()

    async def generate(
        self,
        scene_type: str,
        context: Dict[str, Any],
    ) -> GeneratedResponse:
        """
        从模板生成响应
        Generate response from template

        Args:
            scene_type: 场景类型（如 "click", "drag"）/ Scene type
            context: 上下文变量 / Context variables (for template substitution)

        Returns:
            生成的响应 / Generated response
        """
        start_time = time.perf_counter()

        # 获取场景模板 / Get scene template
        template_data = self._templates.get(scene_type) or self._templates.get(
            "_default", {}
        )

        # 获取文本列表 / Get text list
        texts: List[str] = template_data.get("texts", ["..."])
        if not texts:
            texts = ["..."]

        # 随机选择模板 / Randomly select template
        template_text = random.choice(texts)

        # 替换变量 / Substitute variables
        try:
            text = Template(template_text).safe_substitute(context)
        except Exception:
            text = template_text

        # 解析情感标签 / Parse emotion tag
        emotion_data = template_data.get("emotion", {})
        emotion_tag = EmotionTag(
            tag=emotion_data.get("tag", "neutral"),
            intensity=emotion_data.get("intensity", 0.5),
        )

        # 获取动作提示 / Get action hint
        action_hint = template_data.get("action_hint")

        latency_ms = (time.perf_counter() - start_time) * 1000

        return GeneratedResponse(
            text=text,
            emotion_tag=emotion_tag,
            action_hint=action_hint,
            tier_used=ResponseTier.TIER1_TEMPLATE,
            latency_ms=latency_ms,
            from_cache=False,
            metadata={"template_scene": scene_type},
        )

    def add_template(
        self,
        scene_type: str,
        texts: List[str],
        emotion: Optional[Dict[str, Any]] = None,
        action_hint: Optional[str] = None,
    ) -> None:
        """
        添加或更新模板
        Add or update template

        Args:
            scene_type: 场景类型 / Scene type
            texts: 文本列表 / Text list
            emotion: 情感配置 / Emotion config
            action_hint: 动作提示 / Action hint
        """
        self._templates[scene_type] = {
            "texts": texts,
            "emotion": emotion or {"tag": "neutral", "intensity": 0.5},
        }
        if action_hint:
            self._templates[scene_type]["action_hint"] = action_hint

    def reload_templates(self) -> None:
        """
        重新加载模板
        Reload templates
        """
        self._templates = self._load_templates()
