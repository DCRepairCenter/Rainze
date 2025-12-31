"""
记忆系统模块
Memory System Module

本模块实现 Rainze 的 3 层记忆架构。
This module implements Rainze's 3-layer memory architecture.

Layer 1 (Identity): 身份层 - 角色设定、用户档案（永久存储）
Layer 2 (Working): 工作记忆 - 会话上下文、对话历史（内存级）
Layer 3 (Long-term): 长期记忆 - Facts/Episodes/Relations（持久化）

Exports:
    - MemoryManager: 记忆管理器主入口 / Main memory manager
    - MemoryType: 记忆类型枚举 / Memory type enum
    - MemoryItem: 记忆项 / Memory item
    - FactItem: 事实记忆项 / Fact item
    - EpisodeItem: 情景记忆项 / Episode item
    - WorkingMemory: 工作记忆 / Working memory
    - ConversationTurn: 对话轮次 / Conversation turn
    - RetrievalResult: 检索结果 / Retrieval result
    - RankedMemory: 排序后的记忆 / Ranked memory
    - MemoryIndexItem: 记忆索引项 / Memory index item
    - TimeWindow: 时间窗口 / Time window
    - FTSSearcher: FTS5 检索器 / FTS5 searcher
    - VectorSearcher: FAISS 向量检索器 / FAISS vector searcher
    - TextEmbedder: 文本嵌入器 / Text embedder
    - HybridRetriever: 混合检索器 / Hybrid retriever
    - RetrievalStrategy: 检索策略 / Retrieval strategy

Exception Exports:
    - MemoryError: 基础异常 / Base exception
    - MemoryNotFoundError: 记忆不存在 / Memory not found
    - RetrievalError: 检索失败 / Retrieval error
    - VectorizeError: 向量化失败 / Vectorize error
    - StorageError: 存储失败 / Storage error
    - MemoryQuotaExceededError: 配额超限 / Quota exceeded

Reference:
    - PRD §0.2, §0.4: 记忆系统需求
    - MOD-Memory.md: 记忆系统模块设计

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

# Exceptions / 异常
from .exceptions import (
    MemoryError,
    MemoryNotFoundError,
    MemoryQuotaExceededError,
    RetrievalError,
    StorageError,
    VectorizeError,
)

# Layers / 记忆层
from .layers import ConversationTurn, WorkingMemory

# Main manager / 主管理器
from .manager import MemoryManager

# Models / 数据模型
from .models import (
    EpisodeItem,
    FactItem,
    MemoryIndexItem,
    MemoryItem,
    MemoryType,
    RankedMemory,
    RetrievalResult,
    TimeWindow,
)

# Retrieval / 检索系统
from .retrieval import (
    EmbedderConfig,
    EmbeddingResult,
    FTSConfig,
    FTSSearcher,
    HybridRetriever,
    HybridRetrieverConfig,
    RetrievalStrategy,
    TextEmbedder,
    VectorSearcher,
    VectorSearcherConfig,
)

__all__: list[str] = [
    # Main manager / 主管理器
    "MemoryManager",
    # Models / 数据模型
    "MemoryType",
    "MemoryItem",
    "FactItem",
    "EpisodeItem",
    "RankedMemory",
    "RetrievalResult",
    "MemoryIndexItem",
    "TimeWindow",
    # Layers / 记忆层
    "WorkingMemory",
    "ConversationTurn",
    # Retrieval / 检索系统
    "FTSSearcher",
    "FTSConfig",
    "VectorSearcher",
    "VectorSearcherConfig",
    "TextEmbedder",
    "EmbedderConfig",
    "EmbeddingResult",
    "HybridRetriever",
    "HybridRetrieverConfig",
    "RetrievalStrategy",
    # Exceptions / 异常
    "MemoryError",
    "MemoryNotFoundError",
    "RetrievalError",
    "VectorizeError",
    "StorageError",
    "MemoryQuotaExceededError",
]
