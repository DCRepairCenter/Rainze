"""
检索系统
Retrieval System

本模块导出记忆检索相关的类。
This module exports memory retrieval related classes.

Exports:
    - FTSSearcher: FTS5 全文检索器 / FTS5 full-text searcher
    - FTSConfig: FTS5 配置 / FTS5 configuration

Reference:
    - MOD-Memory.md §3.3: HybridRetriever

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from .fts_searcher import FTSConfig, FTSSearcher

__all__: list[str] = [
    "FTSSearcher",
    "FTSConfig",
]
