"""
检索系统
Retrieval System

本模块导出记忆检索相关的类。
This module exports memory retrieval related classes.

Exports:
    - FTSSearcher: FTS5 全文检索器 / FTS5 full-text searcher
    - FTSConfig: FTS5 配置 / FTS5 configuration
    - VectorSearcher: FAISS 向量检索器 / FAISS vector searcher
    - VectorSearcherConfig: FAISS 配置 / FAISS configuration
    - TextEmbedder: 文本嵌入器 / Text embedder
    - EmbedderConfig: Embedding 配置 / Embedding configuration
    - EmbeddingResult: Embedding 结果 / Embedding result
    - HybridRetriever: 混合检索器 / Hybrid retriever
    - HybridRetrieverConfig: 混合检索配置 / Hybrid retriever config
    - RetrievalStrategy: 检索策略枚举 / Retrieval strategy enum

Reference:
    - MOD-Memory.md §3.3: HybridRetriever

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from .embedder import EmbedderConfig, EmbeddingResult, TextEmbedder
from .fts_searcher import FTSConfig, FTSSearcher
from .hybrid_retriever import HybridRetriever, HybridRetrieverConfig, RetrievalStrategy
from .vector_searcher import VectorSearcher, VectorSearcherConfig

__all__: list[str] = [
    # FTS5 全文检索 / FTS5 full-text search
    "FTSSearcher",
    "FTSConfig",
    # FAISS 向量检索 / FAISS vector search
    "VectorSearcher",
    "VectorSearcherConfig",
    # 文本嵌入 / Text embedding
    "TextEmbedder",
    "EmbedderConfig",
    "EmbeddingResult",
    # 混合检索 / Hybrid retrieval
    "HybridRetriever",
    "HybridRetrieverConfig",
    "RetrievalStrategy",
]
