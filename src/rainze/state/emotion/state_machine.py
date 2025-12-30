"""
情绪状态机
Emotion State Machine

实现混合驱动的情绪状态机，规则层优先于 LLM 层。
Implements hybrid-driven emotion state machine, rule layer takes priority.

Reference:
    - PRD §0.6a: 状态优先级矩阵
    - MOD-State.md §3.2: EmotionStateMachine

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Callable, Optional

# 从 contracts 导入共享类型 / Import shared types from contracts
from rainze.core.contracts import EmotionTag

from .states import (
    MOOD_SUB_STATE_MAP,
    EmotionState,
    MoodState,
    MoodSubState,
    get_priority,
)

if TYPE_CHECKING:
    from rainze.state.models.events import MoodTransitionEvent


# 默认配置 / Default configuration
@dataclass
class EmotionConfig:
    """
    情绪状态机配置
    Emotion state machine configuration
    """

    initial_state: MoodState = MoodState.NORMAL
    inertia_factor: float = 0.7  # 情绪惯性因子 / Emotion inertia factor
    switch_protection_seconds: int = 60  # 切换保护时间（秒）/ Switch protection
    happy_decay_hours: float = 2.0  # Happy 衰减时间 / Happy decay time
    sad_recovery_hours: float = 4.0  # Sad 恢复时间 / Sad recovery time
    min_override_intensity: float = 0.8  # 最小覆盖强度 / Min override intensity


class EmotionStateMachine:
    """
    情绪状态机
    Emotion State Machine

    实现混合驱动架构：
    - 规则层（硬约束）：确定性转换，不依赖 LLM
    - LLM 层（软决策）：情感细微调整，需要上下文理解

    规则层始终优先于 LLM 层。
    Implements hybrid-driven architecture:
    - Rule layer (hard constraints): Deterministic transitions, no LLM
    - LLM layer (soft decisions): Subtle adjustments, needs context

    Rule layer ALWAYS takes priority over LLM layer.

    Reference:
        PRD §0.6a: 混合驱动状态机
    """

    def __init__(
        self,
        config: Optional[EmotionConfig] = None,
        on_transition: Optional[Callable[["MoodTransitionEvent"], None]] = None,
    ) -> None:
        """
        初始化情绪状态机
        Initialize emotion state machine

        Args:
            config: 情绪配置 / Emotion configuration
            on_transition: 状态转换回调 / State transition callback
        """
        self._config = config or EmotionConfig()
        self._on_transition = on_transition

        # 初始化当前状态 / Initialize current state
        self._current = EmotionState(
            main_state=self._config.initial_state,
            sub_state=None,
            intensity=0.5,
            entered_at=datetime.now(),
            trigger_reason="initialization",
        )

        # 状态切换历史，用于保护期检查 / State switch history for protection check
        self._switch_history: dict[MoodState, datetime] = {}

        # 是否处于睡眠状态 / Whether in sleeping state
        self._is_sleeping: bool = False

    # ==================== 状态访问 / State Access ====================

    @property
    def current_state(self) -> EmotionState:
        """
        获取当前情绪状态
        Get current emotion state
        """
        return self._current

    @property
    def main_mood(self) -> MoodState:
        """
        获取主情绪状态
        Get main mood state
        """
        return self._current.main_state

    @property
    def sub_mood(self) -> Optional[MoodSubState]:
        """
        获取子情绪状态
        Get sub-mood state
        """
        return self._current.sub_state

    @property
    def intensity(self) -> float:
        """
        获取情绪强度 [0.0, 1.0]
        Get emotion intensity
        """
        return self._current.intensity

    @property
    def is_sleeping(self) -> bool:
        """
        是否处于睡眠状态
        Whether in sleeping state
        """
        return self._is_sleeping

    # ==================== 规则层转换 / Rule Layer Transition ====================

    def apply_rule_transition(
        self,
        energy: float,
        hour: int,
        idle_minutes: int,
        is_sleeping: bool,
    ) -> Optional[MoodState]:
        """
        应用规则层状态转换（硬约束）
        Apply rule layer state transition (hard constraints)

        规则层判断优先于任何 LLM 层决策。
        Rule layer decisions take priority over any LLM layer.

        Args:
            energy: 当前能量值 / Current energy value
            hour: 当前小时 / Current hour
            idle_minutes: 空闲分钟数 / Idle minutes
            is_sleeping: 是否睡眠中 / Whether sleeping

        Returns:
            需要转换到的状态，None 表示规则层不触发转换
            Target state to transition to, None means no rule triggered
        """
        self._is_sleeping = is_sleeping

        # 规则1: 睡眠状态（最高优先级）/ Rule 1: Sleeping (highest priority)
        if is_sleeping:
            if self._current.main_state != MoodState.TIRED:
                self._force_transition(
                    MoodState.TIRED,
                    MoodSubState.SLEEPY,
                    "rule:sleeping",
                )
            return MoodState.TIRED

        # 规则2: 能量极低（不可覆盖）/ Rule 2: Critical low energy (uncoverridable)
        if energy < 20:
            if self._current.main_state != MoodState.TIRED:
                self._force_transition(
                    MoodState.TIRED,
                    MoodSubState.EXHAUSTED,
                    "rule:low_energy",
                )
            return MoodState.TIRED

        # 规则3: 深夜疲倦（可覆盖）/ Rule 3: Night tiredness (overridable)
        if (hour >= 23 or hour < 6) and energy < 50:
            # 仅在当前不是更高优先级状态时触发
            # Only trigger if not in higher priority state
            current_priority = get_priority(self._current.main_state, energy, hour)
            tired_night_priority = 30  # Tired_Night priority
            if current_priority < tired_night_priority:
                self._force_transition(
                    MoodState.TIRED,
                    MoodSubState.SLEEPY,
                    "rule:night_tired",
                )
                return MoodState.TIRED

        # 规则4: 长时间空闲（触发 Sad/Lonely）/ Rule 4: Long idle (trigger Sad)
        if idle_minutes > 60:
            current_priority = get_priority(self._current.main_state, energy, hour)
            sad_priority = 40
            if current_priority < sad_priority:
                self._force_transition(
                    MoodState.SAD,
                    MoodSubState.LONELY,
                    "rule:long_idle",
                )
                return MoodState.SAD

        # 无规则触发 / No rule triggered
        return None

    # ==================== LLM 层转换 / LLM Layer Transition ====================

    def apply_llm_suggestion(
        self,
        emotion_tag: str,
        intensity: float,
        context: dict[str, Any],
    ) -> bool:
        """
        应用 LLM 层情绪建议（软决策）
        Apply LLM layer emotion suggestion (soft decision)

        仅在规则层未触发且状态允许覆盖时生效。
        Only effective when rule layer didn't trigger and state is overridable.

        Args:
            emotion_tag: LLM 输出的情感标签 / LLM output emotion tag
            intensity: 情感强度 / Emotion intensity
            context: 上下文信息 / Context information

        Returns:
            是否应用了转换 / Whether transition was applied
        """
        # 睡眠状态不接受 LLM 建议 / Sleeping state doesn't accept LLM suggestion
        if self._is_sleeping:
            return False

        # 映射情感标签到 MoodState / Map emotion tag to MoodState
        tag_to_mood: dict[str, MoodState] = {
            "happy": MoodState.HAPPY,
            "excited": MoodState.HAPPY,
            "sad": MoodState.SAD,
            "angry": MoodState.ANXIOUS,  # 愤怒映射到焦虑 / Anger maps to anxious
            "shy": MoodState.HAPPY,  # 害羞映射到开心 / Shy maps to happy
            "surprised": MoodState.HAPPY,
            "tired": MoodState.TIRED,
            "anxious": MoodState.ANXIOUS,
            "neutral": MoodState.NORMAL,
        }

        target_mood = tag_to_mood.get(emotion_tag.lower(), MoodState.NORMAL)

        # 检查是否可以转换 / Check if transition is allowed
        if not self.can_transition_to(target_mood):
            return False

        # 检查切换保护 / Check switch protection
        if self.check_switch_protection(target_mood):
            return False

        # 应用情绪惯性 / Apply emotion inertia
        smoothed_intensity = self.apply_inertia(intensity)

        # 确定子状态 / Determine sub-state
        sub_state = self._determine_sub_state(target_mood, emotion_tag, intensity)

        # 执行转换 / Execute transition
        return self.transition_to(
            target_state=target_mood,
            reason=f"llm:{emotion_tag}",
            sub_state=sub_state,
            intensity=smoothed_intensity,
        )

    def apply_emotion_tag(self, emotion: EmotionTag, context: dict[str, Any]) -> bool:
        """
        应用 EmotionTag 情绪建议
        Apply EmotionTag emotion suggestion

        使用统一的 EmotionTag 类型进行情绪转换。
        Use unified EmotionTag type for emotion transition.

        Args:
            emotion: 情感标签 / Emotion tag from contracts
            context: 上下文信息 / Context information

        Returns:
            是否应用了转换 / Whether transition was applied
        """
        return self.apply_llm_suggestion(
            emotion_tag=emotion.tag,
            intensity=emotion.intensity,
            context=context,
        )

    # ==================== 状态转换 / State Transition ====================

    def transition_to(
        self,
        target_state: MoodState,
        reason: str,
        sub_state: Optional[MoodSubState] = None,
        intensity: float = 0.5,
    ) -> bool:
        """
        执行状态转换
        Execute state transition

        检查状态优先级矩阵和覆盖条件。
        Check state priority matrix and override conditions.

        Args:
            target_state: 目标状态 / Target state
            reason: 转换原因 / Transition reason
            sub_state: 子状态 / Sub-state
            intensity: 强度 / Intensity

        Returns:
            是否成功转换 / Whether transition succeeded
        """
        # 检查是否可以转换 / Check if can transition
        if not self.can_transition_to(target_state):
            return False

        # 记录旧状态 / Record old state
        old_state = self._current

        # 验证子状态 / Validate sub-state
        if sub_state is not None:
            valid_subs = MOOD_SUB_STATE_MAP.get(target_state, [])
            if sub_state not in valid_subs:
                sub_state = None

        # 创建新状态 / Create new state
        now = datetime.now()
        self._current = EmotionState(
            main_state=target_state,
            sub_state=sub_state,
            intensity=max(0.0, min(1.0, intensity)),
            entered_at=now,
            trigger_reason=reason,
        )

        # 更新切换历史 / Update switch history
        self._switch_history[target_state] = now

        # 触发回调 / Trigger callback
        if self._on_transition is not None:
            # 延迟导入避免循环依赖 / Lazy import to avoid circular dependency
            from rainze.state.models.events import MoodTransitionEvent

            event = MoodTransitionEvent(
                from_state=old_state.main_state,
                to_state=target_state,
                from_sub=old_state.sub_state,
                to_sub=sub_state,
                trigger="rule" if reason.startswith("rule:") else "llm",
                reason=reason,
                timestamp=now,
            )
            self._on_transition(event)

        return True

    def can_transition_to(self, target_state: MoodState) -> bool:
        """
        检查是否可以转换到目标状态
        Check if can transition to target state

        基于优先级矩阵判断是否允许转换。
        Check if transition is allowed based on priority matrix.

        Args:
            target_state: 目标状态 / Target state

        Returns:
            是否允许转换 / Whether transition is allowed
        """
        # 睡眠状态不允许转换（除非是规则层）/ Sleeping doesn't allow transition
        if self._is_sleeping and target_state != MoodState.TIRED:
            return False

        # 获取当前和目标优先级 / Get current and target priority
        current_priority = get_priority(self._current.main_state)
        target_priority = get_priority(target_state)

        # 不可覆盖状态（优先级 >= 90）/ Uncoverridable states (priority >= 90)
        if current_priority >= 90:
            return False

        # 低优先级不能覆盖高优先级 / Low priority cannot override high priority
        if target_priority < current_priority:
            # 除非目标强度足够高 / Unless target intensity is high enough
            return False

        return True

    # ==================== 平滑过渡 / Smooth Transition ====================

    def apply_inertia(
        self,
        target_intensity: float,
        inertia_factor: Optional[float] = None,
    ) -> float:
        """
        应用情绪惯性
        Apply emotion inertia

        new_intensity = current * inertia + target * (1 - inertia)

        Args:
            target_intensity: 目标强度 / Target intensity
            inertia_factor: 惯性因子 / Inertia factor

        Returns:
            平滑后的强度 / Smoothed intensity
        """
        factor = inertia_factor or self._config.inertia_factor
        current = self._current.intensity
        smoothed = current * factor + target_intensity * (1 - factor)
        return max(0.0, min(1.0, smoothed))

    def check_switch_protection(self, target_state: MoodState) -> bool:
        """
        检查状态切换保护
        Check state switch protection

        同一状态对60秒内不可重复切换。
        Same state cannot be switched to within 60 seconds.

        Args:
            target_state: 目标状态 / Target state

        Returns:
            是否在保护期内（True = 受保护，不可切换）
            Whether in protection period (True = protected, cannot switch)
        """
        last_switch = self._switch_history.get(target_state)
        if last_switch is None:
            return False

        elapsed = datetime.now() - last_switch
        protection_duration = timedelta(seconds=self._config.switch_protection_seconds)
        return elapsed < protection_duration

    # ==================== 衰减与恢复 / Decay & Recovery ====================

    def apply_decay(self) -> None:
        """
        应用情绪衰减
        Apply emotion decay

        Happy 2小时无强化 → Normal
        Sad 4小时无负面 → Normal
        """
        now = datetime.now()
        elapsed = now - self._current.entered_at

        # Happy 衰减 / Happy decay
        if self._current.main_state == MoodState.HAPPY:
            decay_duration = timedelta(hours=self._config.happy_decay_hours)
            if elapsed > decay_duration:
                self.transition_to(
                    MoodState.NORMAL,
                    "decay:happy_timeout",
                    intensity=0.5,
                )

        # Sad 恢复 / Sad recovery
        elif self._current.main_state == MoodState.SAD:
            recovery_duration = timedelta(hours=self._config.sad_recovery_hours)
            if elapsed > recovery_duration:
                self.transition_to(
                    MoodState.NORMAL,
                    "recovery:sad_timeout",
                    intensity=0.5,
                )

    def apply_recovery(
        self,
        positive_action: str,
        intensity: float,
    ) -> None:
        """
        应用情绪恢复
        Apply emotion recovery

        Args:
            positive_action: 正面行为类型 / Positive action type
            intensity: 行为强度 / Action intensity
        """
        # 从 Sad/Tired 恢复需要足够强度
        # Recovery from Sad/Tired needs sufficient intensity
        if self._current.main_state in (MoodState.SAD, MoodState.TIRED):
            if intensity >= self._config.min_override_intensity:
                self.transition_to(
                    MoodState.HAPPY,
                    f"recovery:{positive_action}",
                    sub_state=MoodSubState.CONTENT,
                    intensity=intensity,
                )
        # 从 Normal 提升到 Happy
        # Elevate from Normal to Happy
        elif self._current.main_state == MoodState.NORMAL:
            if intensity >= 0.5:
                self.transition_to(
                    MoodState.HAPPY,
                    f"positive:{positive_action}",
                    sub_state=MoodSubState.CONTENT,
                    intensity=intensity,
                )

    # ==================== 表情映射 / Expression Mapping ====================

    def get_expression(self) -> str:
        """
        获取当前状态对应的表情
        Get expression for current state

        Returns:
            表情标识符 / Expression identifier
        """
        expression_map: dict[MoodState, str] = {
            MoodState.HAPPY: "smile",
            MoodState.NORMAL: "idle",
            MoodState.TIRED: "sleepy",
            MoodState.SAD: "sad",
            MoodState.ANXIOUS: "worried",
        }
        return expression_map.get(self._current.main_state, "idle")

    def get_animation_hint(self) -> Optional[str]:
        """
        获取动画提示
        Get animation hint

        Returns:
            动画标识符 / Animation identifier
        """
        # 基于子状态提供更精确的动画提示
        # Provide more precise animation hint based on sub-state
        sub = self._current.sub_state
        if sub == MoodSubState.EXCITED:
            return "bounce"
        elif sub == MoodSubState.SLEEPY:
            return "yawn"
        elif sub == MoodSubState.LONELY:
            return "look_around"
        elif sub == MoodSubState.NERVOUS:
            return "fidget"
        return None

    # ==================== 内部方法 / Internal Methods ====================

    def _force_transition(
        self,
        target: MoodState,
        sub: Optional[MoodSubState],
        reason: str,
    ) -> None:
        """
        强制状态转换（规则层专用）
        Force state transition (rule layer only)

        跳过优先级检查和保护期检查。
        Skip priority check and protection period check.
        """
        old_state = self._current
        now = datetime.now()

        self._current = EmotionState(
            main_state=target,
            sub_state=sub,
            intensity=0.8 if reason.startswith("rule:") else 0.5,
            entered_at=now,
            trigger_reason=reason,
        )

        self._switch_history[target] = now

        # 触发回调 / Trigger callback
        if self._on_transition is not None:
            from rainze.state.models.events import MoodTransitionEvent

            event = MoodTransitionEvent(
                from_state=old_state.main_state,
                to_state=target,
                from_sub=old_state.sub_state,
                to_sub=sub,
                trigger="rule",
                reason=reason,
                timestamp=now,
            )
            self._on_transition(event)

    def _determine_sub_state(
        self,
        mood: MoodState,
        emotion_tag: str,
        intensity: float,
    ) -> Optional[MoodSubState]:
        """
        根据情感标签和强度确定子状态
        Determine sub-state based on emotion tag and intensity

        Args:
            mood: 主情绪 / Main mood
            emotion_tag: 情感标签 / Emotion tag
            intensity: 强度 / Intensity

        Returns:
            子状态 / Sub-state
        """
        valid_subs = MOOD_SUB_STATE_MAP.get(mood, [])
        if not valid_subs:
            return None

        # 高强度选择第一个（更强烈的），低强度选择第二个（更温和的）
        # High intensity picks first (stronger), low intensity picks second (milder)
        if intensity >= 0.7 and len(valid_subs) >= 1:
            return valid_subs[0]
        elif len(valid_subs) >= 2:
            return valid_subs[1]
        return valid_subs[0] if valid_subs else None

    def set_sleeping(self, is_sleeping: bool) -> None:
        """
        设置睡眠状态
        Set sleeping state

        Args:
            is_sleeping: 是否睡眠 / Whether sleeping
        """
        self._is_sleeping = is_sleeping
        if is_sleeping:
            self._force_transition(
                MoodState.TIRED,
                MoodSubState.SLEEPY,
                "manual:set_sleeping",
            )
