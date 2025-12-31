"""
行为管理器
Behavior Manager

管理行为脚本的加载、执行和缓存。
Manages behavior script loading, execution and caching.

Reference:
    MOD-Animation-Script.md §5: 集成设计
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Callable

from rainze.animation.script.context import ScriptContext, StateView, AnimationView, InteractionView
from rainze.sandbox import SandboxExecutor, ScriptError

logger = logging.getLogger(__name__)


class BehaviorManager:
    """
    行为管理器
    Behavior Manager

    管理行为脚本的加载、执行和缓存。
    Manages behavior script loading, execution and caching.

    功能 / Features:
    - 加载 behavior.py 脚本
    - 提供脚本上下文
    - 缓存脚本执行结果
    - 优雅降级（脚本失败时使用默认值）

    Attributes:
        _executor: 沙盒执行器
        _context: 脚本上下文
        _script_enabled: 脚本是否启用
        _cache_ttl: 缓存有效期（秒）
        _cached_actions: 缓存的动作列表
        _cache_valid_until: 缓存过期时间

    Example:
        >>> manager = BehaviorManager()
        >>> manager.load_script(Path("assets/animations/behavior.py"))
        >>> actions = manager.get_random_actions()
        >>> manager.on_emotion_change("happy", 0.8)
    """

    # 默认动作列表（脚本未加载或失败时使用）
    DEFAULT_ACTIONS = ["idle"]
    DEFAULT_INTERVAL = (3000, 8000)

    def __init__(
        self,
        state_provider: Callable[[], StateView] | None = None,
        animation_provider: Callable[[], AnimationView] | None = None,
        interaction_provider: Callable[[], InteractionView] | None = None,
        cache_ttl: float = 1.0,
    ) -> None:
        """
        初始化行为管理器
        Initialize behavior manager

        Args:
            state_provider: 状态提供函数 / State provider function
            animation_provider: 动画状态提供函数 / Animation state provider
            interaction_provider: 交互统计提供函数 / Interaction stats provider
            cache_ttl: 缓存有效期（秒）/ Cache TTL in seconds
        """
        # 创建沙盒执行器 / Create sandbox executor
        self._executor = SandboxExecutor(timeout_ms=100)

        # 创建脚本上下文 / Create script context
        self._context = ScriptContext(
            state_provider=state_provider,
            animation_provider=animation_provider,
            interaction_provider=interaction_provider,
        )

        # 脚本状态 / Script state
        self._script_enabled = False
        self._script_path: Path | None = None

        # 缓存 / Cache
        self._cache_ttl = cache_ttl
        self._cached_actions: list[str] = []
        self._cached_interval: tuple[int, int] = self.DEFAULT_INTERVAL
        self._cache_valid_until: float = 0

    def load_script(self, script_path: Path) -> bool:
        """
        加载行为脚本
        Load behavior script

        Args:
            script_path: 脚本文件路径 / Script file path

        Returns:
            是否加载成功 / Whether loading succeeded
        """
        if not script_path.exists():
            logger.info(f"行为脚本不存在: {script_path}")
            self._script_enabled = False
            return False

        try:
            script_code = script_path.read_text(encoding="utf-8")
            self._executor.load_script(script_code, filename=str(script_path))

            # 注入上下文 / Inject context
            self._executor.inject_context("ctx", self._context)

            self._script_enabled = True
            self._script_path = script_path
            logger.info(f"行为脚本加载成功: {script_path}")

            # 列出可用函数 / List available functions
            functions = self._executor.get_available_functions()
            logger.info(f"可用函数: {functions}")

            return True

        except ScriptError as e:
            logger.error(f"行为脚本加载失败: {e}")
            self._script_enabled = False
            return False

    def reload_script(self) -> bool:
        """
        重新加载脚本（热重载）
        Reload script (hot reload)

        Returns:
            是否重载成功 / Whether reload succeeded
        """
        if self._script_path:
            self._executor.reset()
            self._invalidate_cache()
            return self.load_script(self._script_path)
        return False

    @property
    def script_enabled(self) -> bool:
        """脚本是否启用 / Whether script is enabled"""
        return self._script_enabled

    # ==================== 脚本函数调用 / Script Function Calls ====================

    def get_random_actions(self) -> list[str]:
        """
        获取随机动作列表
        Get random action list

        调用脚本的 get_random_actions(ctx) 函数。
        Calls script's get_random_actions(ctx) function.

        Returns:
            动作名称列表 / List of action names
        """
        # 检查缓存 / Check cache
        now = time.time()
        if now < self._cache_valid_until:
            return self._cached_actions

        # 重置上下文 / Reset context
        self._context._reset_requests()
        self._context._reset_interval()

        if not self._script_enabled:
            return self.DEFAULT_ACTIONS

        try:
            # 调用脚本函数 / Call script function
            result = self._executor.call_function_safe(
                "get_random_actions",
                self._context,
                default=self.DEFAULT_ACTIONS,
            )

            # 验证返回值 / Validate return value
            if isinstance(result, list) and all(isinstance(a, str) for a in result):
                self._cached_actions = result
            else:
                logger.warning(f"get_random_actions 返回值无效: {result}")
                self._cached_actions = self.DEFAULT_ACTIONS

            # 获取间隔设置 / Get interval setting
            self._cached_interval = self._context.get_interval()

            # 更新缓存时间 / Update cache time
            self._cache_valid_until = now + self._cache_ttl

            return self._cached_actions

        except Exception as e:
            logger.warning(f"get_random_actions 执行失败: {e}")
            return self.DEFAULT_ACTIONS

    def get_current_interval(self) -> tuple[int, int]:
        """
        获取当前动作间隔
        Get current action interval

        Returns:
            (min_ms, max_ms) 元组 / Tuple of (min_ms, max_ms)
        """
        # 确保缓存有效 / Ensure cache is valid
        if time.time() >= self._cache_valid_until:
            self.get_random_actions()

        return self._cached_interval

    def on_emotion_change(self, emotion: str, intensity: float) -> None:
        """
        情感变化回调
        Emotion change callback

        调用脚本的 on_emotion_change(ctx, emotion, intensity) 函数。

        Args:
            emotion: 情感标签 / Emotion tag
            intensity: 强度 / Intensity
        """
        if not self._script_enabled:
            return

        self._context._reset_requests()

        try:
            self._executor.call_function_safe(
                "on_emotion_change",
                self._context,
                emotion,
                intensity,
                default=None,
            )

            # 处理请求 / Process requests
            self._process_pending_requests()

        except Exception as e:
            logger.warning(f"on_emotion_change 执行失败: {e}")

    def on_interaction(self, interaction_type: str) -> None:
        """
        用户交互回调
        User interaction callback

        调用脚本的 on_interaction(ctx, interaction_type) 函数。

        Args:
            interaction_type: 交互类型 / Interaction type
                - "click": 单击
                - "double_click": 双击
                - "drag_start": 开始拖拽
                - "drag_end": 结束拖拽
                - "pet": 抚摸
                - "chat": 聊天输入
        """
        if not self._script_enabled:
            return

        self._context._reset_requests()

        try:
            self._executor.call_function_safe(
                "on_interaction",
                self._context,
                interaction_type,
                default=None,
            )

            # 处理请求 / Process requests
            self._process_pending_requests()

        except Exception as e:
            logger.warning(f"on_interaction 执行失败: {e}")

    def on_state_update(self) -> None:
        """
        状态更新回调
        State update callback

        调用脚本的 on_state_update(ctx) 函数。
        应该每秒调用一次。
        """
        if not self._script_enabled:
            return

        if not self._executor.has_function("on_state_update"):
            return

        self._context._reset_requests()

        try:
            self._executor.call_function_safe(
                "on_state_update",
                self._context,
                default=None,
            )

            # 处理请求 / Process requests
            self._process_pending_requests()

        except Exception as e:
            logger.warning(f"on_state_update 执行失败: {e}")

    def get_idle_animation(self) -> str:
        """
        获取待机动画名
        Get idle animation name

        调用脚本的 get_idle_animation(ctx) 函数。

        Returns:
            待机动画名称 / Idle animation name
        """
        if not self._script_enabled:
            return "idle"

        if not self._executor.has_function("get_idle_animation"):
            return "idle"

        try:
            result = self._executor.call_function_safe(
                "get_idle_animation",
                self._context,
                default="idle",
            )

            if isinstance(result, str):
                return result

            return "idle"

        except Exception as e:
            logger.warning(f"get_idle_animation 执行失败: {e}")
            return "idle"

    # ==================== 内部方法 / Internal Methods ====================

    def _process_pending_requests(self) -> None:
        """
        处理脚本产生的请求
        Process requests generated by script
        """
        # 获取动作请求 / Get action requests
        actions = self._context.get_pending_actions()
        for action in actions:
            logger.info(f"脚本请求动作: {action}")
            # TODO: 发送到 AnimationController

        # 获取特效请求 / Get effect requests
        effects = self._context.get_pending_effects()
        for effect_name, duration in effects:
            logger.info(f"脚本请求特效: {effect_name}, {duration}ms")
            # TODO: 发送到 AnimationController

    def _invalidate_cache(self) -> None:
        """使缓存失效 / Invalidate cache"""
        self._cache_valid_until = 0
        self._cached_actions = []
        self._cached_interval = self.DEFAULT_INTERVAL

    def get_pending_action_requests(self) -> list[str]:
        """
        获取待处理的动作请求
        Get pending action requests

        Returns:
            动作请求列表 / List of action requests
        """
        return self._context.get_pending_actions()

    def get_pending_effect_requests(self) -> list[tuple[str, int]]:
        """
        获取待处理的特效请求
        Get pending effect requests

        Returns:
            特效请求列表 / List of effect requests
        """
        return self._context.get_pending_effects()
