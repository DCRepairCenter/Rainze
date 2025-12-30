<a id="readme-top"></a>

[![Status][status-shield]][status-url]

# AI 模块 / AI Module

> AI 服务层，提供 LLM 调用和三层响应生成策略。
> AI service layer providing LLM calls and three-tier response generation.

## 📖 目录 / Contents

- [关于模块 / About](#关于模块--about)
- [架构设计 / Architecture](#架构设计--architecture)
- [快速开始 / Quick Start](#快速开始--quick-start)
- [API 参考 / API Reference](#api-参考--api-reference)
- [配置说明 / Configuration](#配置说明--configuration)
- [依赖关系 / Dependencies](#依赖关系--dependencies)

## 关于模块 / About

AI 模块是 Rainze 的智能核心，负责：

- **LLM 调用**: 统一的 API 调用接口，支持 Anthropic、OpenAI 等
- **响应生成**: 三层响应策略 (Tier1 模板 / Tier2 规则 / Tier3 LLM)
- **配置管理**: Pydantic 配置验证

The AI module is Rainze's intelligent core, responsible for:

- **LLM Calls**: Unified API interface supporting Anthropic, OpenAI, etc.
- **Response Generation**: Three-tier strategy (Tier1 template / Tier2 rule / Tier3 LLM)
- **Configuration**: Pydantic config validation

### 技术栈 / Tech Stack

* ![Python](https://img.shields.io/badge/Python-3.12+-blue)
* ![httpx](https://img.shields.io/badge/httpx-0.28+-green)
* ![Pydantic](https://img.shields.io/badge/Pydantic-2.10+-purple)

<p align="right">(<a href="#readme-top">返回顶部 / Back to top</a>)</p>

## 架构设计 / Architecture

```
ai/
├── __init__.py              # 模块导出 / Module exports
├── exceptions.py            # 异常定义 / Exception definitions
├── schemas.py               # Pydantic 配置 / Pydantic config
├── llm/
│   ├── __init__.py
│   ├── client.py            # LLM 客户端抽象 / LLM client abstraction
│   └── providers/
│       ├── __init__.py
│       └── anthropic.py     # Anthropic 实现 / Anthropic implementation
└── generation/
    ├── __init__.py
    ├── strategy.py          # 响应策略协调器 / Strategy coordinator
    ├── tier1_template.py    # Tier1 模板 / Tier1 template
    ├── tier2_rule.py        # Tier2 规则 / Tier2 rule
    └── tier3_llm.py         # Tier3 LLM / Tier3 LLM
```

### 三层响应策略 / Three-Tier Response Strategy

```
[用户输入/事件] → [场景判断] → [Tier 选择]
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        ↓                         ↓                         ↓
   [Tier 1]                  [Tier 2]                  [Tier 3]
   模板响应                   规则生成                  LLM 生成
   <50ms                     <100ms                   500-2000ms
```

<p align="right">(<a href="#readme-top">返回顶部 / Back to top</a>)</p>

## 快速开始 / Quick Start

### 前置条件 / Prerequisites

* Python 3.12+
* `ANTHROPIC_API_KEY` 环境变量 / environment variable

### 使用示例 / Usage Example

```python
from rainze.ai import (
    LLMClientFactory,
    LLMProvider,
    Tier1TemplateGenerator,
    Tier2RuleGenerator,
    Tier3LLMGenerator,
    ResponseGenerator,
)

# 创建 LLM 客户端 / Create LLM client
client = LLMClientFactory.create(
    provider=LLMProvider.ANTHROPIC,
    api_key="your-api-key"
)

# 创建生成器 / Create generators
tier1 = Tier1TemplateGenerator()
tier2 = Tier2RuleGenerator()
tier3 = Tier3LLMGenerator(client)

# 创建协调器 / Create coordinator
generator = ResponseGenerator(tier1, tier2, tier3)

# 生成响应 / Generate response
response = await generator.generate(
    scene_type="conversation",
    scene_context={"topic": "weather"},
    user_input="今天天气怎么样？"
)

print(response.text)
print(response.emotion_tag)
print(response.tier_used)
```

<p align="right">(<a href="#readme-top">返回顶部 / Back to top</a>)</p>

## API 参考 / API Reference

### `LLMClient`

LLM 客户端抽象基类。

| 方法 / Method | 参数 / Args | 返回 / Returns | 说明 / Description |
|---------------|-------------|----------------|---------------------|
| `generate()` | `request: LLMRequest` | `LLMResponse` | 同步生成 / Sync generate |
| `generate_stream()` | `request: LLMRequest` | `AsyncIterator[str]` | 流式生成 / Stream generate |

### `ResponseGenerator`

响应生成协调器。

| 方法 / Method | 参数 / Args | 返回 / Returns | 说明 / Description |
|---------------|-------------|----------------|---------------------|
| `generate()` | `scene_type, context, user_input` | `GeneratedResponse` | 生成响应 / Generate response |

### `GeneratedResponse`

| 字段 / Field | 类型 / Type | 说明 / Description |
|--------------|-------------|---------------------|
| `text` | `str` | 响应文本 / Response text |
| `emotion_tag` | `EmotionTag?` | 情感标签 / Emotion tag |
| `tier_used` | `ResponseTier` | 使用的层级 / Tier used |
| `latency_ms` | `float` | 延迟（毫秒）/ Latency (ms) |

<p align="right">(<a href="#readme-top">返回顶部 / Back to top</a>)</p>

## 配置说明 / Configuration

配置文件: `config/api_settings.json`

```json
{
  "primary_api": {
    "provider": "anthropic",
    "api_key_env": "ANTHROPIC_API_KEY",
    "default_model": "claude-sonnet-4-20250514",
    "timeout_seconds": 30
  },
  "generation": {
    "default_temperature": 0.8,
    "default_max_tokens": 150,
    "tier3_timeout_seconds": 3
  }
}
```

<p align="right">(<a href="#readme-top">返回顶部 / Back to top</a>)</p>

## 依赖关系 / Dependencies

### 依赖的模块 / Depends On

- `rainze.core.contracts` - EmotionTag, ResponseTier
- `rainze.core.exceptions` - RainzeError

### 被依赖于 / Depended By

- `rainze.agent` - Agent 循环调用 AI 服务
- `rainze.features` - 功能模块使用生成能力

<p align="right">(<a href="#readme-top">返回顶部 / Back to top</a>)</p>

<!-- MARKDOWN LINKS -->
[status-shield]: https://img.shields.io/badge/Status-开发中-yellow
[status-url]: #
