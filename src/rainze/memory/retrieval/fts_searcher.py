"""
FTS5 全文检索器
FTS5 Full-Text Searcher

本模块实现基于 SQLite FTS5 的全文检索功能。
This module implements full-text search based on SQLite FTS5.

Reference:
    - MOD-Memory.md §3.3: HybridRetriever - FTS5 检索

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

# aiosqlite 用于异步数据库操作 / aiosqlite for async database operations
try:
    import aiosqlite
except ImportError:
    aiosqlite = None  # type: ignore[assignment, unused-ignore]

if TYPE_CHECKING:
    from ..models import MemoryItem, TimeWindow

logger = logging.getLogger(__name__)


@dataclass
class FTSConfig:
    """
    FTS5 检索配置
    FTS5 search configuration

    Attributes:
        db_path: 数据库路径 / Database path
        table_name: 表名 / Table name
        fts_table_name: FTS 虚拟表名 / FTS virtual table name
        tokenizer: 分词器 / Tokenizer (trigram for Chinese support)
        top_k: 默认返回数量 / Default return count
    """

    db_path: Path = Path("./data/memory.db")
    table_name: str = "memories"
    fts_table_name: str = "memories_fts"
    tokenizer: str = "trigram"  # trigram 支持中文子串匹配 / trigram for Chinese
    top_k: int = 15


class FTSSearcher:
    """
    FTS5 全文检索器
    FTS5 full-text searcher

    使用 SQLite FTS5 扩展实现全文检索。
    Implements full-text search using SQLite FTS5 extension.

    Attributes:
        config: 检索配置 / Search configuration
        _db: 数据库连接 / Database connection
        _initialized: 是否已初始化 / Whether initialized

    Example:
        >>> searcher = FTSSearcher(FTSConfig(db_path=Path("./data/memory.db")))
        >>> await searcher.initialize()
        >>> results = await searcher.search("苹果", top_k=5)
        >>> for memory_id, score in results:
        ...     print(f"{memory_id}: {score}")
    """

    def __init__(self, config: Optional[FTSConfig] = None) -> None:
        """
        初始化 FTS 检索器
        Initialize FTS searcher

        Args:
            config: 检索配置，None 则使用默认配置 / Config, None for default
        """
        self.config = config or FTSConfig()
        self._db: Optional[aiosqlite.Connection] = None
        self._initialized: bool = False

    async def initialize(self) -> None:
        """
        异步初始化数据库连接和表结构
        Async initialize database connection and table structure

        创建必要的表和 FTS5 虚拟表。
        Creates necessary tables and FTS5 virtual table.

        Raises:
            RuntimeError: 当 aiosqlite 未安装时 / When aiosqlite not installed
        """
        if aiosqlite is None:
            raise RuntimeError(
                "aiosqlite is required for FTSSearcher. "
                "Install it with: pip install aiosqlite"
            )

        # 确保数据目录存在 / Ensure data directory exists
        self.config.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._db = await aiosqlite.connect(str(self.config.db_path))
        await self._db.execute("PRAGMA journal_mode=WAL")

        # 创建主表 / Create main table
        await self._db.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.config.table_name} (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                importance REAL DEFAULT 0.5,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                access_count INTEGER DEFAULT 0,
                last_accessed TEXT,
                decay_factor REAL DEFAULT 1.0,
                tags TEXT,
                metadata TEXT,
                is_vectorized INTEGER DEFAULT 0,
                is_archived INTEGER DEFAULT 0,
                conflict_flag INTEGER DEFAULT 0
            )
        """)

        # 创建 rowid 映射表（因为主表使用 TEXT 主键）
        # Create rowid mapping table (since main table uses TEXT primary key)
        await self._db.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.config.table_name}_rowid (
                row_id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id TEXT UNIQUE NOT NULL
            )
        """)

        # 创建 FTS5 虚拟表（独立模式，不使用 external content）
        # Create FTS5 virtual table (standalone mode, no external content)
        await self._db.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS {self.config.fts_table_name}
            USING fts5(
                memory_id,
                content,
                tokenize='{self.config.tokenizer}'
            )
        """)

        await self._db.commit()
        self._initialized = True
        logger.info(f"FTSSearcher initialized with database: {self.config.db_path}")

    async def close(self) -> None:
        """
        关闭数据库连接
        Close database connection
        """
        if self._db is not None:
            await self._db.close()
            self._db = None
            self._initialized = False

    async def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        time_window: Optional["TimeWindow"] = None,
        memory_types: Optional[List[str]] = None,
        min_importance: float = 0.0,
    ) -> List[Tuple[str, float]]:
        """
        执行 FTS5 全文检索
        Execute FTS5 full-text search

        Args:
            query: 检索查询 / Search query
            top_k: 返回数量 / Return count
            time_window: 时间窗口 / Time window
            memory_types: 记忆类型过滤 / Memory type filter
            min_importance: 最小重要度 / Minimum importance

        Returns:
            (memory_id, score) 列表 / List of (memory_id, score)

        Raises:
            RuntimeError: 当未初始化时 / When not initialized
        """
        if not self._initialized or self._db is None:
            raise RuntimeError("FTSSearcher not initialized. Call initialize() first.")

        k = top_k or self.config.top_k

        # 预处理查询（移除特殊字符）
        # Preprocess query (remove special characters)
        clean_query = self._preprocess_query(query)
        if not clean_query:
            return []

        # 对于中文，使用 LIKE 查询（FTS5 unicode61 不支持中文分词）
        # For Chinese, use LIKE query (FTS5 unicode61 doesn't support Chinese tokenization)
        # 检测是否包含中文字符 / Check if contains Chinese characters
        has_chinese = any("\u4e00" <= c <= "\u9fff" for c in clean_query)

        if has_chinese:
            # 使用 LIKE 查询（支持中文）
            # Use LIKE query (supports Chinese)
            sql = f"""
                SELECT
                    m.id,
                    m.importance as score
                FROM {self.config.table_name} m
                WHERE m.content LIKE ?
                    AND m.is_archived = 0
                    AND m.importance >= ?
            """
            params: List[Any] = [f"%{clean_query}%", min_importance]
        else:
            # 使用 FTS5 查询（英文等）
            # Use FTS5 query (for English, etc.)
            sql = f"""
                SELECT
                    fts.memory_id,
                    bm25({self.config.fts_table_name}) as score
                FROM {self.config.fts_table_name} fts
                JOIN {self.config.table_name} m ON fts.memory_id = m.id
                WHERE fts.content MATCH ?
                    AND m.is_archived = 0
                    AND m.importance >= ?
            """
            params = [clean_query, min_importance]

        # 添加时间窗口过滤 / Add time window filter
        if time_window is not None:
            if time_window.start is not None:
                sql += " AND m.created_at >= ?"
                params.append(time_window.start.isoformat())
            if time_window.end is not None:
                sql += " AND m.created_at <= ?"
                params.append(time_window.end.isoformat())

        # 添加记忆类型过滤 / Add memory type filter
        if memory_types:
            placeholders = ",".join("?" * len(memory_types))
            sql += f" AND m.memory_type IN ({placeholders})"
            params.extend(memory_types)

        sql += " ORDER BY score DESC LIMIT ?"
        params.append(k)

        # 执行查询 / Execute query
        try:
            async with self._db.execute(sql, params) as cursor:
                rows = await cursor.fetchall()
                if has_chinese:
                    # LIKE 查询返回 importance 作为分数
                    # LIKE query returns importance as score
                    results = [(row[0], float(row[1])) for row in rows]
                else:
                    # BM25 返回负值，分数越低越好，转换为正分数
                    # BM25 returns negative values, lower is better, convert to positive
                    results = [(row[0], -row[1]) for row in rows]
                return results
        except aiosqlite.OperationalError as e:
            logger.warning(f"FTS5 search failed: {e}, query: {query}")
            return []

    async def insert_memory(self, memory: "MemoryItem") -> None:
        """
        插入记忆到数据库
        Insert memory into database

        Args:
            memory: 记忆项 / Memory item

        Raises:
            RuntimeError: 当未初始化时 / When not initialized
        """
        if not self._initialized or self._db is None:
            raise RuntimeError("FTSSearcher not initialized. Call initialize() first.")

        import json

        # 插入主表 / Insert into main table
        sql = f"""
            INSERT OR REPLACE INTO {self.config.table_name}
            (id, content, memory_type, importance, created_at, updated_at,
             access_count, last_accessed, decay_factor, tags, metadata,
             is_vectorized, is_archived, conflict_flag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            memory.id,
            memory.content,
            memory.memory_type.value,
            memory.importance,
            memory.created_at.isoformat(),
            memory.updated_at.isoformat(),
            memory.access_count,
            memory.last_accessed.isoformat() if memory.last_accessed else None,
            memory.decay_factor,
            json.dumps(memory.tags),
            json.dumps(memory.metadata),
            1 if memory.is_vectorized else 0,
            1 if memory.is_archived else 0,
            1 if memory.conflict_flag else 0,
        )

        await self._db.execute(sql, params)

        # 同步到 FTS5 表 / Sync to FTS5 table
        # 先删除旧记录（如果存在）/ Delete old record if exists
        await self._db.execute(
            f"DELETE FROM {self.config.fts_table_name} WHERE memory_id = ?",
            (memory.id,),
        )
        # 插入新记录 / Insert new record
        await self._db.execute(
            f"INSERT INTO {self.config.fts_table_name} (memory_id, content) VALUES (?, ?)",
            (memory.id, memory.content),
        )

        await self._db.commit()

    async def get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        根据 ID 获取记忆
        Get memory by ID

        Args:
            memory_id: 记忆 ID / Memory ID

        Returns:
            记忆数据字典，不存在返回 None / Memory dict or None
        """
        if not self._initialized or self._db is None:
            raise RuntimeError("FTSSearcher not initialized. Call initialize() first.")

        sql = f"SELECT * FROM {self.config.table_name} WHERE id = ?"

        async with self._db.execute(sql, (memory_id,)) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None

            # 获取列名 / Get column names
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))

    async def get_memory_count(self) -> int:
        """
        获取记忆总数
        Get total memory count

        Returns:
            记忆总数 / Total memory count
        """
        if not self._initialized or self._db is None:
            raise RuntimeError("FTSSearcher not initialized. Call initialize() first.")

        sql = f"SELECT COUNT(*) FROM {self.config.table_name} WHERE is_archived = 0"

        async with self._db.execute(sql) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def update_memory(
        self,
        memory_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """
        更新记忆
        Update memory

        Args:
            memory_id: 记忆 ID / Memory ID
            updates: 更新字段 / Fields to update

        Returns:
            是否更新成功 / Whether update succeeded
        """
        if not self._initialized or self._db is None:
            raise RuntimeError("FTSSearcher not initialized. Call initialize() first.")

        if not updates:
            return False

        # 构建更新语句 / Build update statement
        set_clauses = []
        params = []

        for key, value in updates.items():
            set_clauses.append(f"{key} = ?")
            params.append(value)

        params.append(memory_id)

        sql = f"""
            UPDATE {self.config.table_name}
            SET {', '.join(set_clauses)}
            WHERE id = ?
        """

        result = await self._db.execute(sql, params)
        await self._db.commit()

        rowcount = getattr(result, "rowcount", 0)
        return rowcount is not None and rowcount > 0

    async def delete_memory(self, memory_id: str) -> bool:
        """
        删除记忆
        Delete memory

        Args:
            memory_id: 记忆 ID / Memory ID

        Returns:
            是否删除成功 / Whether delete succeeded
        """
        if not self._initialized or self._db is None:
            raise RuntimeError("FTSSearcher not initialized. Call initialize() first.")

        # 从 FTS5 表删除 / Delete from FTS5 table
        await self._db.execute(
            f"DELETE FROM {self.config.fts_table_name} WHERE memory_id = ?",
            (memory_id,),
        )

        # 从主表删除 / Delete from main table
        sql = f"DELETE FROM {self.config.table_name} WHERE id = ?"
        result = await self._db.execute(sql, (memory_id,))
        await self._db.commit()

        rowcount = getattr(result, "rowcount", 0)
        return rowcount is not None and rowcount > 0

    def _preprocess_query(self, query: str) -> str:
        """
        预处理查询字符串
        Preprocess query string

        移除 FTS5 特殊字符，避免语法错误。
        Remove FTS5 special characters to avoid syntax errors.

        Args:
            query: 原始查询 / Original query

        Returns:
            清理后的查询 / Cleaned query
        """
        # 移除 FTS5 特殊字符 / Remove FTS5 special characters
        # 特殊字符: " * - + ^ : ( ) { } [ ]
        cleaned = re.sub(r'["\*\-\+\^\:\(\)\{\}\[\]]', " ", query)

        # 移除多余空格 / Remove extra spaces
        cleaned = " ".join(cleaned.split())

        return cleaned.strip()

    @property
    def is_initialized(self) -> bool:
        """
        检查是否已初始化
        Check if initialized

        Returns:
            是否已初始化 / Whether initialized
        """
        return self._initialized
