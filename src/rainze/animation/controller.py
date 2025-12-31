"""
动画主控制器
Animation Controller

本模块提供动画系统的主控制器，统一管理所有动画层。
This module provides the main animation controller that manages all layers.

职责 / Responsibilities:
- 统一管理3个动画层 / Manage all 3 animation layers
- 处理层间优先级和混合 / Handle layer priority and blending
- 响应情感标签和状态变化 / Respond to emotion tags and state changes
- 提供给GUI的渲染接口 / Provide rendering interface for GUI
- 连接事件总线 / Connect to EventBus
- 执行行为脚本 / Execute behavior scripts

Reference:
    - PRD §0.14: 动画系统架构
    - MOD: .github/prds/modules/MOD-Animation.md §3.1
    - MOD: .github/prds/modules/MOD-Animation-Script.md

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Dict, List, Optional

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QPainter, QPixmap

from rainze.animation.frames import FramePlayer
from rainze.animation.layers import AnimationLayer
from rainze.animation.models import AnimationState, BlendMode

# ⭐ 从 core.contracts 导入统一类型，禁止本模块重复定义
# Import unified types from core.contracts, NO duplicate definitions
from rainze.core.contracts import EmotionTag

if TYPE_CHECKING:
    from rainze.animation.script import BehaviorManager
    from rainze.core.event_bus import EventBus


# 导出列表 / Export list
__all__ = ["AnimationController"]


@dataclass
class LayerInfo:
    """
    层信息数据类
    Layer information dataclass

    Attributes:
        name: 层名称 / Layer name
        index: 层索引 / Layer index
        visible: 是否可见 / Visibility
        blend_mode: 混合模式 / Blend mode
    """

    name: str
    index: int
    visible: bool = True
    blend_mode: BlendMode = BlendMode.NORMAL


class AnimationController(QObject):
    """
    动画主控制器
    Main Animation Controller

    统一管理6个动画层的渲染和状态转换。
    Manages rendering and state transitions for all 6 animation layers.

    6层动画架构 / 6-Layer Architecture:
    - Layer 0: Base (基础层) - 角色主体
    - Layer 1: Idle (待机层) - 呼吸动画
    - Layer 2: Expression (表情层) - 表情变化
    - Layer 3: Action (动作层) - 肢体动作
    - Layer 4: Effect (特效层) - 粒子效果
    - Layer 5: LipSync (口型层) - 嘴型同步

    Signals:
        frame_ready: 新帧准备完成 / New frame is ready (QPixmap)
        state_changed: 动画状态变化 / Animation state changed
        action_completed: 动作播放完成 / Action playback completed

    Attributes:
        _layers: 动画层字典 / Animation layers dict
        _current_state: 当前动画状态 / Current animation state
        _event_bus: 事件总线引用 / EventBus reference
        _render_timer: 渲染定时器 / Render timer
        _fps: 目标帧率 / Target FPS
        _frame_player: 主帧播放器 / Main frame player
        _canvas_size: 画布大小 / Canvas size

    Example:
        >>> controller = AnimationController(event_bus, resource_path="assets")
        >>> controller.frame_ready.connect(window.update_pet_image)
        >>> await controller.initialize()
        >>> controller.set_expression("happy", intensity=0.8)
        >>> controller.play_action("wave")

    Reference:
        PRD §0.14: 动画系统架构
        MOD-Animation.md: 3层动画架构
    """

    # Qt 信号定义 / Qt Signal definitions
    frame_ready = Signal(QPixmap)
    state_changed = Signal(object)  # AnimationState
    action_completed = Signal(str)
    expression_changed = Signal(str, float)  # (expression_name, intensity)

    # 3层系统常量 / 3-layer system constants
    # Layer 0: Background (阴影/背景)
    # Layer 1: Character (角色帧动画)
    # Layer 2: Overlay (特效/粒子)
    LAYER_BACKGROUND = 0
    LAYER_CHARACTER = 1
    LAYER_OVERLAY = 2

    def __init__(
        self,
        event_bus: Optional["EventBus"] = None,
        resource_path: str = "",
        fps: int = 30,
        canvas_size: tuple[int, int] = (256, 256),
        parent: Optional[QObject] = None,
    ) -> None:
        """
        初始化动画控制器
        Initialize animation controller

        Args:
            event_bus: 事件总线实例 / EventBus instance
            resource_path: 动画资源根目录 / Animation resource root path
            fps: 目标帧率 / Target FPS (default: 30)
            canvas_size: 画布大小 / Canvas size (width, height)
            parent: 父 QObject / Parent QObject
        """
        super().__init__(parent)

        # 依赖注入 / Dependency injection
        self._event_bus = event_bus
        self._resource_path = Path(resource_path) if resource_path else None

        # 渲染参数 / Rendering parameters
        self._fps = fps
        self._frame_interval_ms = 1000 // fps
        self._canvas_size = canvas_size

        # 动画状态 / Animation state
        self._current_state = AnimationState.IDLE
        self._previous_state = AnimationState.IDLE

        # 3层管理 / 3-layer management
        # Layer 0: Background, Layer 1: Character, Layer 2: Overlay
        self._layers: Dict[int, Optional[AnimationLayer]] = {
            self.LAYER_BACKGROUND: None,  # 阴影/背景
            self.LAYER_CHARACTER: None,   # 角色帧动画
            self.LAYER_OVERLAY: None,     # 特效/粒子
        }
        self._layer_pixmaps: Dict[int, Optional[QPixmap]] = {}

        # 帧播放器（用于 Character 层）/ Frame player (for Character layer)
        self._frame_player = FramePlayer(self)
        self._frame_player.frame_changed.connect(self._on_frame_changed)
        self._frame_player.playback_finished.connect(self._on_playback_finished)

        # 渲染定时器 / Render timer
        self._render_timer = QTimer(self)
        self._render_timer.timeout.connect(self._on_render_tick)

        # 表情状态 / Expression state
        self._current_expression: str = "idle"
        self._expression_intensity: float = 0.5

        # 当前动作 / Current action
        self._current_action: Optional[str] = None
        self._action_on_complete: Optional[Callable[[], None]] = None

        # 时间跟踪 / Time tracking
        self._last_update_time_ms: int = 0

        # 初始化标志 / Initialization flag
        self._initialized: bool = False

        # ========== 随机动作系统 / Random Action System ==========
        # 当前基础动画名 / Current base animation name
        self._base_animation: str = "idle"
        # 是否正在播放随机动作 / Whether playing random action
        self._playing_random_action: bool = False
        # 随机动作定时器 / Random action timer
        self._random_action_timer = QTimer(self)
        self._random_action_timer.timeout.connect(self._on_random_action_timer)
        # 随机动作配置缓存 / Random action config cache
        self._random_action_config: Optional[Dict] = None

        # ========== 行为脚本系统 / Behavior Script System ==========
        self._behavior_manager: Optional["BehaviorManager"] = None
        # 状态更新定时器（每秒调用脚本的 on_state_update）
        self._state_update_timer = QTimer(self)
        self._state_update_timer.timeout.connect(self._on_state_update_timer)

    # ==================== 初始化 / Initialization ====================

    async def initialize(self) -> None:
        """
        异步初始化
        Async initialization

        加载动画资源清单、初始化各层、订阅事件。
        Loads animation manifest, initializes layers, subscribes to events.
        """
        if self._initialized:
            return

        # 订阅事件总线事件 / Subscribe to EventBus events
        if self._event_bus:
            self._subscribe_events()

        # 加载行为脚本 / Load behavior script
        self._load_behavior_script()

        # 启动状态更新定时器（每秒一次）/ Start state update timer (once per second)
        self._state_update_timer.start(1000)

        # 标记已初始化 / Mark as initialized
        self._initialized = True

    def _load_behavior_script(self) -> None:
        """
        加载行为脚本
        Load behavior script
        """
        import logging
        logger = logging.getLogger(__name__)

        if not self._resource_path:
            return

        behavior_path = self._resource_path / "behavior.py"
        if not behavior_path.exists():
            logger.info(f"未找到行为脚本: {behavior_path}")
            return

        try:
            from rainze.animation.script import BehaviorManager

            self._behavior_manager = BehaviorManager()
            if self._behavior_manager.load_script(behavior_path):
                logger.info("行为脚本系统已启用")
            else:
                self._behavior_manager = None

        except Exception as e:
            logger.warning(f"加载行为脚本失败: {e}")
            self._behavior_manager = None

    def _on_state_update_timer(self) -> None:
        """
        状态更新定时器回调
        State update timer callback
        """
        if self._behavior_manager and self._behavior_manager.script_enabled:
            self._behavior_manager.on_state_update()

    def _subscribe_events(self) -> None:
        """
        订阅事件总线事件（内部方法）
        Subscribe to EventBus events (internal method)
        """
        # 事件订阅将在实现具体事件类后添加
        # Event subscriptions will be added after event classes are implemented
        pass

    # ==================== 状态控制 / State Control ====================

    def get_current_state(self) -> AnimationState:
        """
        获取当前动画状态
        Get current animation state

        Returns:
            当前动画状态 / Current animation state
        """
        return self._current_state

    def transition_to(
        self,
        target_state: AnimationState,
        transition_duration_ms: int = 200,
    ) -> None:
        """
        执行状态转换
        Execute state transition

        Args:
            target_state: 目标状态 / Target state
            transition_duration_ms: 过渡时长(毫秒) / Transition duration in ms
        """
        if target_state == self._current_state:
            return

        self._previous_state = self._current_state
        self._current_state = target_state

        # 发出状态变化信号 / Emit state changed signal
        self.state_changed.emit(target_state)

    # ==================== 层控制 / Layer Control ====================

    def get_layer(self, layer_index: int) -> Optional[AnimationLayer]:
        """
        获取指定层
        Get specific layer

        Args:
            layer_index: 层索引 (0-5) / Layer index

        Returns:
            动画层实例或 None / Animation layer or None
        """
        return self._layers.get(layer_index)

    def set_layer(self, layer_index: int, layer: AnimationLayer) -> None:
        """
        设置指定层
        Set specific layer

        Args:
            layer_index: 层索引 (0-5) / Layer index
            layer: 动画层实例 / Animation layer instance
        """
        if 0 <= layer_index <= 5:
            self._layers[layer_index] = layer

    def set_layer_visible(self, layer_index: int, visible: bool) -> None:
        """
        设置层可见性
        Set layer visibility

        Args:
            layer_index: 层索引 / Layer index
            visible: 是否可见 / Whether visible
        """
        layer = self._layers.get(layer_index)
        if layer:
            layer.visible = visible

    def get_layer_info(self, layer_index: int) -> Optional[LayerInfo]:
        """
        获取层信息
        Get layer information

        Args:
            layer_index: 层索引 / Layer index

        Returns:
            层信息或 None / LayerInfo or None
        """
        layer = self._layers.get(layer_index)
        if layer:
            return LayerInfo(
                name=layer.name,
                index=layer.index,
                visible=layer.visible,
                blend_mode=layer.blend_mode,
            )
        return None

    # ==================== 表情控制 / Expression Control ====================

    def set_expression(
        self,
        emotion_tag: str,
        intensity: float = 0.5,
        duration_ms: Optional[int] = None,
    ) -> None:
        """
        设置表情
        Set expression

        根据情感标签设置角色表情。
        Sets character expression based on emotion tag.

        Args:
            emotion_tag: 情感标签 / Emotion tag (happy, sad, angry, shy, etc.)
            intensity: 强度 (0.0-1.0) / Intensity
            duration_ms: 持续时间，None表示持续到下次变更
                         Duration in ms, None for indefinite
        """
        # 验证强度范围 / Validate intensity range
        intensity = max(0.0, min(1.0, intensity))

        # 更新表情状态 / Update expression state
        self._current_expression = emotion_tag
        self._expression_intensity = intensity

        # 发出表情变化信号 / Emit expression changed signal
        self.expression_changed.emit(emotion_tag, intensity)

        # 通知行为脚本 / Notify behavior script
        if self._behavior_manager and self._behavior_manager.script_enabled:
            self._behavior_manager.on_emotion_change(emotion_tag, intensity)

        # 切换到表情反应状态 / Transition to reacting state
        if emotion_tag != "neutral":
            self.transition_to(AnimationState.REACTING)

    def set_animation(
        self,
        animation_name: str,
        variant: str = "default",
        is_action: bool = False,
    ) -> None:
        """
        切换动画集
        Switch animation set

        切换整个动画集（如 idle, thinking, happy 等）。
        Switches entire animation set (e.g., idle, thinking, happy).

        动画类型 / Animation types:
        - loop: 持续循环的基础动画，可配置随机插入动作
        - action: 一次性播放的动作，完成后返回基础动画
        - triggered: 由事件触发的动画，需要手动切换回基础动画

        Args:
            animation_name: 动画集名称 / Animation set name
            variant: 变体名称 / Variant name
            is_action: 是否是随机动作（内部使用）/ Whether this is a random action
        """
        import json
        import logging
        logger = logging.getLogger(__name__)

        # 延迟加载行为脚本（如果尚未加载）
        # Lazy load behavior script if not loaded yet
        if self._behavior_manager is None and self._resource_path:
            self._load_behavior_script()

        # 构建动画路径 / Build animation path
        animation_path = Path(self._resource_path) / animation_name / variant

        if not animation_path.exists():
            logger.warning(f"动画路径不存在: {animation_path}")
            return

        logger.info(f"切换动画: {animation_name}/{variant}")

        # 停止随机动作定时器（切换动画时重置）
        # Stop random action timer when switching animation
        if not is_action:
            self._random_action_timer.stop()
            self._playing_random_action = False

        # 尝试加载清单文件 / Try to load manifest file
        manifest_path = Path(self._resource_path) / "manifest.json"
        manifest_config = None

        if manifest_path.exists():
            try:
                with open(manifest_path, encoding="utf-8") as f:
                    manifest = json.load(f)
                    manifest_config = manifest.get("animations", {}).get(animation_name)
            except Exception as e:
                logger.warning(f"加载清单文件失败: {e}")

        # 创建帧序列 / Create frame sequence
        from rainze.animation.frames.sequence import FrameSequence
        from rainze.animation.models import AnimationFrame

        # 从 manifest 的 loop 字段判断是否循环 / Use manifest's loop field
        should_loop = manifest_config.get("loop", True) if manifest_config else True

        sequence = FrameSequence(
            name=f"{animation_name}_{variant}",
            loop=should_loop,
        )

        # 如果有清单配置，按配置加载帧 / If manifest config exists, load frames per config
        if manifest_config and "frames" in manifest_config:
            frame_configs = manifest_config["frames"]

            for frame_cfg in frame_configs:
                frame_file = animation_path / frame_cfg["file"]
                duration_ms = frame_cfg.get("duration_ms", int(1000 / self._fps))

                if frame_file.exists():
                    pixmap = QPixmap(str(frame_file))
                    if not pixmap.isNull():
                        frame = AnimationFrame(
                            pixmap=pixmap,
                            duration_ms=duration_ms,
                        )
                        sequence.add_frame(frame)
                else:
                    logger.warning(f"帧文件不存在: {frame_file}")

            logger.info(f"从清单加载动画: loop={should_loop}, 帧数={len(sequence.frames)}")
        else:
            # 回退到自动加载所有帧 / Fallback to auto-load all frames
            frame_files = sorted(animation_path.glob("frame_*.png"))

            if not frame_files:
                logger.warning(f"动画目录为空: {animation_path}")
                return

            # 计算每帧时长（默认2秒总时长）/ Calculate frame duration (default 2s total)
            default_total_ms = 2000
            frame_duration = default_total_ms // len(frame_files) if frame_files else 100

            for frame_file in frame_files:
                pixmap = QPixmap(str(frame_file))
                if not pixmap.isNull():
                    frame = AnimationFrame(
                        pixmap=pixmap,
                        duration_ms=frame_duration,
                    )
                    sequence.add_frame(frame)

        if sequence.is_empty:
            logger.warning(f"未能加载任何帧: {animation_path}")
            return

        # 设置到帧播放器 / Set to frame player
        self._frame_player.set_sequence(sequence, auto_play=True)

        logger.info(f"动画已切换: {sequence.name}, 共 {len(sequence.frames)} 帧, 总时长 {sequence.total_duration_ms}ms, loop={should_loop}")

        # 处理随机动作系统 / Handle random action system
        # 仅当基础循环动画时启用 / Only enable for base loop animation
        if not is_action and should_loop:
            # 保存基础动画名 / Save base animation name
            self._base_animation = animation_name

            # 优先使用行为脚本 / Prefer behavior script
            if self._behavior_manager and self._behavior_manager.script_enabled:
                # 启动随机动作定时器 / Start random action timer
                self._schedule_next_random_action()
                logger.info("随机动作已启用 (脚本模式)")
            # 回退到 JSON 配置 / Fallback to JSON config
            elif manifest_config and "random_actions" in manifest_config:
                random_cfg = manifest_config["random_actions"]
                if random_cfg.get("enabled", False):
                    self._random_action_config = random_cfg
                    # 启动随机动作定时器 / Start random action timer
                    self._schedule_next_random_action()
                    logger.info(f"随机动作已启用 (JSON模式): actions={random_cfg.get('actions', [])}")

    def _schedule_next_random_action(self) -> None:
        """
        调度下一个随机动作
        Schedule next random action
        """
        import random

        # 优先使用行为脚本的间隔设置 / Prefer behavior script interval
        if self._behavior_manager and self._behavior_manager.script_enabled:
            min_interval, max_interval = self._behavior_manager.get_current_interval()
        elif self._random_action_config:
            min_interval = self._random_action_config.get("min_interval_ms", 3000)
            max_interval = self._random_action_config.get("max_interval_ms", 8000)
        else:
            return

        # 随机等待时间 / Random wait time
        wait_ms = random.randint(min_interval, max_interval)

        self._random_action_timer.start(wait_ms)

    def _on_random_action_timer(self) -> None:
        """
        随机动作定时器回调
        Random action timer callback
        """
        import logging
        import random
        logger = logging.getLogger(__name__)

        self._random_action_timer.stop()

        # 如果正在播放触发动画，跳过 / Skip if playing triggered animation
        if self._current_state != AnimationState.IDLE:
            self._schedule_next_random_action()
            return

        # 获取可用动作列表 / Get available actions
        actions: list[str] = []

        # 优先使用行为脚本 / Prefer behavior script
        if self._behavior_manager and self._behavior_manager.script_enabled:
            actions = self._behavior_manager.get_random_actions()
        elif self._random_action_config:
            actions = self._random_action_config.get("actions", [])

        if not actions:
            self._schedule_next_random_action()
            return

        # 随机选择一个动作 / Randomly select an action
        action_name = random.choice(actions)
        logger.info(f"播放随机动作: {action_name}")

        # 标记正在播放随机动作 / Mark as playing random action
        self._playing_random_action = True
        self._current_action = action_name

        # 播放动作动画 / Play action animation
        self.set_animation(action_name, is_action=True)

    def parse_emotion_tag(self, response_text: str) -> Optional[EmotionTag]:
        """
        从响应文本中解析情感标签
        Parse emotion tag from response text

        解析格式 / Parse format: [EMOTION:tag:intensity]

        Args:
            response_text: AI响应文本 / AI response text

        Returns:
            解析后的情感标签，未找到返回 None
            Parsed EmotionTag, None if not found
        """
        return EmotionTag.parse(response_text)

    def apply_emotion_tag(self, tag: EmotionTag) -> None:
        """
        应用情感标签到动画系统
        Apply emotion tag to animation system

        根据 intensity 自动选择表情和特效：
        - intensity < 0.3 → 轻微表情
        - 0.3 <= intensity < 0.7 → 标准表情
        - intensity >= 0.7 → 夸张表情 + 特效

        Args:
            tag: 解析后的情感标签 / Parsed EmotionTag
        """
        # 设置表情 / Set expression
        self.set_expression(tag.tag, tag.intensity)

        # 高强度时播放特效 / Play effect for high intensity
        if tag.intensity >= 0.7:
            self._play_emotion_effect(tag.tag)

    def _play_emotion_effect(self, emotion_tag: str) -> None:
        """
        播放情感特效（内部方法）
        Play emotion effect (internal method)

        Args:
            emotion_tag: 情感标签 / Emotion tag
        """
        # 情感到特效的映射 / Emotion to effect mapping
        effect_mapping = {
            "happy": "sparkle",
            "excited": "stars",
            "sad": "tear_drop",
            "angry": "anger_mark",
            "shy": "heart",
        }

        effect_name = effect_mapping.get(emotion_tag)
        if effect_name:
            self.play_effect(effect_name)

    def get_current_expression(self) -> tuple[str, float]:
        """
        获取当前表情
        Get current expression

        Returns:
            (表情名称, 强度) / (expression name, intensity)
        """
        return (self._current_expression, self._expression_intensity)

    # ==================== 动作控制 / Action Control ====================

    def play_action(
        self,
        action_name: str,
        on_complete: Optional[Callable[[], None]] = None,
    ) -> bool:
        """
        播放动作
        Play action

        动作播放完成后自动返回 Idle 状态。
        Automatically returns to Idle after action completes.

        Args:
            action_name: 动作名称 / Action name (wave, jump, eat, sleep, etc.)
            on_complete: 完成回调 / Completion callback

        Returns:
            是否成功开始播放 / Whether playback started successfully
        """
        # 记录当前动作 / Record current action
        self._current_action = action_name
        self._action_on_complete = on_complete

        # 切换到动作状态 / Transition to acting state
        self.transition_to(AnimationState.ACTING)

        # 实际的动作播放将在层实现后添加
        # Actual action playback will be added after layer implementation
        return True

    def stop_action(self) -> None:
        """
        停止当前动作，返回 Idle
        Stop current action, return to Idle
        """
        self._current_action = None
        self._action_on_complete = None
        self.transition_to(AnimationState.IDLE)

    def on_user_interaction(self, interaction_type: str) -> None:
        """
        用户交互回调
        User interaction callback

        通知行为脚本用户交互事件。
        Notifies behavior script of user interaction events.

        Args:
            interaction_type: 交互类型 / Interaction type
                - "click": 单击
                - "double_click": 双击
                - "drag_start": 开始拖拽
                - "drag_end": 结束拖拽
                - "pet": 抚摸
                - "chat": 聊天输入
        """
        if self._behavior_manager and self._behavior_manager.script_enabled:
            self._behavior_manager.on_interaction(interaction_type)

    # ==================== 特效控制 / Effect Control ====================

    def play_effect(
        self,
        effect_name: str,
        duration_ms: int = 2000,
    ) -> None:
        """
        播放特效
        Play effect

        Args:
            effect_name: 特效名称 / Effect name
            duration_ms: 持续时间 / Duration in ms
        """
        # 特效播放将在 EffectLayer 实现后添加
        # Effect playback will be added after EffectLayer implementation
        pass

    def stop_effect(self, effect_name: Optional[str] = None) -> None:
        """
        停止特效
        Stop effect

        Args:
            effect_name: 特效名称，None 停止所有 / Effect name, None for all
        """
        pass

    # ==================== 口型同步 / Lip Sync ====================

    def start_lipsync(self, audio_data: bytes) -> None:
        """
        开始口型同步
        Start lip sync

        分析音频振幅，实时控制嘴型。
        Analyzes audio amplitude for real-time mouth shape control.

        Args:
            audio_data: 音频数据 (WAV格式) / Audio data (WAV format)
        """
        self.transition_to(AnimationState.TALKING)
        # 口型同步将在 LipSyncManager 实现后添加
        # Lip sync will be added after LipSyncManager implementation

    def start_text_lipsync(self, text: str, duration_ms: int) -> None:
        """
        基于文本的口型同步
        Text-based lip sync

        不使用 TTS 时，根据文本长度模拟口型动画。
        Simulates mouth animation based on text length without TTS.

        Args:
            text: 说话文本 / Speech text
            duration_ms: 预估持续时间 / Estimated duration in ms
        """
        self.transition_to(AnimationState.TALKING)
        # 文本口型同步将在 LipSyncManager 实现后添加
        # Text lip sync will be added after LipSyncManager implementation

    def stop_lipsync(self) -> None:
        """
        停止口型同步
        Stop lip sync
        """
        if self._current_state == AnimationState.TALKING:
            self.transition_to(AnimationState.IDLE)

    # ==================== 渲染 / Rendering ====================

    def render_frame(self) -> QPixmap:
        """
        渲染当前帧
        Render current frame

        合成3层动画，返回最终图像。
        Composites all 3 layers into final image.

        层顺序 / Layer order:
        - Layer 0: Background (阴影/背景)
        - Layer 1: Character (角色帧动画)
        - Layer 2: Overlay (特效/粒子)

        Returns:
            合成后的帧图像 / Composited frame image
        """
        # 创建画布 / Create canvas
        canvas = QPixmap(self._canvas_size[0], self._canvas_size[1])
        canvas.fill()  # 透明填充 / Fill transparent

        painter = QPainter(canvas)

        # 按层索引顺序合成（0 在底，2 在顶）
        # Composite in layer index order (0 at bottom, 2 on top)
        for layer_index in [self.LAYER_BACKGROUND, self.LAYER_CHARACTER, self.LAYER_OVERLAY]:
            layer = self._layers.get(layer_index)
            if layer and layer.visible:
                frame = layer.get_current_frame()
                if frame and not frame.isNull():
                    # 应用混合模式和不透明度
                    # Apply blend mode and opacity
                    painter.setOpacity(layer.opacity)
                    painter.drawPixmap(0, 0, frame)

        painter.end()
        return canvas

    def start_render_loop(self) -> None:
        """
        启动渲染循环
        Start render loop
        """
        if not self._render_timer.isActive():
            self._render_timer.start(self._frame_interval_ms)

    def stop_render_loop(self) -> None:
        """
        停止渲染循环
        Stop render loop
        """
        self._render_timer.stop()

    def _on_render_tick(self) -> None:
        """
        渲染定时器回调（内部方法）
        Render timer callback (internal method)
        """
        # 计算 delta 时间 / Calculate delta time
        import time

        current_time_ms = int(time.time() * 1000)
        delta_ms = (
            self._frame_interval_ms
            if self._last_update_time_ms == 0
            else current_time_ms - self._last_update_time_ms
        )
        self._last_update_time_ms = current_time_ms

        # 更新所有层 / Update all layers
        for layer in self._layers.values():
            if layer:
                layer.tick(delta_ms)

        # 更新帧播放器 / Update frame player
        self._frame_player.update(delta_ms)

        # 优先使用帧播放器的当前帧，否则使用层合成
        # Prefer frame player's current frame, fallback to layer composite
        current_pixmap = self._frame_player.get_current_pixmap()
        if current_pixmap and not current_pixmap.isNull():
            self.frame_ready.emit(current_pixmap)
        else:
            # 渲染并发出信号 / Render and emit signal
            frame = self.render_frame()
            self.frame_ready.emit(frame)

    def _on_frame_changed(self, pixmap: QPixmap, frame_index: int) -> None:
        """
        帧变化回调（内部方法）
        Frame changed callback (internal method)

        Args:
            pixmap: 新帧图像 / New frame pixmap
            frame_index: 帧索引 / Frame index
        """
        # 发射帧更新信号给 GUI / Emit frame update signal to GUI
        self.frame_ready.emit(pixmap)

    def _on_playback_finished(self) -> None:
        """
        播放完成回调（内部方法）
        Playback finished callback (internal method)
        """
        import logging
        logger = logging.getLogger(__name__)

        # 如果是随机动作播放完成，返回基础动画
        # If random action finished, return to base animation
        if self._playing_random_action:
            logger.info(f"随机动作完成: {self._current_action}, 返回基础动画: {self._base_animation}")
            self._playing_random_action = False
            self._current_action = None

            # 返回基础动画 / Return to base animation
            self.set_animation(self._base_animation)
            return

        # 如果是动作播放完成，触发回调并返回 Idle
        # If action playback finished, trigger callback and return to Idle
        if self._current_state == AnimationState.ACTING:
            action_name = self._current_action
            callback = self._action_on_complete

            self._current_action = None
            self._action_on_complete = None

            # 发出动作完成信号 / Emit action completed signal
            if action_name:
                self.action_completed.emit(action_name)

            # 触发完成回调 / Trigger completion callback
            if callback:
                callback()

            # 返回 Idle 状态 / Return to Idle state
            self.transition_to(AnimationState.IDLE)

    # ==================== 资源管理 / Resource Management ====================

    def preload_animations(self, categories: List[str]) -> None:
        """
        预加载动画资源
        Preload animation resources

        Args:
            categories: 要预加载的类别列表 / Categories to preload
        """
        # 资源预加载将在 ResourceLoader 实现后添加
        # Resource preloading will be added after ResourceLoader implementation
        pass

    def change_outfit(self, outfit_name: str) -> bool:
        """
        切换服装
        Change outfit

        Args:
            outfit_name: 服装名称 / Outfit name

        Returns:
            是否成功切换 / Whether change was successful
        """
        # 服装切换将在完整实现时添加
        # Outfit change will be added in full implementation
        return False

    # ==================== 清理 / Cleanup ====================

    def cleanup(self) -> None:
        """
        清理资源
        Cleanup resources
        """
        self.stop_render_loop()
        self._frame_player.stop()

    def __repr__(self) -> str:
        """
        字符串表示
        String representation
        """
        return (
            f"<AnimationController "
            f"state={self._current_state.name} "
            f"fps={self._fps} "
            f"initialized={self._initialized}>"
        )
