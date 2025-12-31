"""
检索结果数据模型
Retrieval Result Data Models

本模块定义记忆检索相关的数据模型。
This module defines data models for memory retrieval.

Reference:
    - MOD-Memory.md §4.2: RetrievalResult 数据模型 / Data Model

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from .memory_item import MemoryItem


@dataclass
class RankedMemory:
    """
    排序后的记忆
    Ranked memory item

    包含检索评分信息的记忆项。
    Memory item with retrieval scoring information.

    Attributes:
        memory: 记忆项 / Memory item
        final_score: 综合评分 / Final composite score
        similarity_score: 相似度分数 / Similarity score
        recency_score: 时间新近度分数 / Recency score
        retrieval_source: 检索来源 / Retrieval source (fts5/vector/both)
    """

    memory: "MemoryItem"
    final_score: float
    similarity_score: float = 0.0
    recency_score: float = 0.0
    retrieval_source: str = "unknown"


@dataclass
class RetrievalResult:
    """
    检索结果
    Retrieval result

    包含检索到的记忆列表及元数据。
    Contains retrieved memories list and metadata.

    Attributes:
        memories: 检索到的记忆列表 / Retrieved memories list
        no_relevant_memory: 是否无相关记忆 / Whether no relevant memory found
        strategy_used: 使用的检索策略 / Retrieval strategy used
        total_candidates: 候选总数 / Total candidates count
        retrieval_time_ms: 检索耗时（毫秒）/ Retrieval time in ms
        query: 原始查询 / Original query

    Example:
        >>> result = RetrievalResult(memories=[ranked_memory])
        >>> if result.has_results:
        ...     print(result.memories[0].memory.content)
    """

    memories: List[RankedMemory] = field(default_factory=list)
    no_relevant_memory: bool = False
    strategy_used: str = "unknown"
    total_candidates: int = 0
    retrieval_time_ms: float = 0.0
    query: str = ""

    @property
    def has_results(self) -> bool:
        """
        是否有检索结果
        Whether has retrieval results

        Returns:
            是否有有效结果 / Whether has valid results
        """
        return len(self.memories) > 0 and not self.no_relevant_memory

    @property
    def top_memory(self) -> Optional[RankedMemory]:
        """
        获取最佳匹配记忆
        Get top matching memory

        Returns:
            最高分的记忆，无结果返回 None / Top scored memory or None
        """
        if self.has_results:
            return self.memories[0]
        return None


@dataclass
class MemoryIndexItem:
    """
    记忆索引项（用于 Prompt 注入）
    Memory index item (for Prompt injection)

    轻量级的记忆索引，包含ID、时间描述和摘要。
    Lightweight memory index with ID, time description and summary.

    Attributes:
        id: 记忆ID / Memory ID (e.g., "mem_001")
        time_ago: 时间描述 / Time description (e.g., "3天前")
        summary: 20字摘要 / 20-char summary
        importance: 重要度 / Importance score
        is_high_priority: 是否高优先级 / Whether high priority

    Example:
        >>> item = MemoryIndexItem(
        ...     id="mem_001",
        ...     time_ago="3天前",
        ...     summary="主人喜欢苹果",
        ...     importance=0.8,
        ...     is_high_priority=True
        ... )
        >>> print(item.format_for_prompt())
        #mem_001 [3天前] 主人喜欢苹果 (重要度0.8) ⭐
    """

    id: str
    time_ago: str
    summary: str
    importance: float
    is_high_priority: bool = False

    def format_for_prompt(self) -> str:
        """
        格式化为 Prompt 字符串
        Format for Prompt string

        Returns:
            格式化的索引字符串 / Formatted index string
        """
        priority_mark = "⭐" if self.is_high_priority else ""
        return (
            f"#{self.id} [{self.time_ago}] {self.summary} "
            f"(重要度{self.importance:.1f}) {priority_mark}"
        ).strip()

    @classmethod
    def from_memory(
        cls,
        memory: "MemoryItem",
        summary_length: int = 20,
    ) -> "MemoryIndexItem":
        """
        从 MemoryItem 创建索引项
        Create index item from MemoryItem

        Args:
            memory: 记忆项 / Memory item
            summary_length: 摘要长度 / Summary length

        Returns:
            记忆索引项 / MemoryIndexItem instance
        """
        # 生成时间描述 / Generate time description
        time_ago = _format_time_ago(memory.created_at)

        # 生成摘要（截取前 N 个字符）
        # Generate summary (truncate to N chars)
        summary = memory.content[:summary_length]
        if len(memory.content) > summary_length:
            summary = summary[: summary_length - 1] + "…"

        return cls(
            id=memory.id[:8],  # 使用前8位作为短ID / Use first 8 chars as short ID
            time_ago=time_ago,
            summary=summary,
            importance=memory.effective_importance,
            is_high_priority=memory.importance >= 0.7,
        )


@dataclass
class TimeWindow:
    """
    时间窗口
    Time window

    用于检索时的时间范围过滤。
    Used for time range filtering during retrieval.

    Attributes:
        start: 开始时间 / Start time
        end: 结束时间 / End time
        source_keyword: 触发关键词 / Source keyword
    """

    start: Optional[datetime] = None
    end: Optional[datetime] = None
    source_keyword: Optional[str] = None

    @classmethod
    def from_keyword(cls, keyword: str) -> Optional["TimeWindow"]:
        """
        从关键词推断时间窗口
        Infer time window from keyword

        Args:
            keyword: 时间关键词 / Time keyword

        Returns:
            时间窗口，无法推断则返回 None / TimeWindow or None

        Mappings:
            - "刚才/刚刚" → 1小时内 / Last 1 hour
            - "今天" → 当天 / Today
            - "昨天" → 24-48小时 / 24-48 hours ago
            - "最近/这几天" → 3天内 / Last 3 days
            - "上次/之前" → 7天内 / Last 7 days
            - "以前/很久" → 30天内 / Last 30 days
        """
        now = datetime.now()

        # 关键词到时间范围的映射 / Keyword to time range mapping
        keyword_mappings: Dict[str, timedelta | tuple[timedelta, timedelta]] = {
            "刚才": timedelta(hours=1),
            "刚刚": timedelta(hours=1),
            "今天": timedelta(hours=24),
            "昨天": (timedelta(hours=48), timedelta(hours=24)),
            "最近": timedelta(days=3),
            "这几天": timedelta(days=3),
            "上次": timedelta(days=7),
            "之前": timedelta(days=7),
            "以前": timedelta(days=30),
            "很久": timedelta(days=30),
        }

        for kw, delta in keyword_mappings.items():
            if kw in keyword:
                if isinstance(delta, tuple):
                    # 昨天：24-48小时前 / Yesterday: 24-48 hours ago
                    start_delta, end_delta = delta
                    return cls(
                        start=now - start_delta,
                        end=now - end_delta,
                        source_keyword=kw,
                    )
                else:
                    return cls(
                        start=now - delta,
                        end=now,
                        source_keyword=kw,
                    )

        return None

    @classmethod
    def last_hours(cls, hours: int) -> "TimeWindow":
        """
        最近 N 小时
        Last N hours

        Args:
            hours: 小时数 / Number of hours

        Returns:
            时间窗口 / TimeWindow
        """
        now = datetime.now()
        return cls(start=now - timedelta(hours=hours), end=now)

    @classmethod
    def last_days(cls, days: int) -> "TimeWindow":
        """
        最近 N 天
        Last N days

        Args:
            days: 天数 / Number of days

        Returns:
            时间窗口 / TimeWindow
        """
        now = datetime.now()
        return cls(start=now - timedelta(days=days), end=now)


def _format_time_ago(dt: datetime) -> str:
    """
    格式化时间为"X前"形式
    Format datetime to "X ago" form

    Args:
        dt: 时间戳 / Datetime

    Returns:
        时间描述字符串 / Time description string
    """
    now = datetime.now()
    delta = now - dt

    if delta.total_seconds() < 60:
        return "刚刚"
    elif delta.total_seconds() < 3600:
        minutes = int(delta.total_seconds() / 60)
        return f"{minutes}分钟前"
    elif delta.total_seconds() < 86400:
        hours = int(delta.total_seconds() / 3600)
        return f"{hours}小时前"
    elif delta.days < 30:
        return f"{delta.days}天前"
    elif delta.days < 365:
        months = delta.days // 30
        return f"{months}个月前"
    else:
        years = delta.days // 365
        return f"{years}年前"
