"""
状态管理器
State Manager

统一管理所有状态的入口，协调各子状态管理器。
Unified entry point for all state management, coordinates sub-managers.

Reference:
    - MOD-State.md §3.1: StateManager
    - PRD §0.6a: 状态同步机制

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional

from rainze.state.attributes import (
    AffinityConfig,
    AffinityManager,
    EnergyConfig,
    EnergyManager,
)
from rainze.state.emotion import EmotionStateMachine, MoodState
from rainze.state.emotion.state_machine import EmotionConfig
from rainze.state.models.events import (
    MoodTransitionEvent,
    StateChangedEvent,
    StateChangeType,
)


@dataclass
class StateConfig:
    """
    状态系统总配置
    State system overall configuration

    Attributes:
        emotion: 情绪配置 / Emotion configuration
        energy: 能量配置 / Energy configuration
        affinity: 好感度配置 / Affinity configuration
    """

    emotion: EmotionConfig = field(default_factory=EmotionConfig)
    energy: EnergyConfig = field(default_factory=EnergyConfig)
    affinity: AffinityConfig = field(default_factory=AffinityConfig)


@dataclass
class StateSnapshot:
    """
    状态快照
    State snapshot

    包含所有状态的快照，用于持久化和恢复。
    Contains snapshot of all states for persistence and recovery.

    Attributes:
        mood: 主情绪状态 / Main mood state
        mood_sub: 子情绪状态 / Sub mood state
        mood_intensity: 情绪强度 / Mood intensity
        energy: 能量值 / Energy value
        affinity: 好感度值 / Affinity value
        affinity_level: 好感度等级 / Affinity level
        timestamp: 快照时间 / Snapshot time
        schema_version: 数据版本 / Schema version
    """

    mood: str
    mood_sub: Optional[str]
    mood_intensity: float
    energy: float
    affinity: int
    affinity_level: int
    timestamp: datetime = field(default_factory=datetime.now)
    schema_version: str = "1.0"


class StateManager:
    """
    状态管理器
    State Manager

    统一管理所有状态的入口。
    Unified entry point for all state management.

    职责 / Responsibilities:
    - 协调各子状态管理器 / Coordinate sub-managers
    - 提供统一的状态访问接口 / Provide unified state access
    - 触发状态变更事件 / Trigger state change events
    - 管理状态持久化 / Manage state persistence

    Reference:
        MOD-State.md §3.1: StateManager 设计
    """

    def __init__(
        self,
        config: Optional[StateConfig] = None,
    ) -> None:
        """
        初始化状态管理器
        Initialize state manager

        Args:
            config: 状态系统配置 / State system configuration
        """
        self._config = config or StateConfig()
        self._change_listeners: list[Callable[[StateChangedEvent], None]] = []
        self._started = False

        # 初始化情绪状态机 / Initialize emotion state machine
        self._emotion = EmotionStateMachine(
            config=self._config.emotion,
            on_transition=self._on_mood_transition,
        )

        # 初始化能量管理器 / Initialize energy manager
        self._energy = EnergyManager(
            config=self._config.energy,
            on_change=self._on_energy_change,
        )

        # 初始化好感度管理器 / Initialize affinity manager
        self._affinity = AffinityManager(
            config=self._config.affinity,
            on_change=self._on_affinity_change,
            on_level_up=self._on_affinity_level_up,
        )

    # ==================== 状态访问 / State Access ====================

    @property
    def emotion(self) -> EmotionStateMachine:
        """
        获取情绪状态机
        Get emotion state machine
        """
        return self._emotion

    @property
    def energy(self) -> EnergyManager:
        """
        获取能量管理器
        Get energy manager
        """
        return self._energy

    @property
    def affinity(self) -> AffinityManager:
        """
        获取好感度管理器
        Get affinity manager
        """
        return self._affinity

    # ==================== 快照与恢复 / Snapshot & Restore ====================

    def get_snapshot(self) -> StateSnapshot:
        """
        获取当前状态快照
        Get current state snapshot

        Returns:
            包含所有状态的快照对象 / Snapshot containing all states
        """
        current_emotion = self._emotion.current_state
        mood_sub = None
        if current_emotion.sub_state:
            mood_sub = current_emotion.sub_state.value
        return StateSnapshot(
            mood=current_emotion.main_state.value,
            mood_sub=mood_sub,
            mood_intensity=current_emotion.intensity,
            energy=self._energy.value,
            affinity=self._affinity.value,
            affinity_level=self._affinity.level,
            timestamp=datetime.now(),
        )

    def restore_from_snapshot(self, snapshot: StateSnapshot) -> None:
        """
        从快照恢复状态
        Restore state from snapshot

        Args:
            snapshot: 状态快照 / State snapshot
        """
        # 恢复能量 / Restore energy
        self._energy.set(snapshot.energy, "restore_snapshot")

        # 恢复好感度 / Restore affinity
        self._affinity.set(snapshot.affinity, "restore_snapshot")

        # 恢复情绪状态 / Restore emotion state
        try:
            mood = MoodState(snapshot.mood)
            self._emotion.transition_to(
                target_state=mood,
                reason="restore_snapshot",
                intensity=snapshot.mood_intensity,
            )
        except ValueError:
            # 无效状态，使用默认 / Invalid state, use default
            pass

    # ==================== 状态评估 / State Evaluation ====================

    def evaluate_all_states(self) -> None:
        """
        重新评估所有状态
        Re-evaluate all states

        在数值变化后调用，触发状态转换评估。
        Called after value changes, triggers state transition evaluation.
        """
        now = datetime.now()
        hour = now.hour

        # 应用规则层转换 / Apply rule layer transition
        self._emotion.apply_rule_transition(
            energy=self._energy.value,
            hour=hour,
            idle_minutes=0,  # TODO: 从会话管理器获取 / Get from session manager
            is_sleeping=self._emotion.is_sleeping,
        )

        # 应用情绪衰减 / Apply emotion decay
        self._emotion.apply_decay()

    def get_prompt_modifiers(self) -> dict[str, str]:
        """
        获取当前状态对 Prompt 的修饰
        Get current state's prompt modifiers

        Returns:
            状态对应的 Prompt 修饰词典 / Prompt modifier dictionary
        """
        mood = self._emotion.main_mood
        intensity = self._emotion.intensity

        # 情绪对应的 Prompt 修饰 / Mood-specific prompt modifiers
        mood_modifiers: dict[MoodState, str] = {
            MoodState.HAPPY: "用活泼开心的语气回复，可以用emoji",
            MoodState.NORMAL: "",
            MoodState.TIRED: "用简短的语气回复，偶尔打哈欠",
            MoodState.SAD: "用低落、简短的语气回复",
            MoodState.ANXIOUS: "表现出担心和关心，多问候用户状况",
        }

        modifiers: dict[str, str] = {}

        # 情绪修饰 / Mood modifier
        mood_modifier = mood_modifiers.get(mood, "")
        if mood_modifier:
            modifiers["mood"] = mood_modifier

        # 强度修饰 / Intensity modifier
        if intensity >= 0.8:
            modifiers["intensity"] = "情绪表现更强烈"
        elif intensity <= 0.3:
            modifiers["intensity"] = "情绪表现较为平淡"

        # 能量修饰 / Energy modifier
        if self._energy.is_critical:
            modifiers["energy"] = "非常疲惫，需要休息"
        elif self._energy.is_low:
            modifiers["energy"] = "有些疲倦"

        # 好感度修饰 / Affinity modifier
        level = self._affinity.level
        if level >= 4:
            modifiers["affinity"] = "对用户非常亲近，可以使用更亲密的称呼"
        elif level <= 1:
            modifiers["affinity"] = "对用户还比较陌生，保持礼貌距离"

        return modifiers

    def get_behavior_modifiers(self) -> dict[str, float]:
        """
        获取当前状态对行为的修饰
        Get current state's behavior modifiers

        Returns:
            行为修饰因子词典 / Behavior modifier dictionary
        """
        mood = self._emotion.main_mood

        # 基础修饰因子 / Base modifier factors
        base_modifiers: dict[str, float] = {
            "idle_chat_frequency": 1.0,
            "proactive_event_probability": 1.0,
            "response_length": 1.0,
        }

        # 情绪修饰 / Mood modifiers
        mood_modifiers: dict[MoodState, dict[str, float]] = {
            MoodState.HAPPY: {
                "idle_chat_frequency": 1.5,
                "proactive_event_probability": 1.3,
            },
            MoodState.TIRED: {
                "idle_chat_frequency": 0.5,
                "proactive_event_probability": 0.3,
                "response_length": 0.7,
            },
            MoodState.SAD: {
                "idle_chat_frequency": 0.7,
                "proactive_event_probability": 0.5,
            },
            MoodState.ANXIOUS: {
                "idle_chat_frequency": 0.8,
                "proactive_event_probability": 0.6,
            },
        }

        # 应用情绪修饰 / Apply mood modifiers
        if mood in mood_modifiers:
            for key, value in mood_modifiers[mood].items():
                base_modifiers[key] = value

        # 应用好感度主动性乘数 / Apply affinity proactivity multiplier
        proactivity = self._affinity.proactivity_multiplier
        base_modifiers["proactive_event_probability"] *= proactivity

        return base_modifiers

    # ==================== 生命周期 / Lifecycle ====================

    async def start(self) -> None:
        """
        启动状态管理器
        Start state manager
        """
        if self._started:
            return

        self._started = True
        # 初始评估 / Initial evaluation
        self.evaluate_all_states()

    async def stop(self) -> None:
        """
        停止状态管理器
        Stop state manager
        """
        if not self._started:
            return

        self._started = False

    def register_change_listener(
        self,
        callback: Callable[[StateChangedEvent], None],
    ) -> Callable[[], None]:
        """
        注册状态变更监听器
        Register state change listener

        Args:
            callback: 变更回调函数 / Change callback function

        Returns:
            取消注册函数 / Unregister function
        """
        self._change_listeners.append(callback)

        def unregister() -> None:
            if callback in self._change_listeners:
                self._change_listeners.remove(callback)

        return unregister

    # ==================== 内部回调 / Internal Callbacks ====================

    def _on_mood_transition(self, event: MoodTransitionEvent) -> None:
        """
        情绪转换回调
        Mood transition callback

        Args:
            event: 情绪转换事件 / Mood transition event
        """
        # 创建通用状态变化事件 / Create generic state change event
        state_event = StateChangedEvent(
            change_type=StateChangeType.MOOD_CHANGED,
            old_value=event.from_state.value,
            new_value=event.to_state.value,
            reason=event.reason,
            timestamp=event.timestamp,
            extra={
                "from_sub": event.from_sub.value if event.from_sub else None,
                "to_sub": event.to_sub.value if event.to_sub else None,
                "trigger": event.trigger,
            },
        )
        self._notify_listeners(state_event)

    def _on_energy_change(
        self,
        old_value: float,
        new_value: float,
        reason: str,
    ) -> None:
        """
        能量变化回调
        Energy change callback

        Args:
            old_value: 旧值 / Old value
            new_value: 新值 / New value
            reason: 变化原因 / Change reason
        """
        # 检查是否触发疲倦 / Check if tiredness triggered
        triggered_tired = new_value < 20 and old_value >= 20

        event = StateChangedEvent(
            change_type=StateChangeType.ENERGY_CHANGED,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            extra={"triggered_tired": triggered_tired},
        )
        self._notify_listeners(event)

        # 如果能量变化可能影响情绪，重新评估 / Re-evaluate if energy affects mood
        if triggered_tired or (new_value >= 20 and old_value < 20):
            self.evaluate_all_states()

    def _on_affinity_change(
        self,
        old_value: int,
        new_value: int,
        reason: str,
    ) -> None:
        """
        好感度变化回调
        Affinity change callback

        Args:
            old_value: 旧值 / Old value
            new_value: 新值 / New value
            reason: 变化原因 / Change reason
        """
        event = StateChangedEvent(
            change_type=StateChangeType.AFFINITY_CHANGED,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
        )
        self._notify_listeners(event)

    def _on_affinity_level_up(self, old_level: int, new_level: int) -> None:
        """
        好感度等级提升回调
        Affinity level up callback

        Args:
            old_level: 旧等级 / Old level
            new_level: 新等级 / New level
        """
        unlocks = self._affinity.get_unlocks_at_level(new_level)

        # 作为状态变化事件通知 / Notify as state change event
        event = StateChangedEvent(
            change_type=StateChangeType.LEVEL_UP,
            old_value=old_level,
            new_value=new_level,
            reason="affinity_level_up",
            extra={
                "attribute": "affinity",
                "unlocks": unlocks,
            },
        )
        self._notify_listeners(event)

    def _notify_listeners(self, event: StateChangedEvent) -> None:
        """
        通知所有监听器
        Notify all listeners

        Args:
            event: 状态变化事件 / State change event
        """
        for listener in self._change_listeners:
            try:
                listener(event)
            except Exception:
                # 忽略监听器错误，继续通知其他监听器
                # Ignore listener errors, continue notifying others
                pass

    # ==================== 便捷方法 / Convenience Methods ====================

    def get_summary(self) -> dict[str, Any]:
        """
        获取状态摘要
        Get state summary

        Returns:
            状态摘要字典 / State summary dictionary
        """
        return {
            "mood": {
                "main": self._emotion.main_mood.value,
                "sub": self._emotion.sub_mood.value if self._emotion.sub_mood else None,
                "intensity": self._emotion.intensity,
                "expression": self._emotion.get_expression(),
            },
            "energy": self._energy.to_dict(),
            "affinity": self._affinity.to_dict(),
        }
