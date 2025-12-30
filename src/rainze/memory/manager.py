"""
记忆管理器
Memory Manager

本模块实现记忆系统的主入口类 MemoryManager。
This module implements the main entry class MemoryManager.

Reference:
    - MOD-Memory.md §3.1: MemoryManager 设计 / Design
    - PRD §0.2, §0.4: 记忆系统需求 / Requirements

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .exceptions import MemoryNotFoundError  # noqa: F401 - exported for type hints
from .layers import ConversationTurn, WorkingMemory
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
from .retrieval import FTSConfig, FTSSearcher

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    记忆管理器
    Memory Manager

    统一管理 3 层记忆的读写，协调记忆检索与存储。
    Manages all 3 memory layers, coordinates retrieval and storage.

    这是记忆系统的主入口，所有记忆操作都应通过此类进行。
    This is the main entry point for the memory system.

    Attributes:
        working_memory: 工作记忆 (Layer 2) / Working memory
        fts_searcher: FTS5 检索器 / FTS5 searcher

    Example:
        >>> manager = MemoryManager()
        >>> await manager.initialize()
        >>> episode = await manager.create_episode(
        ...     summary="主人说工作压力很大",
        ...     emotion_tag="tired"
        ... )
        >>> results = await manager.search("工作压力")
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        max_conversation_turns: int = 20,
    ) -> None:
        """
        初始化记忆管理器
        Initialize memory manager

        Args:
            db_path: 数据库路径 / Database path
            max_conversation_turns: 最大对话轮次 / Max conversation turns
        """
        self._db_path = db_path or Path("./data/memory.db")

        # Layer 2: 工作记忆 / Working memory
        self.working_memory = WorkingMemory(max_turns=max_conversation_turns)

        # FTS5 检索器 / FTS5 searcher
        self.fts_searcher = FTSSearcher(
            FTSConfig(db_path=self._db_path),
        )

        self._initialized = False

    async def initialize(self) -> None:
        """
        异步初始化
        Async initialization

        初始化数据库连接和 FTS5 索引。
        Initializes database connection and FTS5 index.
        """
        await self.fts_searcher.initialize()
        self._initialized = True
        logger.info("MemoryManager initialized successfully")

    async def close(self) -> None:
        """
        关闭资源
        Close resources
        """
        await self.fts_searcher.close()
        self._initialized = False

    # ==================== 记忆写入 / Memory Write ====================

    async def create_memory(
        self,
        content: str,
        memory_type: MemoryType,
        importance: Optional[float] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryItem:
        """
        创建新记忆
        Create new memory

        Args:
            content: 记忆内容 / Memory content
            memory_type: 记忆类型 / Memory type
            importance: 重要度 (0-1)，None 则使用默认值 / Importance
            tags: 标签列表 / Tag list
            metadata: 元数据 / Metadata

        Returns:
            创建的记忆项 / Created memory item

        Note:
            - 立即写入 SQLite（FTS5 可检索）
            - 向量化功能暂未实现 / Vectorization not yet implemented
        """
        self._ensure_initialized()

        # 使用默认重要度或自动评估（简化版）
        # Use default importance or auto-evaluate (simplified)
        if importance is None:
            importance = self._evaluate_importance(content)

        memory = MemoryItem(
            content=content,
            memory_type=memory_type,
            importance=importance,
            tags=tags or [],
            metadata=metadata or {},
        )

        # 持久化到数据库 / Persist to database
        await self.fts_searcher.insert_memory(memory)

        logger.debug(f"Created memory: {memory.id[:8]}... type={memory_type.value}")
        return memory

    async def create_fact(
        self,
        subject: str,
        predicate: str,
        obj: str,
        confidence: float = 1.0,
        source_memory_ids: Optional[List[str]] = None,
    ) -> FactItem:
        """
        创建事实记忆
        Create fact memory

        Args:
            subject: 主语 / Subject (e.g., "主人")
            predicate: 谓语 / Predicate (e.g., "喜欢")
            obj: 宾语 / Object (e.g., "苹果")
            confidence: 置信度 / Confidence (0-1)
            source_memory_ids: 来源记忆 ID / Source memory IDs

        Returns:
            事实记忆项 / Fact memory item

        Example:
            >>> fact = await manager.create_fact("主人", "喜欢", "苹果")
        """
        self._ensure_initialized()

        fact = FactItem(
            subject=subject,
            predicate=predicate,
            obj=obj,
            confidence=confidence,
            source_memory_ids=source_memory_ids or [],
        )

        # 创建对应的 MemoryItem 用于检索
        # Create corresponding MemoryItem for retrieval
        content = fact.to_content()
        memory = MemoryItem(
            id=fact.id,
            content=content,
            memory_type=MemoryType.FACT,
            importance=0.7,  # 事实记忆默认较高重要度 / Facts have higher importance
            metadata={
                "subject": subject,
                "predicate": predicate,
                "obj": obj,
                "confidence": confidence,
                "source_memory_ids": source_memory_ids or [],
            },
        )

        await self.fts_searcher.insert_memory(memory)

        logger.debug(f"Created fact: {fact.id[:8]}... ({subject} {predicate} {obj})")
        return fact

    async def create_episode(
        self,
        summary: str,
        emotion_tag: Optional[str] = None,
        affinity_change: int = 0,
        participants: Optional[List[str]] = None,
    ) -> EpisodeItem:
        """
        创建情景记忆
        Create episode memory

        Args:
            summary: 情景摘要 / Episode summary
            emotion_tag: 情感标签 / Emotion tag
            affinity_change: 好感度变化 / Affinity change
            participants: 参与者列表 / Participants list

        Returns:
            情景记忆项 / Episode memory item
        """
        self._ensure_initialized()

        episode = EpisodeItem(
            summary=summary,
            emotion_tag=emotion_tag,
            affinity_change=affinity_change,
            participants=participants or [],
        )

        # 根据好感度变化计算重要度
        # Calculate importance based on affinity change
        importance = 0.5
        if abs(affinity_change) >= 5:
            importance = 0.8
        elif abs(affinity_change) >= 3:
            importance = 0.7

        memory = MemoryItem(
            id=episode.id,
            content=summary,
            memory_type=MemoryType.EPISODE,
            importance=importance,
            metadata={
                "emotion_tag": emotion_tag,
                "affinity_change": affinity_change,
                "participants": participants or [],
            },
        )

        await self.fts_searcher.insert_memory(memory)

        logger.debug(f"Created episode: {episode.id[:8]}... affinity={affinity_change}")
        return episode

    # ==================== 记忆检索 / Memory Retrieval ====================

    async def search(
        self,
        query: str,
        top_k: int = 5,
        memory_types: Optional[List[MemoryType]] = None,
        time_window: Optional[TimeWindow] = None,
        min_importance: float = 0.0,
        similarity_threshold: float = 0.65,
    ) -> RetrievalResult:
        """
        混合检索记忆
        Hybrid memory retrieval

        当前实现仅使用 FTS5，向量检索后续实现。
        Current implementation uses FTS5 only, vector search to be added.

        Args:
            query: 检索查询 / Search query
            top_k: 返回数量 / Return count
            memory_types: 记忆类型过滤 / Memory type filter
            time_window: 时间窗口 / Time window
            min_importance: 最小重要度 / Minimum importance
            similarity_threshold: 相关性阈值 / Relevance threshold

        Returns:
            检索结果 / Retrieval result

        Note:
            - 自动检测时间关键词并推断时间窗口
            - 应用阈值门控 (score < threshold 视为无相关记忆)
        """
        self._ensure_initialized()

        start_time = time.time()

        # 自动检测时间关键词 / Auto-detect time keywords
        if time_window is None:
            time_window = TimeWindow.from_keyword(query)

        # 转换记忆类型为字符串列表 / Convert memory types to string list
        type_filters = None
        if memory_types:
            type_filters = [mt.value for mt in memory_types]

        # 执行 FTS5 检索 / Execute FTS5 search
        fts_results = await self.fts_searcher.search(
            query=query,
            top_k=top_k * 2,  # 多取一些用于过滤 / Get more for filtering
            time_window=time_window,
            memory_types=type_filters,
            min_importance=min_importance,
        )

        # 转换为 RankedMemory 列表 / Convert to RankedMemory list
        ranked_memories: List[RankedMemory] = []

        for memory_id, score in fts_results:
            memory_data = await self.fts_searcher.get_memory_by_id(memory_id)
            if memory_data is None:
                continue

            # 解析记忆项 / Parse memory item
            memory = self._parse_memory_from_db(memory_data)
            memory.mark_accessed()

            # 计算时间新近度分数 / Calculate recency score
            recency_score = self._calculate_recency_score(memory.created_at)

            # 计算综合评分 / Calculate composite score
            # 综合评分 = similarity*0.4 + recency*0.3 + importance*0.2 + frequency*0.1
            frequency_score = min(memory.access_count / 10.0, 1.0)
            final_score = (
                score * 0.4
                + recency_score * 0.3
                + memory.effective_importance * 0.2
                + frequency_score * 0.1
            )

            ranked_memories.append(
                RankedMemory(
                    memory=memory,
                    final_score=final_score,
                    similarity_score=score,
                    recency_score=recency_score,
                    retrieval_source="fts5",
                )
            )

        # 按综合评分排序 / Sort by final score
        ranked_memories.sort(key=lambda x: x.final_score, reverse=True)

        # 应用阈值门控 / Apply threshold gating
        filtered_memories = [
            rm for rm in ranked_memories if rm.final_score >= similarity_threshold
        ]

        # 限制返回数量 / Limit return count
        filtered_memories = filtered_memories[:top_k]

        elapsed_ms = (time.time() - start_time) * 1000

        return RetrievalResult(
            memories=filtered_memories,
            no_relevant_memory=len(filtered_memories) == 0,
            strategy_used="fts5",
            total_candidates=len(fts_results),
            retrieval_time_ms=elapsed_ms,
            query=query,
        )

    async def search_facts(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        obj: Optional[str] = None,
    ) -> List[FactItem]:
        """
        检索事实记忆
        Search fact memories

        Args:
            subject: 主语筛选 / Subject filter
            predicate: 谓语筛选 / Predicate filter
            obj: 宾语筛选 / Object filter

        Returns:
            匹配的事实列表 / Matching facts list
        """
        self._ensure_initialized()

        # 构建查询字符串 / Build query string
        query_parts = []
        if subject:
            query_parts.append(subject)
        if predicate:
            query_parts.append(predicate)
        if obj:
            query_parts.append(obj)

        if not query_parts:
            return []

        query = " ".join(query_parts)

        # 使用 FTS5 检索 / Use FTS5 search
        result = await self.search(
            query=query,
            top_k=20,
            memory_types=[MemoryType.FACT],
        )

        # 转换为 FactItem 列表 / Convert to FactItem list
        facts: List[FactItem] = []
        for ranked in result.memories:
            metadata = ranked.memory.metadata
            fact = FactItem(
                id=ranked.memory.id,
                subject=metadata.get("subject", ""),
                predicate=metadata.get("predicate", ""),
                obj=metadata.get("obj", ""),
                confidence=metadata.get("confidence", 1.0),
                source_memory_ids=metadata.get("source_memory_ids", []),
                created_at=ranked.memory.created_at,
            )
            facts.append(fact)

        return facts

    # ==================== 记忆索引 / Memory Index ====================

    async def get_memory_index(
        self,
        query: str,
        count: int = 30,
    ) -> List[MemoryIndexItem]:
        """
        获取记忆索引列表（用于 Prompt 注入）
        Get memory index list (for Prompt injection)

        Args:
            query: 相关性查询 / Relevance query
            count: 索引数量 / Index count

        Returns:
            记忆索引列表 / Memory index list
        """
        self._ensure_initialized()

        result = await self.search(
            query=query,
            top_k=count,
            similarity_threshold=0.3,  # 索引用较低阈值 / Lower threshold for index
        )

        index_items: List[MemoryIndexItem] = []
        for ranked in result.memories:
            index_item = MemoryIndexItem.from_memory(ranked.memory)
            index_items.append(index_item)

        return index_items

    async def expand_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """
        展开记忆全文（响应 [RECALL:#mem_xxx] 指令）
        Expand memory full text (respond to [RECALL:#mem_xxx])

        Args:
            memory_id: 记忆 ID / Memory ID

        Returns:
            完整记忆内容，不存在返回 None / Full memory or None
        """
        self._ensure_initialized()

        # 支持短 ID 或完整 ID / Support short ID or full ID
        memory_data = await self.fts_searcher.get_memory_by_id(memory_id)

        if memory_data is None:
            return None

        memory = self._parse_memory_from_db(memory_data)
        memory.mark_accessed()

        # 更新访问记录 / Update access record
        await self.fts_searcher.update_memory(
            memory_id,
            {
                "access_count": memory.access_count,
                "last_accessed": memory.last_accessed.isoformat()
                if memory.last_accessed
                else None,
            },
        )

        return memory

    # ==================== 工作记忆 / Working Memory ====================

    def get_conversation_history(
        self,
        max_turns: Optional[int] = None,
    ) -> List[ConversationTurn]:
        """
        获取对话历史
        Get conversation history

        Args:
            max_turns: 最大轮数，None 则使用配置值 / Max turns

        Returns:
            对话历史列表 / Conversation history list
        """
        return self.working_memory.get_history(max_turns)

    def add_conversation_turn(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        添加对话轮次
        Add conversation turn

        Args:
            role: 角色 / Role ("user" | "assistant")
            content: 内容 / Content
            metadata: 元数据 / Metadata
        """
        # 验证角色 / Validate role
        valid_roles = ("user", "assistant", "system")
        if role not in valid_roles:
            raise ValueError(f"Invalid role: {role}. Must be one of {valid_roles}")

        self.working_memory.add_turn(
            role=role,  # type: ignore[arg-type]
            content=content,
            metadata=metadata,
        )

    def clear_conversation(self) -> None:
        """
        清空当前会话对话历史
        Clear current session conversation history
        """
        self.working_memory.clear()

    # ==================== 统计与调试 / Stats & Debug ====================

    async def get_stats(self) -> Dict[str, Any]:
        """
        获取记忆统计信息
        Get memory statistics

        Returns:
            统计信息字典 / Statistics dict
        """
        self._ensure_initialized()

        memory_count = await self.fts_searcher.get_memory_count()

        return {
            "total_memories": memory_count,
            "conversation_turns": self.working_memory.turn_count,
            "is_initialized": self._initialized,
        }

    # ==================== 内部方法 / Internal Methods ====================

    def _ensure_initialized(self) -> None:
        """
        确保已初始化
        Ensure initialized

        Raises:
            RuntimeError: 当未初始化时 / When not initialized
        """
        if not self._initialized:
            raise RuntimeError(
                "MemoryManager not initialized. Call await initialize() first."
            )

    def _evaluate_importance(self, content: str) -> float:
        """
        简单的重要度评估（规则版）
        Simple importance evaluation (rule-based)

        Args:
            content: 记忆内容 / Memory content

        Returns:
            重要度分数 / Importance score

        Rules:
            - 包含关键词 (生日/重要/记住/喜欢/讨厌) → 0.7
            - 普通内容 → 0.5
        """
        # 高重要度关键词 / High importance keywords
        high_importance_keywords = [
            "生日",
            "重要",
            "记住",
            "喜欢",
            "讨厌",
            "爱",
            "恨",
            "约定",
            "承诺",
        ]

        for keyword in high_importance_keywords:
            if keyword in content:
                return 0.7

        return 0.5

    def _calculate_recency_score(self, created_at: datetime) -> float:
        """
        计算时间新近度分数
        Calculate recency score

        Args:
            created_at: 创建时间 / Creation time

        Returns:
            新近度分数 (0-1) / Recency score
        """
        now = datetime.now()
        delta = now - created_at

        # 半衰期为 7 天 / Half-life is 7 days
        half_life_days = 7.0
        days_old = delta.total_seconds() / 86400.0

        # 指数衰减 / Exponential decay
        import math

        score = math.exp(-0.693 * days_old / half_life_days)

        return min(1.0, max(0.0, score))

    def _parse_memory_from_db(self, data: Dict[str, Any]) -> MemoryItem:
        """
        从数据库记录解析 MemoryItem
        Parse MemoryItem from database record

        Args:
            data: 数据库记录 / Database record

        Returns:
            记忆项 / Memory item
        """
        # 解析时间字段 / Parse datetime fields
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        elif updated_at is None:
            updated_at = datetime.now()

        last_accessed = data.get("last_accessed")
        if isinstance(last_accessed, str):
            last_accessed = datetime.fromisoformat(last_accessed)

        # 解析 JSON 字段 / Parse JSON fields
        tags = data.get("tags", "[]")
        if isinstance(tags, str):
            tags = json.loads(tags)

        metadata = data.get("metadata", "{}")
        if isinstance(metadata, str):
            metadata = json.loads(metadata)

        return MemoryItem(
            id=data["id"],
            content=data["content"],
            memory_type=MemoryType(data["memory_type"]),
            importance=data.get("importance", 0.5),
            created_at=created_at,
            updated_at=updated_at,
            access_count=data.get("access_count", 0),
            last_accessed=last_accessed,
            decay_factor=data.get("decay_factor", 1.0),
            tags=tags,
            metadata=metadata,
            is_vectorized=bool(data.get("is_vectorized", 0)),
            is_archived=bool(data.get("is_archived", 0)),
            conflict_flag=bool(data.get("conflict_flag", 0)),
        )
