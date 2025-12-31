"""
脚本上下文
Script Context

提供给行为脚本的受限 API。
Provides restricted API for behavior scripts.

上下文只暴露只读状态视图和请求式控制方法。
Context only exposes read-only state views and request-based control methods.

Reference:
    MOD-Animation-Script.md §3.1: 脚本上下文
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StateView:
    """
    角色状态视图（只读）
    Character state view (read-only)

    所有属性都是只读的，脚本无法修改。
    All attributes are read-only, script cannot modify.
    """

    mood: float  # 心情 (0.0 ~ 1.0)
    energy: float  # 精力 (0.0 ~ 1.0)
    affection: float  # 好感度 (0.0 ~ 1.0)
    hunger: float  # 饥饿度 (0.0 ~ 1.0)
    emotion: str  # 当前情感标签
    emotion_intensity: float  # 情感强度 (0.0 ~ 1.0)


@dataclass(frozen=True)
class TimeView:
    """
    时间视图（只读）
    Time view (read-only)
    """

    hour: int  # 小时 (0-23)
    minute: int  # 分钟 (0-59)
    second: int  # 秒 (0-59)
    weekday: int  # 星期几 (0=周一, 6=周日)
    is_night: bool  # 是否夜间 (22:00 ~ 06:00)
    is_weekend: bool  # 是否周末


@dataclass(frozen=True)
class InteractionView:
    """
    交互统计视图（只读）
    Interaction stats view (read-only)
    """

    last_interaction_seconds: int  # 距上次交互的秒数
    today_interactions: int  # 今日交互次数
    total_interactions: int  # 总交互次数
    consecutive_days: int  # 连续互动天数


@dataclass(frozen=True)
class AnimationView:
    """
    动画状态视图（只读）
    Animation state view (read-only)
    """

    current_animation: str  # 当前动画名
    current_action: str | None  # 当前播放的动作
    is_playing_action: bool  # 是否正在播放动作


class ScriptContext:
    """
    脚本执行上下文
    Script Execution Context

    提供给行为脚本的受限 API。
    Provides restricted API for behavior scripts.

    Attributes:
        _state_manager: 状态管理器引用
        _animation_controller: 动画控制器引用
        _action_requests: 待处理的动作请求
        _effect_requests: 待处理的特效请求
        _interval_setting: 间隔设置

    Example:
        在 behavior.py 中:
        ```python
        def get_random_actions(ctx):
            if ctx.state.mood > 0.7:
                ctx.set_interval(2000, 5000)
                return ["ear_wiggle", "happy_bounce"]
            return ["blink"]
        ```
    """

    def __init__(
        self,
        state_provider: Callable[[], StateView] | None = None,
        animation_provider: Callable[[], AnimationView] | None = None,
        interaction_provider: Callable[[], InteractionView] | None = None,
    ) -> None:
        """
        初始化脚本上下文
        Initialize script context

        Args:
            state_provider: 状态提供函数 / State provider function
            animation_provider: 动画状态提供函数 / Animation state provider
            interaction_provider: 交互统计提供函数 / Interaction stats provider
        """
        self._state_provider = state_provider
        self._animation_provider = animation_provider
        self._interaction_provider = interaction_provider

        # 请求队列 / Request queues
        self._action_requests: list[str] = []
        self._effect_requests: list[tuple[str, int]] = []

        # 间隔设置 / Interval setting
        self._interval_min_ms: int = 3000
        self._interval_max_ms: int = 8000

        # 随机数生成器 / Random number generator
        self._rng = random.Random()

    # ==================== 状态访问 (只读) / State Access (Read-only) ====================

    @property
    def state(self) -> StateView:
        """
        角色状态视图
        Character state view (read-only)
        """
        if self._state_provider:
            return self._state_provider()

        # 默认状态 / Default state
        return StateView(
            mood=0.5,
            energy=0.5,
            affection=0.5,
            hunger=0.5,
            emotion="neutral",
            emotion_intensity=0.0,
        )

    @property
    def time(self) -> TimeView:
        """
        时间视图
        Time view (read-only)
        """
        now = datetime.now()
        hour = now.hour
        is_night = hour >= 22 or hour < 6
        is_weekend = now.weekday() >= 5

        return TimeView(
            hour=hour,
            minute=now.minute,
            second=now.second,
            weekday=now.weekday(),
            is_night=is_night,
            is_weekend=is_weekend,
        )

    @property
    def interaction(self) -> InteractionView:
        """
        交互统计视图
        Interaction stats view (read-only)
        """
        if self._interaction_provider:
            return self._interaction_provider()

        # 默认值 / Default values
        return InteractionView(
            last_interaction_seconds=0,
            today_interactions=0,
            total_interactions=0,
            consecutive_days=0,
        )

    @property
    def animation(self) -> AnimationView:
        """
        动画状态视图
        Animation state view (read-only)
        """
        if self._animation_provider:
            return self._animation_provider()

        # 默认值 / Default values
        return AnimationView(
            current_animation="idle",
            current_action=None,
            is_playing_action=False,
        )

    # ==================== 动作控制 / Action Control ====================

    def set_interval(self, min_ms: int, max_ms: int) -> None:
        """
        设置随机动作间隔
        Set random action interval

        Args:
            min_ms: 最小间隔（毫秒）/ Minimum interval (ms)
            max_ms: 最大间隔（毫秒）/ Maximum interval (ms)
        """
        if min_ms < 100:
            min_ms = 100
        if max_ms < min_ms:
            max_ms = min_ms

        self._interval_min_ms = min_ms
        self._interval_max_ms = max_ms

    def get_interval(self) -> tuple[int, int]:
        """
        获取当前间隔设置
        Get current interval setting

        Returns:
            (min_ms, max_ms) 元组 / Tuple of (min_ms, max_ms)
        """
        return (self._interval_min_ms, self._interval_max_ms)

    def play_action(self, action_name: str) -> bool:
        """
        请求播放一次性动作
        Request to play one-shot action

        注意：这是一个请求，不保证立即执行。
        Note: This is a request, not guaranteed to execute immediately.

        Args:
            action_name: 动作名称 / Action name

        Returns:
            请求是否被接受 / Whether request was accepted
        """
        if not action_name or not isinstance(action_name, str):
            return False

        self._action_requests.append(action_name)
        logger.debug(f"动作请求: {action_name}")
        return True

    def play_effect(self, effect_name: str, duration_ms: int = 2000) -> bool:
        """
        请求播放特效
        Request to play effect

        Args:
            effect_name: 特效名称 / Effect name
            duration_ms: 持续时间（毫秒）/ Duration (ms)

        Returns:
            请求是否被接受 / Whether request was accepted
        """
        if not effect_name or not isinstance(effect_name, str):
            return False

        self._effect_requests.append((effect_name, duration_ms))
        logger.debug(f"特效请求: {effect_name}, {duration_ms}ms")
        return True

    def get_pending_actions(self) -> list[str]:
        """
        获取并清空待处理的动作请求
        Get and clear pending action requests

        Returns:
            动作请求列表 / List of action requests
        """
        actions = self._action_requests.copy()
        self._action_requests.clear()
        return actions

    def get_pending_effects(self) -> list[tuple[str, int]]:
        """
        获取并清空待处理的特效请求
        Get and clear pending effect requests

        Returns:
            特效请求列表 [(name, duration_ms), ...] / List of effect requests
        """
        effects = self._effect_requests.copy()
        self._effect_requests.clear()
        return effects

    # ==================== 工具函数 / Utility Functions ====================

    def random(self) -> float:
        """
        返回 0.0 ~ 1.0 的随机数
        Return random float between 0.0 and 1.0
        """
        return self._rng.random()

    def random_int(self, min_val: int, max_val: int) -> int:
        """
        返回 [min_val, max_val] 范围内的随机整数
        Return random integer in range [min_val, max_val]
        """
        return self._rng.randint(min_val, max_val)

    def random_choice(self, items: list[Any]) -> Any:
        """
        从列表中随机选择一个元素
        Randomly select an element from list
        """
        if not items:
            return None
        return self._rng.choice(items)

    def log(self, message: str) -> None:
        """
        记录日志（用于调试）
        Log message (for debugging)

        日志会带上脚本标识，方便追踪。
        """
        logger.info(f"[BehaviorScript] {message}")

    # ==================== 内部方法 / Internal Methods ====================

    def _reset_requests(self) -> None:
        """重置请求队列 / Reset request queues"""
        self._action_requests.clear()
        self._effect_requests.clear()

    def _reset_interval(self) -> None:
        """重置间隔设置 / Reset interval setting"""
        self._interval_min_ms = 3000
        self._interval_max_ms = 8000
