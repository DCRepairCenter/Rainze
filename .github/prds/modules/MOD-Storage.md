# MOD-Storage: 数据持久化模块

> **模块ID**: `rainze.storage`
> **版本**: v1.0.0
> **优先级**: P0
> **依赖**: Core
> **关联PRD**: [PRD-Rainze.md](../PRD-Rainze.md) v3.1.0 §0.4

---

## 1. 模块概述

### 1.1 职责定义

Storage模块提供统一的数据持久化能力：

- **SQLite管理**: 结构化数据存储、FTS5全文搜索
- **FAISS索引**: 向量索引的创建、更新、持久化
- **JSON存储**: 配置文件、状态文件的读写
- **备份恢复**: 自动备份、崩溃恢复

### 1.2 技术选型

| 组件 | 技术 | 理由 |
|------|------|------|
| 关系存储 | SQLite + FTS5 | 轻量、零配置、支持全文搜索 |
| 向量索引 | FAISS | Meta开源、本地运行、工业级 |
| 加密 | SQLCipher (可选) | AES-256加密 |

---

## 2. 目录结构

```
src/rainze/storage/
├── __init__.py
├── database.py           # SQLite数据库管理
├── repository.py         # 通用仓储模式
├── faiss_index.py        # FAISS向量索引
├── json_store.py         # JSON文件存储
├── backup.py             # 备份与恢复
├── migrations/           # 数据库迁移脚本
│   ├── __init__.py
│   └── v001_initial.py
└── schemas/              # 数据库表Schema
    ├── __init__.py
    └── tables.py
```

---

## 3. 类设计

### 3.1 Database (数据库管理)

```python
# src/rainze/storage/database.py

from typing import Optional, AsyncIterator, Any, Dict, List
from pathlib import Path
from contextlib import asynccontextmanager
import aiosqlite

class Database:
    """
    SQLite数据库管理器。
    
    支持:
    - 异步连接池
    - 事务管理
    - FTS5全文搜索
    - 自动迁移
    
    Attributes:
        db_path: 数据库文件路径
        _pool: 连接池
    """
    
    def __init__(
        self, 
        db_path: Path,
        enable_fts5: bool = True,
        enable_encryption: bool = False,
        encryption_key: Optional[str] = None
    ) -> None:
        """
        初始化数据库管理器。
        
        Args:
            db_path: 数据库文件路径
            enable_fts5: 启用FTS5扩展
            enable_encryption: 启用SQLCipher加密
            encryption_key: 加密密钥
        """
        ...
    
    async def initialize(self) -> None:
        """
        初始化数据库。
        
        执行:
        1. 创建连接池
        2. 启用FTS5
        3. 运行迁移
        """
        ...
    
    @asynccontextmanager
    async def connection(self) -> AsyncIterator[aiosqlite.Connection]:
        """
        获取数据库连接的上下文管理器。
        
        Yields:
            数据库连接
        """
        ...
    
    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[aiosqlite.Connection]:
        """
        事务上下文管理器。
        
        自动提交或回滚。
        
        Yields:
            数据库连接
        """
        ...
    
    async def execute(
        self, 
        sql: str, 
        params: Optional[tuple] = None
    ) -> aiosqlite.Cursor:
        """
        执行SQL语句。
        
        Args:
            sql: SQL语句
            params: 参数
            
        Returns:
            游标对象
        """
        ...
    
    async def fetch_one(
        self, 
        sql: str, 
        params: Optional[tuple] = None
    ) -> Optional[Dict[str, Any]]:
        """
        查询单条记录。
        
        Args:
            sql: SQL语句
            params: 参数
            
        Returns:
            记录字典或None
        """
        ...
    
    async def fetch_all(
        self, 
        sql: str, 
        params: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        查询所有记录。
        
        Args:
            sql: SQL语句
            params: 参数
            
        Returns:
            记录列表
        """
        ...
    
    async def fts_search(
        self, 
        table: str, 
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        FTS5全文搜索。
        
        Args:
            table: FTS表名
            query: 搜索词
            limit: 返回数量限制
            
        Returns:
            匹配记录列表
        """
        ...
    
    async def close(self) -> None:
        """关闭数据库连接。"""
        ...
```

### 3.2 Repository (通用仓储)

```python
# src/rainze/storage/repository.py

from typing import TypeVar, Generic, Optional, List, Dict, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

T = TypeVar("T")

@dataclass
class Entity:
    """实体基类。"""
    id: str
    created_at: datetime
    updated_at: datetime

class Repository(ABC, Generic[T]):
    """
    通用仓储抽象基类。
    
    提供CRUD操作的统一接口。
    """
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        """根据ID获取实体。"""
        ...
    
    @abstractmethod
    async def get_all(
        self, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[T]:
        """获取所有实体（分页）。"""
        ...
    
    @abstractmethod
    async def save(self, entity: T) -> T:
        """保存实体（新增或更新）。"""
        ...
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """删除实体。"""
        ...
    
    @abstractmethod
    async def count(self) -> int:
        """统计实体总数。"""
        ...


class SQLiteRepository(Repository[T]):
    """
    SQLite仓储实现。
    
    Attributes:
        db: 数据库管理器
        table_name: 表名
        entity_class: 实体类
    """
    
    def __init__(
        self, 
        db: Database, 
        table_name: str,
        entity_class: type
    ) -> None:
        """
        初始化仓储。
        
        Args:
            db: 数据库管理器
            table_name: 表名
            entity_class: 实体类
        """
        ...
    
    async def get_by_id(self, id: str) -> Optional[T]:
        ...
    
    async def get_all(
        self, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[T]:
        ...
    
    async def save(self, entity: T) -> T:
        ...
    
    async def delete(self, id: str) -> bool:
        ...
    
    async def count(self) -> int:
        ...
    
    async def find_by(
        self, 
        conditions: Dict[str, Any],
        limit: int = 100
    ) -> List[T]:
        """
        条件查询。
        
        Args:
            conditions: 查询条件字典
            limit: 返回数量限制
            
        Returns:
            匹配实体列表
        """
        ...
```

### 3.3 FAISSIndex (向量索引)

```python
# src/rainze/storage/faiss_index.py

from typing import List, Tuple, Optional
from pathlib import Path
import numpy as np

class FAISSIndex:
    """
    FAISS向量索引管理器。
    
    支持:
    - 多种索引类型（Flat、IVF）
    - 自动选择最优索引
    - 持久化与恢复
    - 增量更新
    
    Attributes:
        index_path: 索引文件路径
        dimension: 向量维度
        index_type: 索引类型
    """
    
    def __init__(
        self,
        index_path: Path,
        dimension: int = 768,
        index_type: str = "auto"
    ) -> None:
        """
        初始化FAISS索引。
        
        Args:
            index_path: 索引文件路径
            dimension: 向量维度
            index_type: 索引类型 ("flat", "ivf", "auto")
        """
        ...
    
    def load(self) -> bool:
        """
        从磁盘加载索引。
        
        Returns:
            是否加载成功
        """
        ...
    
    def save(self) -> None:
        """保存索引到磁盘。"""
        ...
    
    def add(
        self, 
        ids: List[str], 
        vectors: np.ndarray
    ) -> None:
        """
        添加向量。
        
        Args:
            ids: ID列表
            vectors: 向量数组 (N, dimension)
        """
        ...
    
    def search(
        self, 
        query_vector: np.ndarray,
        top_k: int = 10,
        threshold: Optional[float] = None
    ) -> List[Tuple[str, float]]:
        """
        相似度搜索。
        
        Args:
            query_vector: 查询向量 (1, dimension)
            top_k: 返回数量
            threshold: 相似度阈值
            
        Returns:
            [(id, similarity_score), ...]
        """
        ...
    
    def remove(self, ids: List[str]) -> int:
        """
        删除向量。
        
        Args:
            ids: 要删除的ID列表
            
        Returns:
            实际删除数量
        """
        ...
    
    def rebuild(self, vectors: np.ndarray, ids: List[str]) -> None:
        """
        重建索引。
        
        Args:
            vectors: 所有向量
            ids: 所有ID
        """
        ...
    
    @property
    def size(self) -> int:
        """当前索引中的向量数量。"""
        ...
    
    def optimize_index_type(self) -> None:
        """
        根据数据量自动优化索引类型。
        
        - <10,000: IndexFlatIP
        - >=10,000: IndexIVFFlat
        """
        ...
```

### 3.4 JSONStore (JSON存储)

```python
# src/rainze/storage/json_store.py

from typing import TypeVar, Type, Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel
import aiofiles
import json

T = TypeVar("T", bound=BaseModel)

class JSONStore:
    """
    JSON文件存储管理器。
    
    支持:
    - 异步读写
    - Pydantic模型序列化
    - 原子写入（防止损坏）
    - 自动创建目录
    
    Attributes:
        base_dir: 基础目录
    """
    
    def __init__(self, base_dir: Path) -> None:
        """
        初始化JSON存储。
        
        Args:
            base_dir: 基础目录
        """
        ...
    
    async def load(
        self, 
        filename: str, 
        model: Type[T],
        default: Optional[T] = None
    ) -> Optional[T]:
        """
        加载JSON文件并反序列化为Pydantic模型。
        
        Args:
            filename: 文件名（相对于base_dir）
            model: Pydantic模型类
            default: 文件不存在时的默认值
            
        Returns:
            模型实例或None
        """
        ...
    
    async def save(
        self, 
        filename: str, 
        data: BaseModel,
        atomic: bool = True
    ) -> None:
        """
        保存Pydantic模型到JSON文件。
        
        Args:
            filename: 文件名
            data: 模型实例
            atomic: 是否原子写入
        """
        ...
    
    async def load_raw(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        加载原始JSON数据。
        
        Args:
            filename: 文件名
            
        Returns:
            字典数据或None
        """
        ...
    
    async def save_raw(
        self, 
        filename: str, 
        data: Dict[str, Any]
    ) -> None:
        """
        保存原始字典到JSON文件。
        
        Args:
            filename: 文件名
            data: 字典数据
        """
        ...
    
    async def exists(self, filename: str) -> bool:
        """
        检查文件是否存在。
        
        Args:
            filename: 文件名
            
        Returns:
            是否存在
        """
        ...
    
    async def delete(self, filename: str) -> bool:
        """
        删除文件。
        
        Args:
            filename: 文件名
            
        Returns:
            是否删除成功
        """
        ...
```

### 3.5 BackupManager (备份管理)

```python
# src/rainze/storage/backup.py

from typing import Optional, List
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

@dataclass
class BackupInfo:
    """备份信息。"""
    backup_id: str
    timestamp: datetime
    path: Path
    size_bytes: int
    is_auto: bool

class BackupManager:
    """
    备份与恢复管理器。
    
    支持:
    - 自动定时备份
    - 手动备份
    - 备份轮转（保留最近N个）
    - 崩溃恢复检测
    
    Attributes:
        backup_dir: 备份目录
        max_backups: 最大备份数量
    """
    
    def __init__(
        self,
        backup_dir: Path,
        max_backups: int = 5,
        auto_backup_interval_hours: int = 24
    ) -> None:
        """
        初始化备份管理器。
        
        Args:
            backup_dir: 备份目录
            max_backups: 最大保留备份数
            auto_backup_interval_hours: 自动备份间隔（小时）
        """
        ...
    
    async def create_backup(
        self,
        db_path: Path,
        state_path: Path,
        is_auto: bool = False
    ) -> BackupInfo:
        """
        创建备份。
        
        Args:
            db_path: 数据库文件路径
            state_path: 状态文件路径
            is_auto: 是否自动备份
            
        Returns:
            备份信息
        """
        ...
    
    async def restore_backup(
        self,
        backup_id: str,
        target_db_path: Path,
        target_state_path: Path
    ) -> bool:
        """
        恢复备份。
        
        Args:
            backup_id: 备份ID
            target_db_path: 目标数据库路径
            target_state_path: 目标状态文件路径
            
        Returns:
            是否恢复成功
        """
        ...
    
    async def list_backups(self) -> List[BackupInfo]:
        """
        列出所有备份。
        
        Returns:
            备份信息列表（按时间倒序）
        """
        ...
    
    async def delete_backup(self, backup_id: str) -> bool:
        """
        删除指定备份。
        
        Args:
            backup_id: 备份ID
            
        Returns:
            是否删除成功
        """
        ...
    
    async def cleanup_old_backups(self) -> int:
        """
        清理旧备份（保留max_backups个）。
        
        Returns:
            删除的备份数量
        """
        ...
    
    def detect_crash_recovery(self) -> bool:
        """
        检测是否需要崩溃恢复。
        
        检查:
        - 上次是否正常关闭
        - 数据库完整性
        
        Returns:
            是否需要恢复
        """
        ...
```

---

## 4. 数据库Schema

```python
# src/rainze/storage/schemas/tables.py

# ========== 记忆表 ==========
MEMORIES_TABLE = """
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content TEXT NOT NULL,
    memory_type TEXT NOT NULL,  -- conversation/event/preference/fact
    importance REAL DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    decay_factor REAL DEFAULT 1.0,
    tags TEXT,  -- JSON数组
    metadata TEXT,  -- JSON对象
    is_archived BOOLEAN DEFAULT FALSE,
    is_vectorized BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance);
CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at);
"""

# FTS5全文搜索表
MEMORIES_FTS_TABLE = """
CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
    content,
    tags,
    content='memories',
    content_rowid='rowid',
    tokenize='unicode61'
);
"""

# ========== 用户偏好表 ==========
USER_PREFERENCES_TABLE = """
CREATE TABLE IF NOT EXISTS user_preferences (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    source_memory_ids TEXT,  -- JSON数组
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# ========== 行为模式表 ==========
BEHAVIOR_PATTERNS_TABLE = """
CREATE TABLE IF NOT EXISTS behavior_patterns (
    pattern_type TEXT PRIMARY KEY,
    pattern_data TEXT NOT NULL,  -- JSON
    sample_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# ========== 聊天历史表 ==========
CHAT_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS chat_history (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,  -- user/assistant/system
    content TEXT NOT NULL,
    emotion_tag TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT  -- JSON
);

CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_history(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_timestamp ON chat_history(timestamp);
"""

# ========== 日程表 ==========
SCHEDULES_TABLE = """
CREATE TABLE IF NOT EXISTS schedules (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    remind_at TIMESTAMP NOT NULL,
    advance_minutes INTEGER DEFAULT 5,
    repeat_type TEXT,  -- once/daily/weekly
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_schedules_remind ON schedules(remind_at);
"""
```

---

## 5. 配置Schema

```python
# src/rainze/storage/config.py

from pydantic import BaseModel, Field
from pathlib import Path
from typing import Optional

class DatabaseConfig(BaseModel):
    """数据库配置。"""
    db_path: Path = Field(default=Path("./data/memory.db"))
    enable_fts5: bool = True
    enable_encryption: bool = False
    encryption_key_env: str = "RAINZE_DB_KEY"
    pool_size: int = Field(default=5, ge=1, le=20)
    busy_timeout_ms: int = Field(default=5000, ge=1000)

class FAISSConfig(BaseModel):
    """FAISS配置。"""
    index_path: Path = Field(default=Path("./data/memory.faiss"))
    ids_path: Path = Field(default=Path("./data/memory_ids.pkl"))
    dimension: int = Field(default=768, ge=64, le=4096)
    index_type: str = Field(default="auto", pattern="^(flat|ivf|auto)$")
    ivf_nlist: int = Field(default=100, ge=10)

class BackupConfig(BaseModel):
    """备份配置。"""
    backup_dir: Path = Field(default=Path("./backups"))
    max_backups: int = Field(default=5, ge=1, le=30)
    auto_backup_interval_hours: int = Field(default=24, ge=1)
    enable_auto_backup: bool = True

class StorageConfig(BaseModel):
    """存储模块总配置 (storage_settings.json)。"""
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    faiss: FAISSConfig = Field(default_factory=FAISSConfig)
    backup: BackupConfig = Field(default_factory=BackupConfig)
```

---

## 6. 测试要点

| 测试类型 | 测试内容 |
|---------|---------|
| 单元测试 | Database CRUD操作 |
| 单元测试 | FAISSIndex 增删改查 |
| 单元测试 | JSONStore 读写 |
| 集成测试 | FTS5全文搜索准确性 |
| 集成测试 | 备份恢复完整性 |
| 性能测试 | 10万条记忆检索延迟 (<100ms) |

---

## 7. 依赖清单

```toml
aiosqlite = ">=0.20"
faiss-cpu = ">=1.9"
aiofiles = ">=24.1"
sqlalchemy = ">=2.0"  # 可选，用于ORM
```

---

## 8. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.0 | 2025-12-29 | 初始版本 |
