"""
记忆项数据模型
Memory Item Data Models

本模块定义记忆系统的核心数据模型，包括 MemoryItem、FactItem、EpisodeItem 等。
This module defines core data models for the memory system.

Reference:
    - MOD-Memory.md §4.1: MemoryItem 数据模型 / Data Model

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MemoryType(Enum):
    """
    记忆类型枚举
    Memory type enumeration

    所有模块必须使用此枚举定义记忆类型。
    All modules MUST use this enum for memory types.
    """

    FACT = "fact"  # 事实记忆 / Fact memory
    EPISODE = "episode"  # 情景记忆 / Episode memory
    RELATION = "relation"  # 关系记忆 / Relation memory
    REFLECTION = "reflection"  # 反思记忆 / Reflection memory


@dataclass
class MemoryItem:
    """
    记忆项数据模型
    Memory item data model

    所有记忆的基础数据结构，包含内容、类型、重要度等信息。
    Base data structure for all memories with content, type, importance, etc.

    Attributes:
        content: 记忆内容 / Memory content
        memory_type: 记忆类型 / Memory type
        importance: 重要度 (0-1) / Importance score
        id: 唯一标识符 / Unique identifier
        created_at: 创建时间 / Creation timestamp
        updated_at: 更新时间 / Update timestamp
        access_count: 访问次数 / Access count
        last_accessed: 最后访问时间 / Last access timestamp
        decay_factor: 衰减因子 (0-1) / Decay factor
        tags: 标签列表 / Tag list
        metadata: 元数据字典 / Metadata dict
        is_vectorized: 是否已向量化 / Whether vectorized
        is_archived: 是否已归档 / Whether archived
        conflict_flag: 是否标记为矛盾 / Whether marked as conflict

    Example:
        >>> item = MemoryItem(content="主人喜欢苹果", memory_type=MemoryType.FACT)
        >>> print(item.effective_importance)
        0.5
    """

    content: str
    memory_type: MemoryType
    importance: float = 0.5
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    decay_factor: float = 1.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_vectorized: bool = False
    is_archived: bool = False
    conflict_flag: bool = False

    @property
    def effective_importance(self) -> float:
        """
        有效重要度 = 原始重要度 × 衰减因子
        Effective importance = original importance × decay factor

        Returns:
            有效重要度分数 / Effective importance score
        """
        return self.importance * self.decay_factor

    def mark_accessed(self) -> None:
        """
        标记记忆被访问
        Mark memory as accessed

        更新访问计数和最后访问时间。
        Updates access count and last access timestamp.
        """
        self.access_count += 1
        self.last_accessed = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        Convert to dictionary format

        Returns:
            记忆项的字典表示 / Dictionary representation
        """
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "importance": self.importance,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "access_count": self.access_count,
            "last_accessed": (
                self.last_accessed.isoformat() if self.last_accessed else None
            ),
            "decay_factor": self.decay_factor,
            "tags": self.tags,
            "metadata": self.metadata,
            "is_vectorized": self.is_vectorized,
            "is_archived": self.is_archived,
            "conflict_flag": self.conflict_flag,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        """
        从字典创建记忆项
        Create memory item from dictionary

        Args:
            data: 记忆项字典 / Memory item dictionary

        Returns:
            记忆项实例 / MemoryItem instance
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

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            content=data["content"],
            memory_type=MemoryType(data["memory_type"]),
            importance=data.get("importance", 0.5),
            created_at=created_at,
            updated_at=updated_at,
            access_count=data.get("access_count", 0),
            last_accessed=last_accessed,
            decay_factor=data.get("decay_factor", 1.0),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            is_vectorized=data.get("is_vectorized", False),
            is_archived=data.get("is_archived", False),
            conflict_flag=data.get("conflict_flag", False),
        )


@dataclass
class FactItem:
    """
    事实记忆项
    Fact memory item

    存储结构化的事实信息，如 "主人喜欢苹果"。
    Stores structured fact information like "Master likes apples".

    Attributes:
        subject: 主语 / Subject (e.g., "主人")
        predicate: 谓语 / Predicate (e.g., "喜欢")
        obj: 宾语 / Object (e.g., "苹果")
        confidence: 置信度 (0-1) / Confidence score
        source_memory_ids: 来源记忆ID列表 / Source memory IDs
        id: 唯一标识符 / Unique identifier
        created_at: 创建时间 / Creation timestamp
        updated_at: 更新时间 / Update timestamp

    Example:
        >>> fact = FactItem(subject="主人", predicate="喜欢", obj="苹果")
        >>> print(fact.to_triple())
        ('主人', '喜欢', '苹果')
    """

    subject: str
    predicate: str
    obj: str
    confidence: float = 1.0
    source_memory_ids: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_triple(self) -> tuple[str, str, str]:
        """
        转换为三元组格式
        Convert to triple format

        Returns:
            (主语, 谓语, 宾语) 元组 / (subject, predicate, object) tuple
        """
        return (self.subject, self.predicate, self.obj)

    def to_content(self) -> str:
        """
        转换为自然语言内容
        Convert to natural language content

        Returns:
            自然语言描述 / Natural language description
        """
        return f"{self.subject}{self.predicate}{self.obj}"

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        Convert to dictionary format

        Returns:
            事实项的字典表示 / Dictionary representation
        """
        return {
            "id": self.id,
            "subject": self.subject,
            "predicate": self.predicate,
            "obj": self.obj,
            "confidence": self.confidence,
            "source_memory_ids": self.source_memory_ids,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FactItem":
        """
        从字典创建事实项
        Create fact item from dictionary

        Args:
            data: 事实项字典 / Fact item dictionary

        Returns:
            事实项实例 / FactItem instance
        """
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

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            subject=data["subject"],
            predicate=data["predicate"],
            obj=data["obj"],
            confidence=data.get("confidence", 1.0),
            source_memory_ids=data.get("source_memory_ids", []),
            created_at=created_at,
            updated_at=updated_at,
        )


@dataclass
class EpisodeItem:
    """
    情景记忆项
    Episode memory item

    存储情景化的记忆，如对话事件、重要时刻等。
    Stores episodic memories like conversation events, important moments, etc.

    Attributes:
        summary: 情景摘要 / Episode summary
        emotion_tag: 情感标签 / Emotion tag
        affinity_change: 好感度变化 / Affinity change
        participants: 参与者列表 / Participants list
        id: 唯一标识符 / Unique identifier
        created_at: 创建时间 / Creation timestamp

    Example:
        >>> episode = EpisodeItem(
        ...     summary="主人说工作压力很大",
        ...     emotion_tag="tired",
        ...     affinity_change=5
        ... )
    """

    summary: str
    emotion_tag: Optional[str] = None
    affinity_change: int = 0
    participants: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        Convert to dictionary format

        Returns:
            情景项的字典表示 / Dictionary representation
        """
        return {
            "id": self.id,
            "summary": self.summary,
            "emotion_tag": self.emotion_tag,
            "affinity_change": self.affinity_change,
            "participants": self.participants,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EpisodeItem":
        """
        从字典创建情景项
        Create episode item from dictionary

        Args:
            data: 情景项字典 / Episode item dictionary

        Returns:
            情景项实例 / EpisodeItem instance
        """
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            summary=data["summary"],
            emotion_tag=data.get("emotion_tag"),
            affinity_change=data.get("affinity_change", 0),
            participants=data.get("participants", []),
            created_at=created_at,
        )
