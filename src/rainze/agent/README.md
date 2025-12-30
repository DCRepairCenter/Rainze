<a id="readme-top"></a>

<!-- 模块徽章 -->
[![Status][status-shield]][status-url]

# Agent 模块 - 统一上下文管理

> Rainze 的"大脑"：所有用户交互的唯一入口点

## 📖 目录

- [关于模块](#关于模块)
- [架构设计](#架构设计)
- [快速开始](#快速开始)
- [API 参考](#api-参考)
- [配置说明](#配置说明)
- [依赖关系](#依赖关系)

## 关于模块

Agent 模块负责统一上下文管理 (UCM)，是 Rainze 所有用户交互的唯一入口点。

### 核心职责

| 职责 | 说明 |
|------|------|
| **统一入口** | 所有交互（对话、游戏、工具、插件、系统事件）必须通过 UCM |
| **场景分类** | 判断交互类型，路由到正确的响应层级 |
| **3层响应** | Tier1模板(<50ms) / Tier2规则(<100ms) / Tier3 LLM(<3s) |
| **状态一致性** | 确保状态变化实时同步 |
| **记忆完整性** | 所有交互都按策略写入记忆系统 |

### 技术栈

* ![Python](https://img.shields.io/badge/Python-3.12+-blue)
* asyncio 异步框架
* dataclasses 数据类

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

## 架构设计

```
src/rainze/agent/
├── __init__.py              # 模块导出
├── context_manager.py       # 统一上下文管理器 (UCM) ⭐核心
├── scene_classifier.py      # 场景分类器
├── tier_handlers.py         # 3层响应处理器
├── README.md                # 模块说明
├── TODO.md                  # 任务追踪
└── CHANGELOG.md             # 变更记录
```

### 处理流程

```
用户交互 ─────────────────────────────────────────────────────────────►
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    UnifiedContextManager (UCM)                       │
├─────────────────────────────────────────────────────────────────────┤
│  1. 创建上下文   2. 场景分类   3. 记忆检索   4. 路由处理   5. 后处理  │
│       │              │             │             │           │       │
│       ▼              ▼             ▼             ▼           ▼       │
│  InteractionContext  SceneClassifier  Memory   TierHandlers  State  │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
InteractionResponse ◄─────────────────────────────────────────────────
```

### 场景分类规则

| 场景类型 | 条件 | 响应层级 | 延迟 |
|----------|------|----------|------|
| SIMPLE | 点击、拖拽、短确认 | Tier1 | <50ms |
| MEDIUM | 整点报时、系统警告 | Tier2 | <100ms |
| COMPLEX | 自由对话、情感分析 | Tier3 | <3s |

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

## 快速开始

### 前置条件

* Python 3.12+
* rainze.core 模块（contracts, exceptions）

### 基本使用

```python
from rainze.agent import UnifiedContextManager, SceneClassifier
from rainze.core.contracts import InteractionRequest, InteractionSource

# 创建 UCM 实例
ucm = UnifiedContextManager()

# 创建交互请求
request = InteractionRequest.create(
    source=InteractionSource.CHAT_INPUT,
    payload={"text": "你好呀~"}
)

# 处理交互
response = await ucm.process_interaction(request)
print(response.response_text)  # "你好呀！今天过得怎么样？"
```

### 自定义模板响应

```python
from rainze.core.contracts import EmotionTag

# 获取 Tier1 处理器
tier1 = ucm.get_tier_handlers().get_tier1_handler()

# 添加自定义模板
tier1.add_template(
    scene_id="feed",
    templates=["谢谢投喂！", "好好吃~", "还要还要！"],
    emotion=EmotionTag(tag="happy", intensity=0.8)
)
```

### 注册自定义规则

```python
# 获取 Tier2 处理器
tier2 = ucm.get_tier_handlers().get_tier2_handler()

# 注册自定义规则
def my_rule(context: dict) -> tuple[str, EmotionTag]:
    value = context.get("value", 0)
    return f"收到数值: {value}", EmotionTag.default()

tier2.register_rule("my_scene", my_rule)
```

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

## API 参考

### `UnifiedContextManager`

统一上下文管理器，所有交互的唯一入口。

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `process_interaction()` | `request: InteractionRequest` | `InteractionResponse` | 处理交互的主入口 |
| `get_context_summary()` | - | `Dict[str, Any]` | 获取 UCM 状态摘要 |
| `register_custom_handler()` | `source, handler` | `None` | 注册自定义处理器 |
| `get_scene_classifier()` | - | `SceneClassifier` | 获取场景分类器 |
| `get_tier_handlers()` | - | `TierHandlerRegistry` | 获取层级处理器注册表 |

### `SceneClassifier`

场景分类器，根据交互来源和内容判断场景类型。

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `classify()` | `source, event_type, user_input, context` | `ClassificationResult` | 分类场景 |
| `add_rule()` | `rule: ClassificationRule` | `None` | 添加自定义规则 |
| `add_simple_event_type()` | `event_type: str` | `None` | 添加简单事件类型 |
| `add_complex_keyword()` | `keyword: str` | `None` | 添加复杂场景关键词 |

### `TierHandlerRegistry`

层级处理器注册表。

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `register()` | `handler: BaseTierHandler` | `None` | 注册处理器 |
| `get()` | `tier: ResponseTier` | `BaseTierHandler` | 获取指定层级处理器 |
| `handle_with_fallback()` | `request, classification, context` | `TierResponse` | 带降级链的处理 |

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

## 配置说明

相关配置文件：`config/scene_tier_mapping.json`

| 场景ID | 场景类型 | 默认层级 | 超时(ms) | 记忆检索 |
|--------|----------|----------|----------|----------|
| `click` | SIMPLE | TIER1 | 50 | none |
| `drag` | SIMPLE | TIER1 | 50 | none |
| `hourly_chime` | MEDIUM | TIER2 | 100 | facts_summary |
| `conversation` | COMPLEX | TIER3 | 3000 | full |

### 记忆写入策略

| 交互来源 | 策略 | 默认重要度 |
|----------|------|------------|
| CHAT_INPUT | FULL | 0.6 |
| GAME_INTERACTION | RESULT_ONLY | 0.3 |
| TOOL_RESULT | SUMMARY | 0.5 |
| SYSTEM_EVENT | SUMMARY | 0.5 |
| PASSIVE_TRIGGER | NONE | 0.0 |

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

## 依赖关系

### 依赖的模块
- `rainze.core.contracts` - 共享类型定义（InteractionRequest, SceneType 等）
- `rainze.core.exceptions` - 基础异常类

### 被依赖于
- `rainze.gui` - GUI 层通过 UCM 处理用户交互
- `rainze.features` - 功能模块通过 UCM 处理特定交互

### 未来依赖（TODO）
- `rainze.memory` - 记忆系统集成
- `rainze.state` - 状态管理集成
- `rainze.ai` - AI 服务集成（Tier3）
- `rainze.core.observability` - 可观测性追踪

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

<!-- MARKDOWN LINKS -->
[status-shield]: https://img.shields.io/badge/Status-P0%20开发中-yellow
[status-url]: #
