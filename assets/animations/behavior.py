"""
狐耳娘行为脚本
Fox Girl Behavior Script

此脚本在沙盒环境中执行，可以访问 ctx（ScriptContext）对象。
This script runs in sandbox, with access to ctx (ScriptContext) object.

可用的 ctx API / Available ctx API:
- ctx.state.mood / energy / affection / emotion / emotion_intensity
- ctx.time.hour / minute / is_night / is_weekend / weekday
- ctx.interaction.last_interaction_seconds / today_interactions
- ctx.animation.current_animation / is_playing_action
- ctx.set_interval(min_ms, max_ms)
- ctx.play_action(name)
- ctx.play_effect(name, duration_ms)
- ctx.random() / ctx.random_int(min, max) / ctx.random_choice(list)
- ctx.log(message)
"""


def get_random_actions(ctx):
    """
    返回当前可用的随机动作列表
    Return list of available random actions

    根据状态动态调整动作列表和频率。
    Dynamically adjust action list and frequency based on state.

    Args:
        ctx: ScriptContext 实例

    Returns:
        动作名称列表
    """
    # 基础动作 / Base actions
    actions = []

    mood = ctx.state.mood
    energy = ctx.state.energy
    affection = ctx.state.affection

    # 根据好感度解锁动作 / Unlock actions based on affection
    if affection >= 0.0:
        actions.append("ear_wiggle")

    # 根据心情调整频率 / Adjust frequency based on mood
    if mood > 0.7:
        # 开心时：更频繁
        ctx.set_interval(2000, 5000)
    elif mood > 0.4:
        # 普通心情
        ctx.set_interval(3000, 8000)
    else:
        # 心情不好：更慢
        ctx.set_interval(5000, 12000)

    # 疲劳时减少动作 / Reduce actions when tired
    if energy < 0.3:
        ctx.set_interval(6000, 12000)

    # 如果没有动作，返回空列表（不播放随机动作）
    if not actions:
        actions = ["ear_wiggle"]

    return actions


def on_emotion_change(ctx, emotion, intensity):
    """
    情感变化响应
    Response to emotion change

    Args:
        ctx: ScriptContext 实例
        emotion: 情感标签 (happy, sad, angry, shy, etc.)
        intensity: 强度 (0.0 ~ 1.0)
    """
    ctx.log(f"情感变化: {emotion}, 强度: {intensity}")

    if emotion == "happy":
        if intensity > 0.8:
            ctx.play_effect("sparkle", 3000)
        elif intensity > 0.5:
            ctx.play_effect("sparkle", 1500)

    elif emotion == "shy":
        ctx.play_effect("heart", 2000)

    elif emotion == "sad":
        if intensity > 0.7:
            ctx.play_effect("tear_drop", 3000)

    elif emotion == "excited":
        ctx.play_effect("sparkle", 2000)


def on_interaction(ctx, interaction_type):
    """
    用户交互响应
    Response to user interaction

    Args:
        ctx: ScriptContext 实例
        interaction_type: 交互类型
            - "click": 单击
            - "double_click": 双击
            - "drag_start": 开始拖拽
            - "drag_end": 结束拖拽
            - "pet": 抚摸
            - "chat": 聊天输入
    """
    ctx.log(f"用户交互: {interaction_type}")

    if interaction_type == "click":
        # 点击时有概率摇耳朵
        if ctx.random() < 0.3:
            ctx.play_action("ear_wiggle")

    elif interaction_type == "pet":
        # 抚摸时的反应 / Pet reaction
        ctx.play_action("head_pat")
        if ctx.state.affection > 0.7:
            ctx.play_effect("heart", 2000)
        elif ctx.state.affection > 0.4:
            ctx.play_effect("sparkle", 1500)


def get_idle_animation(ctx):
    """
    获取当前应该使用的待机动画
    Get current idle animation to use

    Returns:
        待机动画名称
    """
    # 目前只有一个 idle 动画
    return "idle"


def on_state_update(ctx):
    """
    周期性状态检查（每秒调用）
    Periodic state check (called every second)
    """
    # 长时间未交互
    idle_seconds = ctx.interaction.last_interaction_seconds

    if idle_seconds > 300:  # 5分钟
        if ctx.random() < 0.02:  # 2% 概率
            ctx.log("长时间未交互，触发随机动作")

    # 夜间模式
    if ctx.time.is_night and ctx.time.hour >= 23:
        if ctx.random() < 0.01:  # 1% 概率
            ctx.log("夜深了...")
