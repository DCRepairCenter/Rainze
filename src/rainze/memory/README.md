<a id="readme-top"></a>

<!-- 模块徽章 -->
[![Status][status-shield]][status-url]
[![Python][python-shield]][python-url]

# Memory 模块 - 记忆系统

> Rainze AI 桌宠的 3 层记忆架构实现

## 📖 目录

- [关于模块](#关于模块)
- [架构设计](#架构设计)
- [快速开始](#快速开始)
- [API 参考](#api-参考)
- [配置说明](#配置说明)
- [依赖关系](#依赖关系)

## 关于模块

Memory 模块负责 Rainze 的 3 层记忆架构实现：

| 层级 | 名称 | 说明 | 存储 |
|------|------|------|------|
| Layer 1 | Identity Layer | 身份层 - 角色设定、用户档案 | 永久存储 |
| Layer 2 | Working Memory | 工作记忆 - 会话上下文、对话历史 | 内存级 |
| Layer 3 | Long-term Memory | 长期记忆 - Facts/Episodes/Relations | SQLite |

### 核心能力

- ✅ 记忆的创建、存储、检索
- ✅ FTS5 全文检索
- ✅ 对话历史管理
- ✅ SQLite 异步持久化
- 🔲 向量检索 (FAISS) - 计划中
- 🔲 重要度自动评估 - 计划中
- 🔲 矛盾检测 - 计划中

### 技术栈

* ![Python](https://img.shields.io/badge/Python-3.12+-blue)
* ![SQLite](https://img.shields.io/badge/SQLite-FTS5-green)
* aiosqlite - 异步数据库操作

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

## 架构设计

```
memory/
├── __init__.py              # 模块导出
├── manager.py               # MemoryManager - 主入口
├── exceptions.py            # 异常定义
│
├── models/                  # 数据模型
│   ├── __init__.py
│   ├── memory_item.py       # MemoryItem, FactItem, EpisodeItem
│   └── retrieval_result.py  # RetrievalResult, MemoryIndexItem
│
├── layers/                  # 记忆层实现
│   ├── __init__.py
│   └── working.py           # WorkingMemory (Layer 2)
│
└── retrieval/               # 检索系统
    ├── __init__.py
    └── fts_searcher.py      # FTS5 全文检索
```

### 类图

```
┌─────────────────────────────────────────────────────────────┐
│                      MemoryManager                          │
│  ─────────────────────────────────────────────────────────  │
│  + working_memory: WorkingMemory                            │
│  + fts_searcher: FTSSearcher                                │
│  ─────────────────────────────────────────────────────────  │
│  + initialize() -> None                                     │
│  + create_memory(content, type, ...) -> MemoryItem          │
│  + create_fact(subject, predicate, obj) -> FactItem         │
│  + create_episode(summary, ...) -> EpisodeItem              │
│  + search(query, top_k, ...) -> RetrievalResult             │
│  + get_memory_index(query, count) -> List[MemoryIndexItem]  │
│  + get_conversation_history() -> List[ConversationTurn]     │
│  + add_conversation_turn(role, content) -> None             │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  WorkingMemory   │ │   FTSSearcher    │ │   MemoryItem     │
│  (Layer 2)       │ │   (检索)         │ │   (数据模型)     │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

## 快速开始

### 前置条件

* Python 3.12+
* aiosqlite (`pip install aiosqlite`)

### 基本使用

```python
import asyncio
from rainze.memory import MemoryManager, MemoryType

async def main():
    # 初始化记忆管理器
    manager = MemoryManager()
    await manager.initialize()
    
    # 创建情景记忆
    episode = await manager.create_episode(
        summary="主人说工作压力很大，想休息一下",
        emotion_tag="tired",
        affinity_change=5
    )
    
    # 创建事实记忆
    fact = await manager.create_fact(
        subject="主人",
        predicate="喜欢",
        obj="苹果",
        confidence=0.9
    )
    
    # 检索记忆
    result = await manager.search("主人喜欢什么", top_k=5)
    
    if result.has_results:
        for ranked in result.memories:
            print(f"[{ranked.final_score:.2f}] {ranked.memory.content}")
    
    # 对话历史管理
    manager.add_conversation_turn("user", "你好")
    manager.add_conversation_turn("assistant", "你好呀~")
    
    history = manager.get_conversation_history()
    for turn in history:
        print(f"{turn.role}: {turn.content}")
    
    # 清理
    await manager.close()

asyncio.run(main())
```

### 获取记忆索引（用于 Prompt 注入）

```python
# 获取与查询相关的记忆索引
index_list = await manager.get_memory_index(
    query="水果偏好",
    count=30
)

for item in index_list:
    print(item.format_for_prompt())
    # 输出: #mem_001 [3天前] 主人喜欢苹果 (重要度0.8) ⭐
```

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

## API 参考

### `MemoryManager`

主记忆管理器类。

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `initialize()` | - | `None` | 异步初始化 |
| `close()` | - | `None` | 关闭资源 |
| `create_memory()` | `content, memory_type, ...` | `MemoryItem` | 创建记忆 |
| `create_fact()` | `subject, predicate, obj, ...` | `FactItem` | 创建事实 |
| `create_episode()` | `summary, emotion_tag, ...` | `EpisodeItem` | 创建情景 |
| `search()` | `query, top_k, ...` | `RetrievalResult` | 检索记忆 |
| `get_memory_index()` | `query, count` | `List[MemoryIndexItem]` | 获取索引 |
| `expand_memory()` | `memory_id` | `Optional[MemoryItem]` | 展开记忆 |
| `get_conversation_history()` | `max_turns` | `List[ConversationTurn]` | 获取对话历史 |
| `add_conversation_turn()` | `role, content` | `None` | 添加对话 |
| `clear_conversation()` | - | `None` | 清空对话 |
| `get_stats()` | - | `Dict[str, Any]` | 获取统计 |

### `MemoryType`

记忆类型枚举。

| 值 | 说明 |
|---|------|
| `FACT` | 事实记忆 |
| `EPISODE` | 情景记忆 |
| `RELATION` | 关系记忆 |
| `REFLECTION` | 反思记忆 |

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

## 配置说明

### 默认配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `db_path` | `./data/memory.db` | SQLite 数据库路径 |
| `max_conversation_turns` | `20` | 最大对话轮次 |
| `similarity_threshold` | `0.65` | 相关性阈值 |

### 配置示例

```python
from pathlib import Path

manager = MemoryManager(
    db_path=Path("./custom/path/memory.db"),
    max_conversation_turns=30,
)
```

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

## 依赖关系

### 依赖的模块

- 无（独立模块）

### 被依赖于

- `rainze.agent` - Agent 循环调用记忆检索
- `rainze.ai` - AI 服务获取上下文

### 外部依赖

| 包 | 版本 | 用途 |
|---|------|------|
| `aiosqlite` | >=0.19 | 异步 SQLite 操作 |

<p align="right">(<a href="#readme-top">返回顶部</a>)</p>

<!-- MARKDOWN LINKS -->
[status-shield]: https://img.shields.io/badge/Status-开发中-yellow
[status-url]: #
[python-shield]: https://img.shields.io/badge/Python-3.12+-blue
[python-url]: https://www.python.org/
