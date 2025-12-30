"""
动画主控制器
Animation Controller

本模块提供动画系统的主控制器，统一管理所有动画层。
This module provides the main animation controller that manages all layers.

职责 / Responsibilities:
- 统一管理6个动画层 / Manage all 6 animation layers
- 处理层间优先级和混合 / Handle layer priority and blending
- 响应情感标签和状态变化 / Respond to emotion tags and state changes
- 提供给GUI的渲染接口 / Provide rendering interface for GUI
- 连接事件总线 / Connect to EventBus

Reference:
    - PRD §0.14: 动画系统架构
    - MOD: .github/prds/modules/MOD-Animation.md §3.1

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
    """

    # Qt 信号定义 / Qt Signal definitions
    frame_ready = Signal(QPixmap)
    state_changed = Signal(object)  # AnimationState
    action_completed = Signal(str)
    expression_changed = Signal(str, float)  # (expression_name, intensity)

    # 层索引常量 / Layer index constants
    LAYER_BASE = 0
    LAYER_IDLE = 1
    LAYER_EXPRESSION = 2
    LAYER_ACTION = 3
    LAYER_EFFECT = 4
    LAYER_LIPSYNC = 5

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

        # 层管理 / Layer management
        self._layers: Dict[int, Optional[AnimationLayer]] = {
            self.LAYER_BASE: None,
            self.LAYER_IDLE: None,
            self.LAYER_EXPRESSION: None,
            self.LAYER_ACTION: None,
            self.LAYER_EFFECT: None,
            self.LAYER_LIPSYNC: None,
        }
        self._layer_pixmaps: Dict[int, Optional[QPixmap]] = {}

        # 帧播放器 / Frame player
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

        # 标记已初始化 / Mark as initialized
        self._initialized = True

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

        # 切换到表情反应状态 / Transition to reacting state
        if emotion_tag != "neutral":
            self.transition_to(AnimationState.REACTING)

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

        合成6层动画，返回最终图像。
        Composites all 6 layers into final image.

        Returns:
            合成后的帧图像 / Composited frame image
        """
        # 创建画布 / Create canvas
        canvas = QPixmap(self._canvas_size[0], self._canvas_size[1])
        canvas.fill()  # 透明填充 / Fill transparent

        painter = QPainter(canvas)

        # 按层索引顺序合成（0 在底，5 在顶）
        # Composite in layer index order (0 at bottom, 5 on top)
        for layer_index in range(6):
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
        pass

    def _on_playback_finished(self) -> None:
        """
        播放完成回调（内部方法）
        Playback finished callback (internal method)
        """
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
