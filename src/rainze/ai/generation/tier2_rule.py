"""
Tier2 规则响应生成器
Tier2 Rule Response Generator

本模块实现基于规则的响应生成（<100ms）。
This module implements rule-based response generation (<100ms).

适用场景 / Use Cases:
    - 整点报时 / Hourly chime
    - 系统警告 / System warning
    - 状态驱动响应 / State-driven responses

Reference:
    - PRD §0.3: 混合响应策略
    - MOD-AI.md §3.4: Tier2RuleGenerator

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import json
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from rainze.ai.generation.strategy import GeneratedResponse
from rainze.core.contracts import EmotionTag, ResponseTier

# 规则处理器类型 / Rule handler type
RuleHandler = Callable[[str, Dict[str, Any]], Optional[GeneratedResponse]]


class Tier2RuleGenerator:
    """
    Tier2 规则响应生成器
    Tier2 Rule Response Generator

    根据预定义规则和上下文生成响应。
    Generates responses based on predefined rules and context.

    性能目标 / Performance Target: <100ms

    Attributes:
        _rules_path: 规则配置文件路径 / Rules config file path
        _rules: 规则配置 / Rule configuration
        _handlers: 自定义规则处理器 / Custom rule handlers
    """

    def __init__(self, rules_path: Optional[str] = None) -> None:
        """
        初始化规则生成器
        Initialize rule generator

        Args:
            rules_path: 规则配置文件路径 / Rules config file path
        """
        self._rules_path = rules_path
        self._rules = self._load_rules()
        self._handlers: Dict[str, RuleHandler] = {}
        self._register_builtin_handlers()

    def _load_rules(self) -> Dict[str, Dict[str, Any]]:
        """
        加载规则配置
        Load rule configuration

        Returns:
            规则字典 / Rule dictionary
        """
        default_rules = self._get_default_rules()

        if self._rules_path is None:
            return default_rules

        path = Path(self._rules_path)
        if not path.exists():
            return default_rules

        try:
            with open(path, encoding="utf-8") as f:
                loaded = json.load(f)
                rules = default_rules.copy()
                rules.update(loaded)
                return rules
        except (json.JSONDecodeError, OSError):
            return default_rules

    def _get_default_rules(self) -> Dict[str, Dict[str, Any]]:
        """
        获取默认规则
        Get default rules
        """
        return {
            "hourly_chime": {
                "handler": "_handle_hourly_chime",
                "emotion": {"tag": "happy", "intensity": 0.6},
            },
            "system_warning": {
                "handler": "_handle_system_warning",
                "emotion": {"tag": "anxious", "intensity": 0.7},
            },
            "low_battery": {
                "handler": "_handle_low_battery",
                "emotion": {"tag": "tired", "intensity": 0.6},
            },
            "high_cpu": {
                "handler": "_handle_high_cpu",
                "emotion": {"tag": "anxious", "intensity": 0.5},
            },
            "daily_greeting": {
                "handler": "_handle_daily_greeting",
                "emotion": {"tag": "happy", "intensity": 0.7},
            },
        }

    def _register_builtin_handlers(self) -> None:
        """
        注册内置处理器
        Register builtin handlers
        """
        self._handlers["_handle_hourly_chime"] = self._handle_hourly_chime
        self._handlers["_handle_system_warning"] = self._handle_system_warning
        self._handlers["_handle_low_battery"] = self._handle_low_battery
        self._handlers["_handle_high_cpu"] = self._handle_high_cpu
        self._handlers["_handle_daily_greeting"] = self._handle_daily_greeting

    async def generate(
        self,
        scene_type: str,
        context: Dict[str, Any],
    ) -> GeneratedResponse:
        """
        根据规则生成响应
        Generate response based on rules

        Args:
            scene_type: 场景类型（如 "hourly_chime"）/ Scene type
            context: 上下文数据 / Context data

        Returns:
            生成的响应 / Generated response
        """
        start_time = time.perf_counter()

        # 获取规则配置 / Get rule config
        rule = self._rules.get(scene_type, {})
        handler_name = rule.get("handler", "")

        # 尝试调用处理器 / Try to call handler
        response: Optional[GeneratedResponse] = None
        if handler_name and handler_name in self._handlers:
            handler = self._handlers[handler_name]
            response = handler(scene_type, context)

        # 如果处理器未返回响应，使用默认响应 / If handler didn't return, use default
        if response is None:
            response = self._generate_default_response(scene_type, context, rule)

        response.latency_ms = (time.perf_counter() - start_time) * 1000
        return response

    def _generate_default_response(
        self,
        scene_type: str,
        context: Dict[str, Any],
        rule: Dict[str, Any],
    ) -> GeneratedResponse:
        """
        生成默认响应
        Generate default response

        Args:
            scene_type: 场景类型 / Scene type
            context: 上下文 / Context
            rule: 规则配置 / Rule config

        Returns:
            默认响应 / Default response
        """
        # 获取情感配置 / Get emotion config
        emotion_data = rule.get("emotion", {"tag": "neutral", "intensity": 0.5})
        emotion_tag = EmotionTag(
            tag=emotion_data.get("tag", "neutral"),
            intensity=emotion_data.get("intensity", 0.5),
        )

        return GeneratedResponse(
            text=f"[{scene_type}]",
            emotion_tag=emotion_tag,
            tier_used=ResponseTier.TIER2_RULE,
            metadata={"rule_scene": scene_type},
        )

    # ===== 内置处理器 / Builtin Handlers =====

    def _handle_hourly_chime(
        self,
        scene_type: str,
        context: Dict[str, Any],
    ) -> GeneratedResponse:
        """
        处理整点报时
        Handle hourly chime
        """
        hour = context.get("hour") or datetime.now().hour

        # 根据时间段选择不同的问候 / Select greeting based on time period
        if 5 <= hour < 12:
            greetings = [
                f"早上好~ 现在是 {hour} 点啦~",
                f"上午 {hour} 点了，今天也要加油哦！",
                f"滴滴~ {hour} 点报时~",
            ]
            emotion = EmotionTag(tag="happy", intensity=0.7)
        elif 12 <= hour < 18:
            greetings = [
                f"下午 {hour} 点啦~ 该休息一下了？",
                f"现在是 {hour} 点~ 喝杯水吧！",
                f"滴滴~ {hour} 点报时~",
            ]
            emotion = EmotionTag(tag="happy", intensity=0.6)
        elif 18 <= hour < 22:
            greetings = [
                f"晚上 {hour} 点了呢~ 辛苦了！",
                f"现在是 {hour} 点~ 今天过得怎么样？",
                f"滴滴~ {hour} 点报时~",
            ]
            emotion = EmotionTag(tag="happy", intensity=0.6)
        else:
            greetings = [
                f"已经 {hour} 点了... 该睡觉了！",
                f"深夜 {hour} 点... 早点休息吧~",
                f"夜深了，{hour} 点了哦...",
            ]
            emotion = EmotionTag(tag="tired", intensity=0.7)

        return GeneratedResponse(
            text=random.choice(greetings),
            emotion_tag=emotion,
            tier_used=ResponseTier.TIER2_RULE,
            metadata={"hour": hour, "rule_scene": scene_type},
        )

    def _handle_system_warning(
        self,
        scene_type: str,
        context: Dict[str, Any],
    ) -> GeneratedResponse:
        """
        处理系统警告
        Handle system warning
        """
        warning_type = context.get("warning_type", "unknown")
        warning_message = context.get("message", "系统警告")

        warnings = {
            "memory": [
                "内存有点紧张了呢... 要关掉一些程序吗？",
                "检测到内存占用较高！要清理一下吗？",
            ],
            "disk": [
                "磁盘空间快满了... 该整理一下了~",
                "存储空间不太够了呢，要清理吗？",
            ],
            "network": [
                "网络好像有点问题...",
                "网络连接似乎不太稳定呢~",
            ],
        }

        texts = warnings.get(warning_type, [warning_message])

        return GeneratedResponse(
            text=random.choice(texts),
            emotion_tag=EmotionTag(tag="anxious", intensity=0.6),
            tier_used=ResponseTier.TIER2_RULE,
            metadata={"warning_type": warning_type, "rule_scene": scene_type},
        )

    def _handle_low_battery(
        self,
        scene_type: str,
        context: Dict[str, Any],
    ) -> GeneratedResponse:
        """
        处理低电量警告
        Handle low battery warning
        """
        battery_level = context.get("battery_level", 20)

        if battery_level <= 10:
            texts = [
                f"电量只剩 {battery_level}% 了！快充电！！",
                f"要没电了！{battery_level}%！快去充电！",
            ]
            emotion = EmotionTag(tag="anxious", intensity=0.9)
        else:
            texts = [
                f"电量 {battery_level}%，该充电了~",
                f"电量有点低了，{battery_level}%，要充电吗？",
            ]
            emotion = EmotionTag(tag="tired", intensity=0.6)

        return GeneratedResponse(
            text=random.choice(texts),
            emotion_tag=emotion,
            tier_used=ResponseTier.TIER2_RULE,
            metadata={"battery_level": battery_level, "rule_scene": scene_type},
        )

    def _handle_high_cpu(
        self,
        scene_type: str,
        context: Dict[str, Any],
    ) -> GeneratedResponse:
        """
        处理高 CPU 使用率
        Handle high CPU usage
        """
        cpu_usage = context.get("cpu_usage", 80)

        if cpu_usage >= 90:
            texts = [
                f"CPU 占用 {cpu_usage}%！电脑要累坏了！",
                f"处理器快冒烟了！{cpu_usage}% 了！",
            ]
            emotion = EmotionTag(tag="anxious", intensity=0.8)
        else:
            texts = [
                f"CPU 有点忙，{cpu_usage}% 了呢~",
                f"处理器占用 {cpu_usage}%，在忙什么呢？",
            ]
            emotion = EmotionTag(tag="anxious", intensity=0.5)

        return GeneratedResponse(
            text=random.choice(texts),
            emotion_tag=emotion,
            tier_used=ResponseTier.TIER2_RULE,
            metadata={"cpu_usage": cpu_usage, "rule_scene": scene_type},
        )

    def _handle_daily_greeting(
        self,
        scene_type: str,
        context: Dict[str, Any],
    ) -> GeneratedResponse:
        """
        处理每日问候
        Handle daily greeting
        """
        hour = datetime.now().hour
        user_name = context.get("user_name", "")
        name_suffix = f"，{user_name}" if user_name else ""

        if 5 <= hour < 12:
            texts = [
                f"早安{name_suffix}~ 新的一天开始啦！",
                f"早上好{name_suffix}！今天也要元气满满哦！",
            ]
            emotion = EmotionTag(tag="happy", intensity=0.8)
        elif 12 <= hour < 18:
            texts = [
                f"下午好{name_suffix}~ 午后时光~",
                f"嗨{name_suffix}~ 下午茶时间？",
            ]
            emotion = EmotionTag(tag="happy", intensity=0.7)
        else:
            texts = [
                f"晚上好{name_suffix}~ 辛苦一天了！",
                f"晚安{name_suffix}~ 今天过得如何？",
            ]
            emotion = EmotionTag(tag="happy", intensity=0.6)

        return GeneratedResponse(
            text=random.choice(texts),
            emotion_tag=emotion,
            tier_used=ResponseTier.TIER2_RULE,
            metadata={"rule_scene": scene_type},
        )

    def register_handler(self, name: str, handler: RuleHandler) -> None:
        """
        注册自定义处理器
        Register custom handler

        Args:
            name: 处理器名称 / Handler name
            handler: 处理器函数 / Handler function
        """
        self._handlers[name] = handler

    def reload_rules(self) -> None:
        """
        重新加载规则
        Reload rules
        """
        self._rules = self._load_rules()
