"""
混合检索器
Hybrid Retriever

本模块实现 FTS5 + FAISS 的混合检索策略，让 AI 更智能地找到相关记忆。
This module implements FTS5 + FAISS hybrid retrieval for smarter memory search.

Reference:
    - MOD-Memory.md §3.3: HybridRetriever
    - PRD §0.4: 混合存储系统

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set

from ..exceptions import RetrievalError
from ..models import MemoryItem, RankedMemory, RetrievalResult, TimeWindow
from .embedder import EmbedderConfig, TextEmbedder
from .fts_searcher import FTSConfig, FTSSearcher
from .vector_searcher import VectorSearcher, VectorSearcherConfig

logger = logging.getLogger(__name__)


class RetrievalStrategy(Enum):
    """
    检索策略枚举
    Retrieval strategy enumeration
    """

    FTS_ONLY = "fts_only"  # 仅全文检索 / FTS only
    VECTOR_ONLY = "vector_only"  # 仅向量检索 / Vector only
    HYBRID = "hybrid"  # 混合检索 / Hybrid (default)
    ADAPTIVE = "adaptive"  # 自适应策略 / Adaptive strategy


@dataclass
class HybridRetrieverConfig:
    """
    混合检索器配置
    Hybrid retriever configuration

    Attributes:
        fts_config: FTS5 配置 / FTS5 configuration
        vector_config: 向量检索配置 / Vector search configuration
        embedder_config: Embedding 配置 / Embedding configuration
        strategy: 检索策略 / Retrieval strategy
        fts_weight: FTS 权重 (0-1) / FTS weight
        vector_weight: 向量权重 (0-1) / Vector weight
        recency_weight: 时间新近度权重 / Recency weight
        importance_weight: 重要度权重 / Importance weight
        top_k: 最终返回数量 / Final return count
        fts_candidates: FTS 候选数量 / FTS candidate count
        vector_candidates: 向量候选数量 / Vector candidate count
        min_score: 最小分数阈值 / Minimum score threshold
        recency_decay_days: 新近度衰减天数 / Recency decay days
    """

    fts_config: FTSConfig = None  # type: ignore[assignment]
    vector_config: VectorSearcherConfig = None  # type: ignore[assignment]
    embedder_config: EmbedderConfig = None  # type: ignore[assignment]
    strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    fts_weight: float = 0.3
    vector_weight: float = 0.5
    recency_weight: float = 0.1
    importance_weight: float = 0.1
    top_k: int = 10
    fts_candidates: int = 30
    vector_candidates: int = 30
    min_score: float = 0.1
    recency_decay_days: int = 30

    def __post_init__(self) -> None:
        """初始化默认配置 / Initialize default configs"""
        if self.fts_config is None:
            self.fts_config = FTSConfig()
        if self.vector_config is None:
            self.vector_config = VectorSearcherConfig()
        if self.embedder_config is None:
            self.embedder_config = EmbedderConfig()


class HybridRetriever:
    """
    混合检索器
    Hybrid retriever

    结合 FTS5 全文检索和 FAISS 向量检索，
    通过加权融合得到更准确的检索结果。
    Combines FTS5 full-text search with FAISS vector search
    through weighted fusion for more accurate results.

    Attributes:
        config: 配置 / Configuration
        fts_searcher: FTS5 检索器 / FTS5 searcher
        vector_searcher: 向量检索器 / Vector searcher
        embedder: 文本嵌入器 / Text embedder

    Example:
        >>> retriever = HybridRetriever()
        >>> await retriever.initialize()
        >>> result = await retriever.retrieve("主人喜欢什么水果")
        >>> if result.has_results:
        ...     for ranked in result.memories:
        ...         print(f"{ranked.memory.content}: {ranked.final_score:.2f}")
    """

    def __init__(self, config: Optional[HybridRetrieverConfig] = None) -> None:
        """
        初始化混合检索器
        Initialize hybrid retriever

        Args:
            config: 配置，None 则使用默认配置 / Config, None for default
        """
        self.config = config or HybridRetrieverConfig()
        self.fts_searcher = FTSSearcher(self.config.fts_config)
        self.vector_searcher = VectorSearcher(self.config.vector_config)
        self.embedder = TextEmbedder(self.config.embedder_config)
        self._initialized = False

    async def initialize(self) -> None:
        """
        异步初始化所有组件
        Async initialize all components

        初始化 FTS5、FAISS 和 Embedding 模型。
        Initializes FTS5, FAISS and embedding model.
        """
        logger.info("Initializing HybridRetriever...")

        # FTS5 初始化（异步）
        await self.fts_searcher.initialize()

        # FAISS 和 Embedder 初始化（同步，在线程池中执行）
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.vector_searcher.initialize)
        await loop.run_in_executor(None, self.embedder.initialize)

        self._initialized = True
        logger.info("HybridRetriever initialized successfully")

    async def close(self) -> None:
        """
        关闭所有组件
        Close all components
        """
        await self.fts_searcher.close()
        self.vector_searcher.close()
        self.embedder.close()
        self._initialized = False
        logger.info("HybridRetriever closed")

    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        time_window: Optional[TimeWindow] = None,
        memory_types: Optional[List[str]] = None,
        strategy: Optional[RetrievalStrategy] = None,
    ) -> RetrievalResult:
        """
        执行混合检索
        Execute hybrid retrieval

        Args:
            query: 查询文本 / Query text
            top_k: 返回数量 / Return count
            time_window: 时间窗口 / Time window
            memory_types: 记忆类型过滤 / Memory type filter
            strategy: 检索策略，None 使用配置值 / Strategy, None for config

        Returns:
            RetrievalResult 包含排序后的记忆 / Result with ranked memories

        Raises:
            RuntimeError: 当未初始化时 / When not initialized
            RetrievalError: 检索失败时 / When retrieval fails
        """
        if not self._initialized:
            raise RuntimeError(
                "HybridRetriever not initialized. Call initialize() first."
            )

        start_time = time.perf_counter()
        k = top_k or self.config.top_k
        strat = strategy or self.config.strategy

        try:
            if strat == RetrievalStrategy.FTS_ONLY:
                result = await self._retrieve_fts_only(
                    query, k, time_window, memory_types
                )
            elif strat == RetrievalStrategy.VECTOR_ONLY:
                result = await self._retrieve_vector_only(
                    query, k, time_window, memory_types
                )
            elif strat == RetrievalStrategy.ADAPTIVE:
                result = await self._retrieve_adaptive(
                    query, k, time_window, memory_types
                )
            else:  # HYBRID
                result = await self._retrieve_hybrid(
                    query, k, time_window, memory_types
                )

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            result.retrieval_time_ms = elapsed_ms
            result.query = query

            logger.debug(
                f"Retrieved {len(result.memories)} memories in {elapsed_ms:.1f}ms "
                f"using {result.strategy_used}"
            )

            return result

        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            raise RetrievalError(str(e), strat.value) from e

    async def _retrieve_fts_only(
        self,
        query: str,
        top_k: int,
        time_window: Optional[TimeWindow],
        memory_types: Optional[List[str]],
    ) -> RetrievalResult:
        """
        仅 FTS5 检索
        FTS5 only retrieval
        """
        fts_results = await self.fts_searcher.search(
            query,
            top_k=top_k,
            time_window=time_window,
            memory_types=memory_types,
        )

        memories = await self._fetch_and_rank_memories(
            fts_results, {}, query, time_window
        )

        return RetrievalResult(
            memories=memories[:top_k],
            strategy_used="fts_only",
            total_candidates=len(fts_results),
            no_relevant_memory=len(memories) == 0,
        )

    async def _retrieve_vector_only(
        self,
        query: str,
        top_k: int,
        time_window: Optional[TimeWindow],
        memory_types: Optional[List[str]],
    ) -> RetrievalResult:
        """
        仅向量检索
        Vector only retrieval
        """
        # 获取查询向量 / Get query vector
        loop = asyncio.get_event_loop()
        query_vector = await loop.run_in_executor(
            None, self.embedder.embed_single, query
        )

        # 向量搜索 / Vector search
        vector_results = self.vector_searcher.search(
            query_vector,
            top_k=self.config.vector_candidates,
        )

        # 转换为 (id, score) 格式 / Convert to (id, score) format
        vector_scores = {mid: score for mid, score in vector_results}

        memories = await self._fetch_and_rank_memories(
            [], vector_scores, query, time_window, memory_types
        )

        return RetrievalResult(
            memories=memories[:top_k],
            strategy_used="vector_only",
            total_candidates=len(vector_results),
            no_relevant_memory=len(memories) == 0,
        )

    async def _retrieve_hybrid(
        self,
        query: str,
        top_k: int,
        time_window: Optional[TimeWindow],
        memory_types: Optional[List[str]],
    ) -> RetrievalResult:
        """
        混合检索（FTS5 + FAISS 融合）
        Hybrid retrieval (FTS5 + FAISS fusion)
        """
        # 并行执行 FTS5 和向量检索 / Parallel FTS5 and vector search
        loop = asyncio.get_event_loop()

        # 获取查询向量 / Get query vector
        query_vector_task = loop.run_in_executor(
            None, self.embedder.embed_single, query
        )

        # FTS5 检索 / FTS5 search
        fts_task = self.fts_searcher.search(
            query,
            top_k=self.config.fts_candidates,
            time_window=time_window,
            memory_types=memory_types,
        )

        # 等待两个任务完成 / Wait for both tasks
        query_vector, fts_results = await asyncio.gather(query_vector_task, fts_task)

        # 向量检索 / Vector search
        vector_results = self.vector_searcher.search(
            query_vector,
            top_k=self.config.vector_candidates,
        )

        # 转换为字典 / Convert to dict
        fts_scores = {mid: score for mid, score in fts_results}
        vector_scores = {mid: score for mid, score in vector_results}

        # 融合排序 / Fusion ranking
        memories = await self._fetch_and_rank_memories(
            fts_results, vector_scores, query, time_window, memory_types
        )

        total_candidates = len(set(fts_scores.keys()) | set(vector_scores.keys()))

        return RetrievalResult(
            memories=memories[:top_k],
            strategy_used="hybrid",
            total_candidates=total_candidates,
            no_relevant_memory=len(memories) == 0,
        )

    async def _retrieve_adaptive(
        self,
        query: str,
        top_k: int,
        time_window: Optional[TimeWindow],
        memory_types: Optional[List[str]],
    ) -> RetrievalResult:
        """
        自适应检索
        Adaptive retrieval

        根据查询特征自动选择最佳策略：
        - 短查询（<= 5 字）：优先 FTS5
        - 长查询（> 20 字）：优先向量
        - 其他：混合
        """
        query_len = len(query)

        if query_len <= 5:
            # 短查询，关键词匹配更重要 / Short query, keyword match matters
            return await self._retrieve_fts_only(
                query, top_k, time_window, memory_types
            )
        elif query_len > 20:
            # 长查询，语义匹配更重要 / Long query, semantic match matters
            return await self._retrieve_hybrid(
                query, top_k, time_window, memory_types
            )
        else:
            # 混合策略 / Hybrid strategy
            return await self._retrieve_hybrid(
                query, top_k, time_window, memory_types
            )

    async def _fetch_and_rank_memories(
        self,
        fts_results: List[tuple[str, float]],
        vector_scores: Dict[str, float],
        query: str,  # noqa: ARG002 - 保留用于未来扩展
        time_window: Optional[TimeWindow],
        memory_types: Optional[List[str]] = None,
    ) -> List[RankedMemory]:
        """
        获取记忆并进行综合排序
        Fetch memories and perform comprehensive ranking

        Args:
            fts_results: FTS 结果 (memory_id, score)
            vector_scores: 向量分数 {memory_id: score}
            query: 原始查询 / Original query
            time_window: 时间窗口 / Time window
            memory_types: 记忆类型过滤 / Memory type filter

        Returns:
            排序后的记忆列表 / Ranked memory list
        """
        # 收集所有候选 ID / Collect all candidate IDs
        candidate_ids: Set[str] = set()
        fts_scores: Dict[str, float] = {}

        for memory_id, score in fts_results:
            candidate_ids.add(memory_id)
            fts_scores[memory_id] = score

        candidate_ids.update(vector_scores.keys())

        if not candidate_ids:
            return []

        # 获取记忆详情 / Fetch memory details
        memories_dict: Dict[str, MemoryItem] = {}
        for memory_id in candidate_ids:
            data = await self.fts_searcher.get_memory_by_id(memory_id)
            if data:
                # 类型过滤 / Type filter
                if memory_types and data.get("memory_type") not in memory_types:
                    continue

                memory = MemoryItem.from_dict(data)
                memories_dict[memory_id] = memory

        # 计算综合分数 / Calculate composite score
        ranked_memories: List[RankedMemory] = []
        now = time.time()

        for memory_id, memory in memories_dict.items():
            # 归一化各项分数 / Normalize scores
            fts_score = self._normalize_score(fts_scores.get(memory_id, 0), "fts")
            vec_score = self._normalize_score(vector_scores.get(memory_id, 0), "vector")

            # 时间新近度分数 / Recency score
            age_seconds = now - memory.created_at.timestamp()
            age_days = age_seconds / 86400
            recency_score = max(0, 1 - age_days / self.config.recency_decay_days)

            # 重要度分数 / Importance score
            importance_score = memory.effective_importance

            # 加权融合 / Weighted fusion
            final_score = (
                self.config.fts_weight * fts_score
                + self.config.vector_weight * vec_score
                + self.config.recency_weight * recency_score
                + self.config.importance_weight * importance_score
            )

            # 确定检索来源 / Determine retrieval source
            source = "both" if memory_id in fts_scores and memory_id in vector_scores \
                else "fts" if memory_id in fts_scores else "vector"

            ranked_memories.append(
                RankedMemory(
                    memory=memory,
                    final_score=final_score,
                    similarity_score=vec_score,
                    recency_score=recency_score,
                    retrieval_source=source,
                )
            )

        # 按最终分数排序 / Sort by final score
        ranked_memories.sort(key=lambda x: x.final_score, reverse=True)

        # 过滤低分 / Filter low scores
        ranked_memories = [
            rm for rm in ranked_memories if rm.final_score >= self.config.min_score
        ]

        return ranked_memories

    def _normalize_score(self, score: float, source: str) -> float:
        """
        归一化分数到 0-1 范围
        Normalize score to 0-1 range

        Args:
            score: 原始分数 / Raw score
            source: 分数来源 (fts/vector) / Score source

        Returns:
            归一化分数 / Normalized score
        """
        if source == "fts":
            # BM25 分数通常在 0-30 范围 / BM25 scores typically 0-30
            return min(1.0, score / 15.0)
        elif source == "vector":
            # 余弦相似度已在 -1 到 1 范围 / Cosine similarity already -1 to 1
            # 归一化向量后内积等于余弦相似度
            return max(0, (score + 1) / 2)
        return score

    async def add_memory(self, memory: MemoryItem) -> None:
        """
        添加记忆到检索系统
        Add memory to retrieval system

        同时添加到 FTS5 和 FAISS 索引。
        Adds to both FTS5 and FAISS indices.

        Args:
            memory: 记忆项 / Memory item
        """
        if not self._initialized:
            raise RuntimeError(
                "HybridRetriever not initialized. Call initialize() first."
            )

        # 添加到 FTS5 / Add to FTS5
        await self.fts_searcher.insert_memory(memory)

        # 向量化并添加到 FAISS / Vectorize and add to FAISS
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, self.embedder.embed_single, memory.content
        )

        self.vector_searcher.add_vectors(
            [memory.id],
            embedding.reshape(1, -1),
        )

        # 更新向量化标记 / Update vectorized flag
        await self.fts_searcher.update_memory(memory.id, {"is_vectorized": 1})

        logger.debug(f"Added memory to retrieval system: {memory.id[:8]}...")

    async def remove_memory(self, memory_id: str) -> bool:
        """
        从检索系统删除记忆
        Remove memory from retrieval system

        Args:
            memory_id: 记忆 ID / Memory ID

        Returns:
            是否删除成功 / Whether removal succeeded
        """
        if not self._initialized:
            raise RuntimeError(
                "HybridRetriever not initialized. Call initialize() first."
            )

        # 从 FTS5 删除 / Remove from FTS5
        fts_removed = await self.fts_searcher.delete_memory(memory_id)

        # 从 FAISS 删除 / Remove from FAISS
        vector_removed = self.vector_searcher.remove_vectors([memory_id])

        return fts_removed or vector_removed > 0

    async def save(self) -> None:
        """
        保存所有索引
        Save all indices
        """
        if not self._initialized:
            return

        # FAISS 索引保存 / Save FAISS index
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.vector_searcher.save)

        logger.info("HybridRetriever indices saved")

    @property
    def is_initialized(self) -> bool:
        """
        检查是否已初始化
        Check if initialized

        Returns:
            是否已初始化 / Whether initialized
        """
        return self._initialized

    async def get_stats(self) -> Dict[str, int]:
        """
        获取检索系统统计
        Get retrieval system statistics

        Returns:
            统计信息字典 / Statistics dict
        """
        fts_count = await self.fts_searcher.get_memory_count()
        vector_count = self.vector_searcher.get_vector_count()

        return {
            "fts_memory_count": fts_count,
            "vector_count": vector_count,
            "embedding_dimension": self.embedder.dimension if self._initialized else 0,
        }
