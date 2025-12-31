# MOD-Animation-Script - 动画脚本系统

> **模块版本**: v1.0.0
> **创建时间**: 2025-12-30
> **关联PRD**: PRD-Rainze.md v3.1.0 §0.14
> **关联模块**: MOD-Animation.md, MOD-Plugin.md
> **模块层级**: 应用层 (Application Layer)
> **优先级**: P1 (重要功能)
> **依赖模块**: Animation, State, Core

---

## 1. 模块概述

### 1.1 设计动机

**问题**: 当前 JSON 配置的动画系统存在以下局限：

| 问题 | 描述 |
|------|------|
| **静态配置** | 无法表达条件逻辑 (`if mood > 0.7 then ...`) |
| **无状态感知** | 无法访问心情、好感度、时间等运行时状态 |
| **固定行为** | 随机动作列表是写死的，无法根据情绪动态调整 |
| **缺乏个性** | 不同角色/皮肤无法有独特的行为模式 |

**解决方案**: 引入 Python 脚本系统，在沙盒中执行动画行为逻辑。

### 1.2 设计目标

```
┌─────────────────────────────────────────────────────────────┐
│                    Animation Script System                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   manifest.json          behavior.py                        │
│   ┌─────────────┐       ┌─────────────────────────────┐    │
│   │ 静态配置     │       │ 动态行为逻辑               │    │
│   │ - 帧定义    │       │ - get_random_actions()     │    │
│   │ - 时长      │       │ - on_emotion_change()      │    │
│   │ - 锚点      │       │ - on_state_update()        │    │
│   └─────────────┘       │ - on_interaction()         │    │
│         │               └─────────────────────────────┘    │
│         │                         │                         │
│         v                         v                         │
│   ┌─────────────────────────────────────────────────┐      │
│   │           AnimationController                    │      │
│   │  - 加载 manifest.json                           │      │
│   │  - 在沙盒中执行 behavior.py                     │      │
│   │  - 根据脚本输出调度动画                         │      │
│   └─────────────────────────────────────────────────┘      │
│                           │                                 │
│                           v                                 │
│   ┌─────────────────────────────────────────────────┐      │
│   │              3 层渲染系统                        │      │
│   │  ┌─────────────────────────────────────────┐   │      │
│   │  │ Layer 2: Overlay (特效/粒子)            │   │      │
│   │  ├─────────────────────────────────────────┤   │      │
│   │  │ Layer 1: Character (角色帧动画)         │   │      │
│   │  ├─────────────────────────────────────────┤   │      │
│   │  │ Layer 0: Background (阴影/背景)         │   │      │
│   │  └─────────────────────────────────────────┘   │      │
│   └─────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 核心原则

| 原则 | 说明 |
|------|------|
| **安全第一** | 脚本在受限沙盒中执行，无法访问文件系统、网络、系统调用 |
| **只读访问** | 脚本只能读取状态，不能直接修改（通过返回值影响行为） |
| **性能约束** | 脚本执行有超时限制（默认 10ms），防止阻塞渲染 |
| **优雅降级** | 脚本执行失败时回退到 JSON 配置 |
| **复用基础设施** | 与 Plugin 系统共享沙盒执行环境 |

---

## 2. 目录结构

### 2.1 角色动画资源结构

```
assets/
└── animations/
    └── {character_name}/           # 角色名（如 fox_girl）
        ├── manifest.json           # 静态配置（帧、时长等）
        ├── behavior.py             # 行为脚本（动态逻辑）
        ├── idle/
        │   └── default/
        │       └── frame_*.png
        ├── ear_wiggle/
        │   └── default/
        │       └── frame_*.png
        ├── happy_bounce/
        │   └── default/
        │       └── frame_*.png
        └── expressions/
            ├── happy/
            ├── sad/
            └── shy/
```

### 2.2 源码结构

```
src/rainze/animation/
├── script/                     # 脚本系统
│   ├── __init__.py
│   ├── sandbox.py              # 沙盒执行环境
│   ├── context.py              # 脚本上下文（暴露给脚本的 API）
│   ├── loader.py               # 行为脚本加载器
│   └── builtins.py             # 安全内置函数白名单
└── behavior/                   # 行为管理
    ├── __init__.py
    ├── manager.py              # BehaviorManager 行为管理器
    └── events.py               # 行为事件定义
```

---

## 3. 脚本 API 设计

### 3.1 脚本上下文 (ScriptContext)

脚本可以访问的只读 API：

```python
class ScriptContext:
    """
    脚本执行上下文
    Script Execution Context
    
    提供给行为脚本的受限 API。
    Provides restricted API for behavior scripts.
    """
    
    # ==================== 状态访问 (只读) ====================
    
    @property
    def state(self) -> StateView:
        """
        角色状态视图
        Character state view (read-only)
        
        Attributes:
            mood: float         # 心情 (0.0 ~ 1.0)
            energy: float       # 精力 (0.0 ~ 1.0)
            affection: float    # 好感度 (0.0 ~ 1.0)
            hunger: float       # 饥饿度 (0.0 ~ 1.0)
            emotion: str        # 当前情感标签
            emotion_intensity: float  # 情感强度
        """
        ...
    
    @property
    def time(self) -> TimeView:
        """
        时间视图
        Time view (read-only)
        
        Attributes:
            hour: int           # 小时 (0-23)
            minute: int         # 分钟 (0-59)
            weekday: int        # 星期几 (0=周一, 6=周日)
            is_night: bool      # 是否夜间 (22:00 ~ 06:00)
            is_weekend: bool    # 是否周末
        """
        ...
    
    @property
    def interaction(self) -> InteractionView:
        """
        交互统计视图
        Interaction stats view (read-only)
        
        Attributes:
            last_interaction_seconds: int   # 距上次交互的秒数
            today_interactions: int         # 今日交互次数
            total_interactions: int         # 总交互次数
            consecutive_days: int           # 连续互动天数
        """
        ...
    
    @property
    def animation(self) -> AnimationView:
        """
        动画状态视图
        Animation state view (read-only)
        
        Attributes:
            current_animation: str      # 当前动画名
            current_action: str | None  # 当前播放的动作
            is_playing_action: bool     # 是否正在播放动作
        """
        ...
    
    # ==================== 动作控制 ====================
    
    def set_interval(self, min_ms: int, max_ms: int) -> None:
        """
        设置随机动作间隔
        Set random action interval
        
        Args:
            min_ms: 最小间隔（毫秒）
            max_ms: 最大间隔（毫秒）
        """
        ...
    
    def play_action(self, action_name: str) -> bool:
        """
        请求播放一次性动作
        Request to play one-shot action
        
        注意：这是一个请求，不保证立即执行。
        Note: This is a request, not guaranteed to execute immediately.
        
        Args:
            action_name: 动作名称
            
        Returns:
            请求是否被接受
        """
        ...
    
    def play_effect(self, effect_name: str, duration_ms: int = 2000) -> bool:
        """
        请求播放特效
        Request to play effect
        
        Args:
            effect_name: 特效名称 (sparkle, heart, sweat, etc.)
            duration_ms: 持续时间
            
        Returns:
            请求是否被接受
        """
        ...
    
    # ==================== 工具函数 ====================
    
    def random(self) -> float:
        """返回 0.0 ~ 1.0 的随机数"""
        ...
    
    def random_int(self, min_val: int, max_val: int) -> int:
        """返回 [min_val, max_val] 范围内的随机整数"""
        ...
    
    def random_choice(self, items: list) -> Any:
        """从列表中随机选择一个元素"""
        ...
    
    def log(self, message: str) -> None:
        """
        记录日志（用于调试）
        Log message (for debugging)
        
        日志会带上脚本标识，方便追踪。
        """
        ...
```

### 3.2 行为脚本接口

行为脚本必须实现的函数：

```python
# behavior.py - 行为脚本模板
# Behavior Script Template

"""
角色行为脚本
Character Behavior Script

此脚本在沙盒环境中执行，可以访问 ctx（ScriptContext）对象。
This script runs in sandbox, with access to ctx (ScriptContext) object.

可用的 ctx API:
- ctx.state.mood / energy / affection / emotion / ...
- ctx.time.hour / minute / is_night / is_weekend / ...
- ctx.interaction.last_interaction_seconds / today_interactions / ...
- ctx.animation.current_animation / is_playing_action / ...
- ctx.set_interval(min_ms, max_ms)
- ctx.play_action(name)
- ctx.play_effect(name, duration_ms)
- ctx.random() / ctx.random_int(min, max) / ctx.random_choice(list)
- ctx.log(message)
"""


def get_random_actions(ctx) -> list[str]:
    """
    返回当前可用的随机动作列表
    Return list of available random actions
    
    此函数在每次调度随机动作时调用。
    Called when scheduling random actions.
    
    Args:
        ctx: ScriptContext 实例
        
    Returns:
        动作名称列表（从 manifest.json 中定义的动作中选择）
    """
    actions = ["blink"]  # 基础动作，总是可用
    
    mood = ctx.state.mood
    energy = ctx.state.energy
    
    # 根据心情调整动作列表
    if mood > 0.7:
        # 开心时：更多活泼动作
        actions.extend(["ear_wiggle", "happy_bounce", "tail_wag"])
        ctx.set_interval(2000, 5000)  # 更频繁
    elif mood > 0.4:
        # 普通心情
        actions.extend(["ear_wiggle", "tail_wag"])
        ctx.set_interval(3000, 8000)
    else:
        # 心情不好
        actions.append("sigh")
        ctx.set_interval(5000, 12000)  # 更慢
    
    # 根据精力调整
    if energy < 0.3:
        actions.append("yawn")
    
    # 根据时间调整
    if ctx.time.is_night:
        actions.append("sleepy_nod")
    
    return actions


def on_emotion_change(ctx, emotion: str, intensity: float) -> None:
    """
    情感变化时的响应
    Response to emotion change
    
    当 AI 返回情感标签或状态系统检测到情感变化时调用。
    Called when AI returns emotion tag or state system detects emotion change.
    
    Args:
        ctx: ScriptContext 实例
        emotion: 情感标签 (happy, sad, angry, shy, etc.)
        intensity: 强度 (0.0 ~ 1.0)
    """
    if emotion == "happy" and intensity > 0.8:
        ctx.play_action("celebrate")
        ctx.play_effect("sparkle", 3000)
    elif emotion == "shy" and intensity > 0.5:
        ctx.play_action("hide_face")
        ctx.play_effect("heart", 2000)
    elif emotion == "sad" and intensity > 0.6:
        ctx.play_effect("tear_drop", 2000)
    elif emotion == "angry" and intensity > 0.7:
        ctx.play_effect("anger_mark", 2000)


def on_state_update(ctx) -> None:
    """
    状态更新时的响应（可选）
    Response to state update (optional)
    
    每隔固定间隔（默认 1 秒）调用一次。
    Called at fixed intervals (default 1 second).
    
    可用于检测状态变化并触发动画。
    Can be used to detect state changes and trigger animations.
    """
    # 示例：长时间未交互时打哈欠
    if ctx.interaction.last_interaction_seconds > 300:  # 5分钟
        if ctx.random() < 0.1:  # 10% 概率
            ctx.play_action("yawn")


def on_interaction(ctx, interaction_type: str) -> None:
    """
    用户交互时的响应（可选）
    Response to user interaction (optional)
    
    Args:
        ctx: ScriptContext 实例
        interaction_type: 交互类型
            - "click": 单击
            - "double_click": 双击
            - "drag_start": 开始拖拽
            - "drag_end": 结束拖拽
            - "pet": 抚摸（长按）
            - "chat": 聊天输入
    """
    if interaction_type == "pet":
        if ctx.state.affection > 0.7:
            ctx.play_action("happy_wiggle")
            ctx.play_effect("heart", 2000)
        else:
            ctx.play_action("shy_look")
    elif interaction_type == "click":
        if ctx.state.mood > 0.5:
            ctx.play_action("wave")


def get_idle_animation(ctx) -> str:
    """
    获取当前应该使用的待机动画（可选）
    Get current idle animation to use (optional)
    
    可以根据状态返回不同的待机动画变体。
    Can return different idle animation variants based on state.
    
    Returns:
        待机动画名称（默认 "idle"）
    """
    if ctx.state.energy < 0.2:
        return "idle_tired"
    elif ctx.state.mood > 0.8:
        return "idle_happy"
    elif ctx.time.is_night:
        return "idle_sleepy"
    return "idle"
```

---

## 4. 沙盒安全设计

### 4.1 安全约束

| 约束 | 实现方式 |
|------|----------|
| **禁止文件访问** | 不暴露 `open`, `os`, `pathlib` 等 |
| **禁止网络访问** | 不暴露 `socket`, `urllib`, `requests` 等 |
| **禁止系统调用** | 不暴露 `subprocess`, `os.system` 等 |
| **禁止代码执行** | 不暴露 `exec`, `eval`, `compile`, `__import__` |
| **超时限制** | 脚本执行超过 10ms 自动终止 |
| **内存限制** | 限制脚本可分配的内存 |
| **调用深度限制** | 限制递归深度（默认 50） |

### 4.2 白名单内置函数

```python
SAFE_BUILTINS = {
    # 类型
    "int", "float", "str", "bool", "list", "dict", "tuple", "set",
    
    # 数学
    "abs", "min", "max", "sum", "round",
    
    # 序列操作
    "len", "range", "enumerate", "zip", "sorted", "reversed",
    
    # 条件
    "all", "any", "isinstance",
    
    # 特殊
    "True", "False", "None",
}
```

### 4.3 沙盒实现方案

**方案 A: RestrictedPython（推荐）**

```python
from RestrictedPython import compile_restricted, safe_globals

def execute_behavior_script(script_code: str, context: ScriptContext) -> Any:
    """在沙盒中执行行为脚本"""
    
    # 编译为受限字节码
    byte_code = compile_restricted(
        script_code,
        filename="<behavior>",
        mode="exec",
    )
    
    # 准备安全的全局命名空间
    safe_env = safe_globals.copy()
    safe_env["ctx"] = context
    safe_env["__builtins__"] = SAFE_BUILTINS
    
    # 执行
    exec(byte_code, safe_env)
    
    return safe_env
```

**方案 B: AST 过滤 + exec**

```python
import ast

class SafetyChecker(ast.NodeVisitor):
    """检查 AST 中的不安全节点"""
    
    FORBIDDEN_NODES = {
        ast.Import, ast.ImportFrom,  # 禁止导入
        ast.Exec,                     # 禁止 exec
    }
    
    FORBIDDEN_NAMES = {
        "__import__", "exec", "eval", "compile",
        "open", "file", "input",
        "globals", "locals", "vars",
        "__builtins__", "__class__", "__bases__",
    }
    
    def visit(self, node):
        if type(node) in self.FORBIDDEN_NODES:
            raise SecurityError(f"Forbidden node: {type(node).__name__}")
        return super().visit(node)
    
    def visit_Name(self, node):
        if node.id in self.FORBIDDEN_NAMES:
            raise SecurityError(f"Forbidden name: {node.id}")
        return node
    
    def visit_Attribute(self, node):
        if node.attr.startswith("_"):
            raise SecurityError(f"Forbidden attribute: {node.attr}")
        return self.generic_visit(node)
```

---

## 5. 集成设计

### 5.1 与 AnimationController 集成

```python
class AnimationController:
    """动画控制器 - 集成脚本系统"""
    
    def __init__(self, ...):
        ...
        # 脚本系统
        self._behavior_manager: Optional[BehaviorManager] = None
        self._script_context: Optional[ScriptContext] = None
    
    def load_character(self, character_path: Path) -> None:
        """
        加载角色资源和行为脚本
        Load character resources and behavior script
        """
        # 加载 manifest.json
        manifest = self._load_manifest(character_path / "manifest.json")
        
        # 加载 behavior.py（如果存在）
        behavior_path = character_path / "behavior.py"
        if behavior_path.exists():
            self._behavior_manager = BehaviorManager(
                script_path=behavior_path,
                context=self._create_script_context(),
            )
            logger.info(f"已加载行为脚本: {behavior_path}")
        else:
            logger.info("未找到行为脚本，使用 JSON 配置")
    
    def _schedule_next_random_action(self) -> None:
        """调度下一个随机动作"""
        
        if self._behavior_manager:
            # 使用脚本获取动作列表
            actions = self._behavior_manager.get_random_actions()
            interval = self._behavior_manager.get_current_interval()
        else:
            # 回退到 JSON 配置
            actions = self._random_action_config.get("actions", [])
            interval = self._calculate_interval_from_config()
        
        ...
    
    def on_emotion_change(self, emotion: str, intensity: float) -> None:
        """情感变化回调"""
        
        if self._behavior_manager:
            self._behavior_manager.on_emotion_change(emotion, intensity)
        
        # 继续默认处理
        ...
```

### 5.2 与 StateManager 集成

```python
class ScriptContext:
    """脚本上下文 - 连接 StateManager"""
    
    def __init__(self, state_manager: StateManager, ...):
        self._state_manager = state_manager
    
    @property
    def state(self) -> StateView:
        """创建状态的只读视图"""
        current = self._state_manager.get_current_state()
        return StateView(
            mood=current.mood,
            energy=current.energy,
            affection=current.affection,
            hunger=current.hunger,
            emotion=current.emotion.tag if current.emotion else "neutral",
            emotion_intensity=current.emotion.intensity if current.emotion else 0.0,
        )
```

### 5.3 与 Plugin 系统复用

```
src/rainze/
├── sandbox/                    # 共享沙盒基础设施
│   ├── __init__.py
│   ├── executor.py             # 沙盒执行器
│   ├── builtins.py             # 安全内置函数
│   └── security.py             # 安全检查
├── animation/
│   └── script/
│       ├── context.py          # 动画脚本上下文
│       └── manager.py          # 使用 sandbox.executor
└── plugin/
    └── script/
        ├── context.py          # 插件脚本上下文
        └── manager.py          # 使用 sandbox.executor
```

---

## 6. 配置示例

### 6.1 manifest.json（静态配置）

```json
{
  "$schema": "animation-manifest.schema.json",
  "character": "fox_girl",
  "version": "1.0.0",
  
  "animations": {
    "idle": {
      "type": "loop",
      "frames": [
        { "file": "frame_001.png", "duration_ms": 100 }
      ]
    },
    
    "idle_happy": {
      "type": "loop",
      "frames": [
        { "file": "frame_001.png", "duration_ms": 80 },
        { "file": "frame_002.png", "duration_ms": 80 }
      ]
    },
    
    "idle_tired": {
      "type": "loop",
      "frames": [
        { "file": "frame_001.png", "duration_ms": 150 }
      ]
    },
    
    "ear_wiggle": {
      "type": "action",
      "frames": [
        { "file": "frame_001.png", "duration_ms": 100 },
        { "file": "frame_002.png", "duration_ms": 100 },
        { "file": "frame_003.png", "duration_ms": 100 },
        { "file": "frame_002.png", "duration_ms": 100 }
      ]
    },
    
    "happy_bounce": {
      "type": "action",
      "frames": [
        { "file": "frame_001.png", "duration_ms": 80 },
        { "file": "frame_002.png", "duration_ms": 80 },
        { "file": "frame_003.png", "duration_ms": 80 },
        { "file": "frame_002.png", "duration_ms": 80 },
        { "file": "frame_001.png", "duration_ms": 80 }
      ]
    },
    
    "celebrate": {
      "type": "action",
      "frames": [...]
    },
    
    "thinking": {
      "type": "triggered",
      "frames": [
        { "file": "frame_001.png", "duration_ms": 500 }
      ]
    }
  },
  
  "effects": {
    "sparkle": { "sprite_sheet": "effects/sparkle.png", "frame_count": 8 },
    "heart": { "sprite_sheet": "effects/heart.png", "frame_count": 6 },
    "tear_drop": { "sprite_sheet": "effects/tear.png", "frame_count": 4 },
    "anger_mark": { "sprite_sheet": "effects/anger.png", "frame_count": 4 }
  },
  
  "fallback": {
    "random_actions": {
      "enabled": true,
      "min_interval_ms": 3000,
      "max_interval_ms": 8000,
      "actions": ["ear_wiggle", "blink"]
    }
  }
}
```

### 6.2 behavior.py（动态逻辑）

```python
"""
狐耳娘行为脚本
Fox Girl Behavior Script
"""


def get_random_actions(ctx):
    """根据状态返回随机动作列表"""
    actions = ["blink"]
    
    mood = ctx.state.mood
    energy = ctx.state.energy
    affection = ctx.state.affection
    
    # 高好感度解锁更多动作
    if affection > 0.5:
        actions.append("ear_wiggle")
    if affection > 0.7:
        actions.append("tail_wag")
    if affection > 0.9:
        actions.append("happy_bounce")
    
    # 根据心情调整频率
    if mood > 0.7:
        ctx.set_interval(2000, 4000)
    elif mood > 0.4:
        ctx.set_interval(3000, 7000)
    else:
        ctx.set_interval(5000, 10000)
        actions.append("sigh")
    
    # 疲劳时
    if energy < 0.3:
        actions.append("yawn")
        ctx.set_interval(6000, 12000)
    
    # 夜间
    if ctx.time.is_night:
        actions.append("sleepy_nod")
    
    return actions


def on_emotion_change(ctx, emotion, intensity):
    """情感变化响应"""
    
    if emotion == "happy":
        if intensity > 0.8:
            ctx.play_action("celebrate")
            ctx.play_effect("sparkle", 3000)
        elif intensity > 0.5:
            ctx.play_effect("sparkle", 1500)
    
    elif emotion == "shy":
        if intensity > 0.6:
            ctx.play_action("hide_face")
        ctx.play_effect("heart", 2000)
    
    elif emotion == "sad":
        if intensity > 0.7:
            ctx.play_effect("tear_drop", 3000)
    
    elif emotion == "excited":
        ctx.play_action("happy_bounce")
        ctx.play_effect("sparkle", 2000)


def on_interaction(ctx, interaction_type):
    """用户交互响应"""
    
    if interaction_type == "pet":
        # 抚摸时的反应取决于好感度
        if ctx.state.affection > 0.8:
            ctx.play_action("happy_wiggle")
            ctx.play_effect("heart", 2000)
        elif ctx.state.affection > 0.5:
            ctx.play_action("ear_wiggle")
        else:
            ctx.play_action("shy_look")
    
    elif interaction_type == "click":
        # 点击时打招呼
        if ctx.random() < 0.3:
            ctx.play_action("wave")
    
    elif interaction_type == "drag_end":
        # 被拖拽后
        if ctx.state.mood < 0.3:
            ctx.play_effect("sweat", 1500)


def get_idle_animation(ctx):
    """选择待机动画变体"""
    
    if ctx.state.energy < 0.2:
        return "idle_tired"
    elif ctx.state.mood > 0.8:
        return "idle_happy"
    elif ctx.time.is_night and ctx.time.hour >= 23:
        return "idle_sleepy"
    return "idle"


def on_state_update(ctx):
    """周期性状态检查"""
    
    # 长时间未交互时打哈欠
    idle_seconds = ctx.interaction.last_interaction_seconds
    
    if idle_seconds > 300 and ctx.random() < 0.05:  # 5分钟后，5%概率
        ctx.play_action("yawn")
    
    # 非常开心时随机蹦跶
    if ctx.state.mood > 0.9 and ctx.random() < 0.02:  # 2%概率
        ctx.play_action("happy_bounce")
```

---

## 7. 性能考虑

### 7.1 执行频率

| 函数 | 调用频率 | 超时限制 |
|------|----------|----------|
| `get_random_actions()` | 每次调度随机动作时 | 10ms |
| `on_emotion_change()` | 情感变化时 | 10ms |
| `on_interaction()` | 用户交互时 | 10ms |
| `on_state_update()` | 每秒一次 | 5ms |
| `get_idle_animation()` | 返回 idle 时 | 5ms |

### 7.2 缓存策略

```python
class BehaviorManager:
    """行为管理器 - 带缓存"""
    
    def __init__(self, ...):
        # 缓存上次的动作列表（避免频繁执行脚本）
        self._cached_actions: List[str] = []
        self._cached_interval: Tuple[int, int] = (3000, 8000)
        self._cache_valid_until: float = 0
        self._cache_ttl: float = 1.0  # 缓存有效期 1 秒
    
    def get_random_actions(self) -> List[str]:
        """获取随机动作列表（带缓存）"""
        
        now = time.time()
        if now < self._cache_valid_until:
            return self._cached_actions
        
        # 执行脚本
        try:
            actions = self._execute_function("get_random_actions")
            self._cached_actions = actions
            self._cache_valid_until = now + self._cache_ttl
        except ScriptError as e:
            logger.warning(f"脚本执行失败: {e}")
            # 返回缓存或默认值
        
        return self._cached_actions
```

---

## 8. 错误处理

### 8.1 脚本错误类型

```python
class ScriptError(Exception):
    """脚本执行错误基类"""
    pass

class ScriptSyntaxError(ScriptError):
    """脚本语法错误"""
    pass

class ScriptSecurityError(ScriptError):
    """脚本安全违规"""
    pass

class ScriptTimeoutError(ScriptError):
    """脚本执行超时"""
    pass

class ScriptRuntimeError(ScriptError):
    """脚本运行时错误"""
    pass
```

### 8.2 错误恢复策略

```python
def execute_with_fallback(func_name: str, fallback_value: Any) -> Any:
    """带回退的脚本执行"""
    
    try:
        return self._executor.call(func_name, self._context)
    except ScriptSyntaxError as e:
        # 语法错误：禁用脚本，使用 JSON 配置
        logger.error(f"脚本语法错误，已禁用: {e}")
        self._script_enabled = False
        return fallback_value
    except ScriptSecurityError as e:
        # 安全违规：禁用脚本，记录警告
        logger.warning(f"脚本安全违规，已禁用: {e}")
        self._script_enabled = False
        return fallback_value
    except ScriptTimeoutError as e:
        # 超时：本次使用回退值，不禁用
        logger.warning(f"脚本执行超时: {e}")
        return fallback_value
    except ScriptRuntimeError as e:
        # 运行时错误：本次使用回退值，不禁用
        logger.warning(f"脚本运行时错误: {e}")
        return fallback_value
```

---

## 9. 测试策略

### 9.1 单元测试

```python
# tests/unit/animation/test_behavior_script.py

class TestBehaviorScript:
    """行为脚本测试"""
    
    def test_get_random_actions_high_mood(self):
        """高心情时返回更多动作"""
        ctx = MockScriptContext(mood=0.9, energy=0.8)
        manager = BehaviorManager(SAMPLE_SCRIPT, ctx)
        
        actions = manager.get_random_actions()
        
        assert "happy_bounce" in actions
        assert manager.get_current_interval() == (2000, 4000)
    
    def test_get_random_actions_low_energy(self):
        """低精力时包含打哈欠"""
        ctx = MockScriptContext(mood=0.5, energy=0.2)
        manager = BehaviorManager(SAMPLE_SCRIPT, ctx)
        
        actions = manager.get_random_actions()
        
        assert "yawn" in actions
    
    def test_script_timeout(self):
        """脚本超时测试"""
        infinite_loop_script = """
def get_random_actions(ctx):
    while True:
        pass
"""
        ctx = MockScriptContext()
        manager = BehaviorManager(infinite_loop_script, ctx)
        
        # 应该超时并返回回退值
        actions = manager.get_random_actions()
        assert actions == DEFAULT_ACTIONS
    
    def test_script_security_violation(self):
        """脚本安全违规测试"""
        malicious_script = """
import os
def get_random_actions(ctx):
    os.system("rm -rf /")
    return []
"""
        ctx = MockScriptContext()
        
        with pytest.raises(ScriptSecurityError):
            BehaviorManager(malicious_script, ctx)
```

### 9.2 集成测试

```python
# tests/integration/test_animation_script_integration.py

class TestAnimationScriptIntegration:
    """动画脚本集成测试"""
    
    async def test_emotion_triggers_script_action(self):
        """情感变化触发脚本动作"""
        controller = AnimationController(...)
        controller.load_character(Path("assets/animations/fox_girl"))
        
        # 触发高强度开心情感
        controller.on_emotion_change("happy", 0.9)
        
        # 验证播放了庆祝动作和特效
        assert controller.current_action == "celebrate"
        assert "sparkle" in controller.active_effects
```

---

## 10. 实现路线图

### Phase 1: 基础设施 (P0)

- [ ] 创建 `src/rainze/sandbox/` 沙盒基础设施
- [ ] 实现 `SandboxExecutor` 沙盒执行器
- [ ] 实现安全检查和白名单
- [ ] 单元测试

### Phase 2: 动画脚本系统 (P0)

- [ ] 创建 `src/rainze/animation/script/` 目录
- [ ] 实现 `ScriptContext` 脚本上下文
- [ ] 实现 `BehaviorManager` 行为管理器
- [ ] 集成到 `AnimationController`

### Phase 3: 示例脚本 (P1)

- [ ] 创建示例 `behavior.py` 脚本
- [ ] 更新 `manifest.json` 格式
- [ ] 文档和使用指南

### Phase 4: 调试工具 (P2)

- [ ] 脚本热重载
- [ ] 脚本调试日志
- [ ] 错误报告界面

---

**文档版本历史**:

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0.0 | 2025-12-30 | 初始版本 |
