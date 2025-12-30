<a id="readme-top"></a>

<!-- 模块徽章 -->
[![Status][status-shield]][status-url]
[![Python][python-shield]][python-url]

# 状态管理模块 (State Module)

> 管理桌宠的核心状态：情绪、能量、好感度

## 📖 目录

- [关于模块](#关于模块)
- [架构设计](#架构设计)
- [快速开始](#快速开始)
- [API 参考](#api-参考)
- [配置说明](#配置说明)
- [依赖关系](#依赖关系)

## 关于模块

状态管理模块负责桌宠的核心状态维护，包括：

- **情绪状态机**: 5态+子态的混合驱动情绪系统
- **数值状态**: 能量、好感度的管理与计算
- **状态同步**: 单一数据源、变更通知机制

### 设计哲学

```
轻度养成 × 自适应主动性 = 有生命感，但不是负担

核心原则：
- 用"情感共鸣"替代"惩罚机制"
- 桌宠不会因为被忽略而"死亡"
- 规则层始终优先于LLM层
```

### 技术栈

* ![Python](https://img.shields.io/badge/Python-3.12+-blue)
* dataclasses - 数据类
* enum - 枚举类型

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

## 架构设计

```
src/rainze/state/
├── __init__.py              # 模块导出
├── manager.py               # StateManager 状态管理器
├── emotion/
│   ├── __init__.py
│   ├── states.py            # MoodState, MoodSubState 枚举
│   └── state_machine.py     # EmotionStateMachine 状态机
├── attributes/
│   ├── __init__.py
│   ├── base.py              # AttributeManager 抽象基类
│   ├── energy.py            # EnergyManager 能量管理
│   └── affinity.py          # AffinityManager 好感度管理
└── models/
    ├── __init__.py
    └── events.py            # 状态变化事件
```

### 状态优先级矩阵

| 状态 | 优先级 | 可覆盖性 | 触发条件 |
|------|--------|----------|----------|
| Sleeping | 100 | 不可覆盖 | 睡眠中 |
| Tired_LowEnergy | 90 | 不可覆盖 | energy < 20 |
| Anxious | 50 | 可覆盖 | 用户异常行为 |
| Sad | 40 | 可覆盖 | 连续负面事件 |
| Happy | 10 | 可覆盖 | 正面交互 |
| Normal | 0 | 基准态 | 默认状态 |

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

## 快速开始

### 前置条件

* Python 3.12+
* rainze.core.contracts 模块

### 基础使用

```python
from rainze.state import StateManager, StateConfig

# 创建状态管理器
state_manager = StateManager(config=StateConfig())

# 启动
await state_manager.start()

# 访问各子管理器
print(f"当前情绪: {state_manager.emotion.main_mood}")
print(f"当前能量: {state_manager.energy.value}")
print(f"当前好感度: {state_manager.affinity.value}")

# 修改状态
state_manager.energy.subtract(10, "用户互动")
state_manager.affinity.add(5, "完成对话")

# 获取状态快照
snapshot = state_manager.get_snapshot()
```

### 情绪状态机使用

```python
from rainze.state import EmotionStateMachine, MoodState

# 创建状态机
emotion = EmotionStateMachine()

# 规则层转换（硬约束）
new_state = emotion.apply_rule_transition(
    energy=15,     # 能量低于20触发Tired
    hour=23,
    idle_minutes=10,
    is_sleeping=False
)

# LLM层建议（软决策）
success = emotion.apply_llm_suggestion(
    emotion_tag="happy",
    intensity=0.8,
    context={"interaction": "positive"}
)

# 获取表情
expression = emotion.get_expression()
```

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

## API 参考

### `StateManager`

状态管理器，统一管理所有状态的入口。

| 属性/方法 | 类型 | 说明 |
|----------|------|------|
| `emotion` | `EmotionStateMachine` | 情绪状态机 |
| `energy` | `EnergyManager` | 能量管理器 |
| `affinity` | `AffinityManager` | 好感度管理器 |
| `get_snapshot()` | `StateSnapshot` | 获取状态快照 |
| `restore_from_snapshot(snapshot)` | `None` | 恢复状态 |
| `get_prompt_modifiers()` | `dict` | 获取Prompt修饰 |
| `get_behavior_modifiers()` | `dict` | 获取行为修饰 |

### `EmotionStateMachine`

情绪状态机，实现混合驱动架构。

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `apply_rule_transition()` | `energy, hour, ...` | `Optional[MoodState]` | 规则层转换 |
| `apply_llm_suggestion()` | `emotion_tag, intensity, ...` | `bool` | LLM层建议 |
| `can_transition_to()` | `target_state` | `bool` | 检查可否转换 |
| `transition_to()` | `target_state, reason, ...` | `bool` | 执行转换 |

### `EnergyManager`

能量管理器，范围 0-100。

| 方法 | 说明 |
|------|------|
| `add(amount, reason)` | 增加能量 |
| `subtract(amount, reason)` | 消耗能量 |
| `apply_hourly_decay()` | 应用每小时衰减 |
| `apply_sleep_recovery(hours)` | 应用睡眠恢复 |

### `AffinityManager`

好感度管理器，范围 0-999，5级系统。

| 方法 | 说明 |
|------|------|
| `add(amount, reason)` | 增加好感度 |
| `subtract(amount, reason)` | 减少好感度（有下限保护） |
| `level` | 当前等级 (1-5) |
| `proactivity_multiplier` | 主动性乘数 |

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

## 配置说明

相关配置文件：`config/state_settings.json`

### 能量配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `max_value` | `float` | `100.0` | 最大能量 |
| `initial_value` | `float` | `80.0` | 初始能量 |
| `decay_per_hour` | `float` | `2.0` | 每小时衰减 |
| `critical_threshold` | `float` | `20.0` | 极低阈值 |

### 好感度配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `max_value` | `int` | `999` | 最大好感度 |
| `min_value` | `int` | `10` | 下限保护 |
| `level_thresholds` | `list` | `[0,25,50,75,100]` | 等级阈值 |

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

## 依赖关系

### 依赖的模块
- `rainze.core.contracts` - EmotionTag 共享类型

### 被依赖于
- `rainze.gui` - GUI 层获取状态显示
- `rainze.ai` - AI 服务获取状态修饰
- `rainze.agent` - Agent 循环状态评估

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

<!-- MARKDOWN LINKS -->
[status-shield]: https://img.shields.io/badge/Status-开发中-yellow
[status-url]: #
[python-shield]: https://img.shields.io/badge/Python-3.12+-blue
[python-url]: https://python.org
