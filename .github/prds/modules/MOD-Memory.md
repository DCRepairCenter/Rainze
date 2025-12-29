# MOD-Memory - 记忆系统模块

> **模块版本**: v1.0.0
> **所属层级**: 业务层 (Business Layer)
> **依赖模块**: MOD-Core, MOD-Storage, MOD-RustCore
> **关联PRD**: PRD-Rainze.md §0.2, §0.4
> **最后更新**: 2025-12-29

---

## 1. 模块概述

### 1.1 职责定义

Memory模块负责Rainze的3层记忆架构实现，包括：

- **Layer 1 (Identity Layer)**: 身份层 - 角色设定、用户档案（永久存储）
- **Layer 2 (Working Memory)**: 工作记忆 - 会话上下文、实时状态（内存级）
- **Layer 3 (Long-term Memory)**: 长期记忆 - Facts/Episodes/Relations（持久化）

核心能力：

1. 记忆的创建、存储、检索、更新、归档
2. 混合检索策略（FTS5 + FAISS向量）
3. 记忆重要度评估与衰减
4. 矛盾检测与Reflection生成
5. 记忆整合与遗忘机制

### 1.2 设计原则

```
┌─────────────────────────────────────────────────────────────────┐
│                      Memory Architecture                        │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: Identity Layer (不可变)                               │
│  ├── SystemPrompt (角色设定)                                    │
│  └── MasterProfile (用户档案)                                   │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: Working Memory (会话级)                               │
│  ├── ConversationHistory (对话历史)                             │
│  ├── RealtimeState (实时状态)                                   │
│  └── EnvironmentContext (环境感知)                              │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: Long-term Memory (持久化)                             │
│  ├── Facts (事实记忆)                                           │
│  ├── Episodes (情景记忆)                                        │
│  └── Relations (关系记忆)                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 目录结构

```
src/rainze/memory/
├── __init__.py
├── manager.py              # MemoryManager - 记忆管理器主入口
├── coordinator.py          # MemoryCoordinator - 记忆协调器
│
├── layers/                 # 记忆层实现
│   ├── __init__.py
│   ├── identity.py         # IdentityLayer - 身份层
│   ├── working.py          # WorkingMemory - 工作记忆
│   └── longterm.py         # LongTermMemory - 长期记忆
│
├── retrieval/              # 检索系统
│   ├── __init__.py
│   ├── strategy.py         # RetrievalStrategy - 检索策略选择
│   ├── fts_searcher.py     # FTSSearcher - FTS5全文检索
│   ├── vector_searcher.py  # VectorSearcher - 向量检索
│   ├── hybrid.py           # HybridRetriever - 混合检索
│   └── reranker.py         # Reranker - 重排序器 (调用Rust)
│
├── lifecycle/              # 生命周期管理
│   ├── __init__.py
│   ├── importance.py       # ImportanceEvaluator - 重要度评估
│   ├── decay.py            # DecayManager - 衰减管理
│   ├── archival.py         # ArchivalManager - 归档管理
│   └── consolidation.py    # ConsolidationManager - 记忆整合
│
├── analysis/               # 记忆分析
│   ├── __init__.py
│   ├── conflict.py         # ConflictDetector - 矛盾检测
│   ├── reflection.py       # ReflectionGenerator - 反思生成
│   └── pattern.py          # PatternAnalyzer - 行为模式分析
│
└── models/                 # 数据模型
    ├── __init__.py
    ├── memory_item.py      # 记忆项模型
    ├── retrieval_result.py # 检索结果模型
    └── memory_index.py     # 记忆索引模型
```

---

## 3. 核心类设计

### 3.1 MemoryManager - 记忆管理器

```python
"""记忆管理器 - 记忆系统主入口"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class MemoryType(Enum):
    """记忆类型枚举"""
    FACT = "fact"           # 事实记忆
    EPISODE = "episode"     # 情景记忆
    RELATION = "relation"   # 关系记忆
    REFLECTION = "reflection"  # 反思记忆


class MemoryManager:
    """
    记忆管理器
    
    职责:
    - 统一管理3层记忆的读写
    - 协调记忆检索与存储
    - 管理记忆生命周期
    
    Attributes:
        identity_layer: 身份层实例
        working_memory: 工作记忆实例
        longterm_memory: 长期记忆实例
        coordinator: 记忆协调器
        retriever: 混合检索器
    """
    
    def __init__(
        self,
        config: "MemoryConfig",
        storage: "StorageManager",
        rust_core: "RustCoreModule"
    ) -> None:
        """
        初始化记忆管理器
        
        Args:
            config: 记忆配置
            storage: 存储管理器
            rust_core: Rust核心模块（用于向量检索）
        """
        ...
    
    async def initialize(self) -> None:
        """
        异步初始化
        
        - 加载身份层数据
        - 初始化FAISS索引
        - 恢复待处理向量化队列
        """
        ...
    
    # ==================== 记忆写入 ====================
    
    async def create_memory(
        self,
        content: str,
        memory_type: MemoryType,
        importance: Optional[float] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_context: Optional["ConversationContext"] = None
    ) -> "MemoryItem":
        """
        创建新记忆
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型
            importance: 重要度 (0-1)，None则自动评估
            tags: 标签列表
            metadata: 元数据
            source_context: 来源上下文
            
        Returns:
            创建的记忆项
            
        Note:
            - 立即写入SQLite（FTS5可检索）
            - 异步加入向量化队列
        """
        ...
    
    async def create_fact(
        self,
        subject: str,
        predicate: str,
        obj: str,
        confidence: float = 1.0,
        source_memory_ids: Optional[List[str]] = None
    ) -> "FactItem":
        """
        创建事实记忆
        
        Args:
            subject: 主语 (如 "主人")
            predicate: 谓语 (如 "喜欢")
            obj: 宾语 (如 "苹果")
            confidence: 置信度 (0-1)
            source_memory_ids: 来源记忆ID列表
            
        Returns:
            事实记忆项
            
        Example:
            >>> await manager.create_fact("主人", "喜欢", "苹果", confidence=0.9)
        """
        ...
    
    async def create_episode(
        self,
        summary: str,
        emotion_tag: Optional[str] = None,
        affinity_change: int = 0,
        participants: Optional[List[str]] = None
    ) -> "EpisodeItem":
        """
        创建情景记忆
        
        Args:
            summary: 情景摘要
            emotion_tag: 情感标签
            affinity_change: 好感度变化
            participants: 参与者列表
            
        Returns:
            情景记忆项
        """
        ...
    
    # ==================== 记忆检索 ====================
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        memory_types: Optional[List[MemoryType]] = None,
        time_window: Optional["TimeWindow"] = None,
        min_importance: float = 0.0
    ) -> "RetrievalResult":
        """
        混合检索记忆
        
        Args:
            query: 检索查询
            top_k: 返回数量
            memory_types: 限定记忆类型
            time_window: 时间窗口限制
            min_importance: 最小重要度阈值
            
        Returns:
            检索结果，包含记忆列表和元数据
            
        Note:
            - 自动选择检索策略 (FTS5优先/向量优先/并行)
            - 应用阈值门控 (score < 0.65 视为无相关记忆)
        """
        ...
    
    async def search_facts(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        obj: Optional[str] = None
    ) -> List["FactItem"]:
        """
        检索事实记忆
        
        Args:
            subject: 主语筛选
            predicate: 谓语筛选
            obj: 宾语筛选
            
        Returns:
            匹配的事实列表
        """
        ...
    
    async def get_user_profile_summary(self) -> "UserProfileSummary":
        """
        获取用户画像摘要
        
        Returns:
            用户偏好、习惯、近期关注等摘要
        """
        ...
    
    # ==================== 记忆索引 ====================
    
    async def get_memory_index(
        self,
        query: str,
        count: int = 30
    ) -> List["MemoryIndexItem"]:
        """
        获取记忆索引列表（用于Prompt注入）
        
        Args:
            query: 相关性查询
            count: 索引数量
            
        Returns:
            记忆索引列表，每项包含:
            - id: 记忆ID
            - time_ago: 时间描述 (如 "3天前")
            - summary: 20字摘要
            - importance: 重要度
        """
        ...
    
    async def expand_memory(self, memory_id: str) -> Optional["MemoryItem"]:
        """
        展开记忆全文（响应 [RECALL:#mem_xxx] 指令）
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            完整记忆内容，不存在则返回None
        """
        ...
    
    # ==================== 身份层 ====================
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        ...
    
    def get_master_profile(self) -> "MasterProfile":
        """获取用户档案"""
        ...
    
    async def update_master_profile(
        self,
        updates: Dict[str, Any]
    ) -> "MasterProfile":
        """
        更新用户档案
        
        Args:
            updates: 要更新的字段
            
        Returns:
            更新后的档案
        """
        ...
    
    # ==================== 工作记忆 ====================
    
    def get_conversation_history(
        self,
        max_turns: Optional[int] = None
    ) -> List["ConversationTurn"]:
        """
        获取对话历史
        
        Args:
            max_turns: 最大轮数，None则使用配置值
            
        Returns:
            对话历史列表
        """
        ...
    
    def add_conversation_turn(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        添加对话轮次
        
        Args:
            role: 角色 ("user" / "assistant")
            content: 内容
            metadata: 元数据
        """
        ...
    
    def clear_conversation(self) -> None:
        """清空当前会话对话历史"""
        ...
    
    # ==================== 生命周期 ====================
    
    async def run_consolidation(self) -> "ConsolidationResult":
        """
        执行记忆整合（建议在用户空闲时调用）
        
        Returns:
            整合结果，包含:
            - generated_reflections: 生成的反思数
            - detected_conflicts: 检测到的矛盾数
            - extracted_facts: 提取的事实数
            - archived_memories: 归档的记忆数
        """
        ...
    
    async def run_decay(self) -> int:
        """
        执行记忆衰减
        
        Returns:
            受影响的记忆数量
        """
        ...
    
    async def archive_old_memories(self) -> int:
        """
        归档旧记忆
        
        Returns:
            归档的记忆数量
        """
        ...
    
    # ==================== 统计与调试 ====================
    
    async def get_stats(self) -> "MemoryStats":
        """
        获取记忆统计信息
        
        Returns:
            统计信息，包含各类记忆数量、存储大小等
        """
        ...
    
    async def health_check(self) -> "HealthCheckResult":
        """
        健康检查
        
        Returns:
            健康状态，包含待向量化队列长度、索引状态等
        """
        ...
```

### 3.2 MemoryCoordinator - 记忆协调器

```python
"""记忆协调器 - 控制Prompt注入的记忆量"""

from enum import Enum
from typing import Optional, Dict, Any


class SceneType(Enum):
    """场景类型"""
    SIMPLE = "simple"     # 简单场景：点击、拖拽
    MEDIUM = "medium"     # 中等场景：整点报时、系统警告
    COMPLEX = "complex"   # 复杂场景：自由对话


class MemoryCoordinator:
    """
    记忆协调器
    
    职责:
    - 根据场景类型决定是否检索长期记忆
    - 控制注入到Prompt的总Token量
    - 管理记忆缓存
    
    Attributes:
        memory_manager: 记忆管理器引用
        token_budget: Token预算配置
        cache: 检索结果缓存
    """
    
    def __init__(
        self,
        memory_manager: "MemoryManager",
        config: "CoordinatorConfig"
    ) -> None:
        """
        初始化协调器
        
        Args:
            memory_manager: 记忆管理器
            config: 协调器配置
        """
        ...
    
    def classify_scene(
        self,
        event_type: str,
        interaction_type: Optional[str] = None,
        has_user_input: bool = False
    ) -> SceneType:
        """
        场景分类
        
        Args:
            event_type: 事件类型
            interaction_type: 交互类型
            has_user_input: 是否有用户输入
            
        Returns:
            场景类型
        """
        ...
    
    async def prepare_context(
        self,
        scene_type: SceneType,
        query: Optional[str] = None,
        event_context: Optional[Dict[str, Any]] = None
    ) -> "PreparedContext":
        """
        准备Prompt上下文
        
        Args:
            scene_type: 场景类型
            query: 用户输入/检索查询
            event_context: 事件上下文
            
        Returns:
            准备好的上下文，包含:
            - identity_context: 身份层内容
            - working_context: 工作记忆内容
            - longterm_context: 长期记忆内容 (如需要)
            - total_tokens: 总Token数估算
        """
        ...
    
    def should_retrieve_longterm(
        self,
        scene_type: SceneType,
        query: Optional[str] = None
    ) -> bool:
        """
        判断是否需要检索长期记忆
        
        Args:
            scene_type: 场景类型
            query: 用户输入
            
        Returns:
            是否需要检索
            
        Note:
            触发检索的条件:
            - COMPLEX场景
            - 检测到记忆关键词 ("之前/上次/记得/你说过")
        """
        ...
    
    def get_token_budget(self, scene_type: SceneType) -> "TokenBudget":
        """
        获取Token预算
        
        Args:
            scene_type: 场景类型
            
        Returns:
            各层的Token预算分配
        """
        ...
    
    def invalidate_cache(self, keys: Optional[List[str]] = None) -> None:
        """
        使缓存失效
        
        Args:
            keys: 要失效的缓存键，None则清空全部
        """
        ...
```

### 3.3 HybridRetriever - 混合检索器

```python
"""混合检索器 - FTS5 + FAISS向量检索"""

from enum import Enum
from typing import Optional, List, Tuple


class RetrievalStrategy(Enum):
    """检索策略"""
    FTS5_PRIMARY = "fts5_primary"       # FTS5优先（有明确实体词）
    VECTOR_PRIMARY = "vector_primary"   # 向量优先（无明确实体词）
    PARALLEL = "parallel"               # 并行检索


class HybridRetriever:
    """
    混合检索器
    
    职责:
    - 智能选择检索策略
    - 执行FTS5全文检索
    - 执行FAISS向量检索
    - 合并结果并重排序
    
    Attributes:
        fts_searcher: FTS5检索器
        vector_searcher: 向量检索器
        reranker: 重排序器 (Rust实现)
        entity_detector: 实体检测器 (Rust实现)
    """
    
    def __init__(
        self,
        storage: "StorageManager",
        rust_core: "RustCoreModule",
        config: "RetrievalConfig"
    ) -> None:
        """
        初始化混合检索器
        
        Args:
            storage: 存储管理器
            rust_core: Rust核心模块
            config: 检索配置
        """
        ...
    
    def select_strategy(self, query: str) -> RetrievalStrategy:
        """
        智能选择检索策略
        
        Args:
            query: 检索查询
            
        Returns:
            推荐的检索策略
            
        Note:
            - 检测到实体词 → FTS5_PRIMARY
            - 无明确实体词 → VECTOR_PRIMARY
            - 无法判断 → PARALLEL (fallback)
        """
        ...
    
    async def search(
        self,
        query: str,
        strategy: Optional[RetrievalStrategy] = None,
        top_k: int = 5,
        time_window: Optional["TimeWindow"] = None
    ) -> "RetrievalResult":
        """
        执行混合检索
        
        Args:
            query: 检索查询
            strategy: 检索策略，None则自动选择
            top_k: 返回数量
            time_window: 时间窗口
            
        Returns:
            检索结果
        """
        ...
    
    async def _fts5_search(
        self,
        query: str,
        limit: int = 15,
        time_window: Optional["TimeWindow"] = None
    ) -> List[Tuple[str, float]]:
        """
        FTS5全文检索
        
        Args:
            query: 检索查询
            limit: 结果数量限制
            time_window: 时间窗口
            
        Returns:
            (memory_id, score) 列表
        """
        ...
    
    async def _vector_search(
        self,
        query: str,
        limit: int = 20
    ) -> List[Tuple[str, float]]:
        """
        FAISS向量检索
        
        Args:
            query: 检索查询
            limit: 结果数量限制
            
        Returns:
            (memory_id, similarity_score) 列表
            
        Note:
            如果向量结果 < min_vector_results，
            自动补充FTS5结果
        """
        ...
    
    def _merge_results(
        self,
        fts_results: List[Tuple[str, float]],
        vector_results: List[Tuple[str, float]]
    ) -> List[Tuple[str, float]]:
        """
        合并去重检索结果
        
        Args:
            fts_results: FTS5结果
            vector_results: 向量结果
            
        Returns:
            合并后的结果
        """
        ...
    
    async def _rerank(
        self,
        candidates: List[Tuple[str, float]],
        top_k: int
    ) -> List["RankedMemory"]:
        """
        重排序
        
        Args:
            candidates: 候选结果
            top_k: 最终返回数量
            
        Returns:
            重排序后的结果
            
        Note:
            综合评分 = similarity*0.4 + recency*0.3 + importance*0.2 + frequency*0.1
        """
        ...
    
    def _apply_threshold_gating(
        self,
        results: List["RankedMemory"],
        threshold: float = 0.65
    ) -> Tuple[List["RankedMemory"], bool]:
        """
        阈值门控
        
        Args:
            results: 排序后的结果
            threshold: 相关性阈值
            
        Returns:
            (过滤后的结果, 是否无相关记忆)
        """
        ...
```

### 3.4 ImportanceEvaluator - 重要度评估器

```python
"""重要度评估器"""

from typing import Optional, List


class ImportanceEvaluator:
    """
    重要度评估器
    
    职责:
    - 评估记忆的重要度
    - 支持规则评估和LLM评估
    
    Attributes:
        config: 重要度规则配置
        llm_client: LLM客户端（可选，用于复杂评估）
    """
    
    def __init__(
        self,
        config: "ImportanceConfig",
        llm_client: Optional["LLMClient"] = None
    ) -> None:
        """
        初始化评估器
        
        Args:
            config: 重要度配置
            llm_client: LLM客户端
        """
        ...
    
    def evaluate(
        self,
        content: str,
        context: Optional["EvaluationContext"] = None
    ) -> float:
        """
        评估记忆重要度
        
        Args:
            content: 记忆内容
            context: 评估上下文（好感度变化、关键词等）
            
        Returns:
            重要度分数 (0-1)
            
        Rules:
            - 好感度变化 >= 5 → 0.8+
            - 包含关键词 (记住/喜欢/讨厌/重要) → 0.6+
            - 普通对话 → 0.3-0.5
        """
        ...
    
    def evaluate_batch(
        self,
        items: List["PendingMemory"]
    ) -> List[float]:
        """
        批量评估
        
        Args:
            items: 待评估记忆列表
            
        Returns:
            重要度分数列表
        """
        ...
    
    def _rule_based_evaluate(
        self,
        content: str,
        context: Optional["EvaluationContext"]
    ) -> float:
        """规则评估"""
        ...
    
    async def _llm_evaluate(
        self,
        content: str,
        context: Optional["EvaluationContext"]
    ) -> float:
        """LLM评估（复杂场景）"""
        ...
```

### 3.5 ConflictDetector - 矛盾检测器

```python
"""矛盾检测器"""

from typing import List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ConflictPair:
    """矛盾对"""
    memory_a_id: str
    memory_b_id: str
    subject: str
    attitude_a: str
    attitude_b: str
    confidence: float


class ConflictDetector:
    """
    矛盾检测器
    
    职责:
    - 检测记忆中的矛盾信息
    - 标记冲突记忆
    - 生成态度变化的Reflection
    
    Attributes:
        antonym_pairs: 对立词对配置
        conflict_window_hours: 检测时间窗口
    """
    
    def __init__(self, config: "ConflictConfig") -> None:
        """
        初始化检测器
        
        Args:
            config: 矛盾检测配置
        """
        ...
    
    async def detect_conflicts(
        self,
        new_memory: "MemoryItem",
        existing_memories: Optional[List["MemoryItem"]] = None
    ) -> List[ConflictPair]:
        """
        检测矛盾
        
        Args:
            new_memory: 新记忆
            existing_memories: 现有记忆列表，None则自动检索
            
        Returns:
            检测到的矛盾对列表
        """
        ...
    
    def extract_attitude_triple(
        self,
        content: str
    ) -> Optional[Tuple[str, str, str]]:
        """
        提取态度三元组
        
        Args:
            content: 记忆内容
            
        Returns:
            (实体, 态度, 对象) 或 None
            
        Example:
            "主人喜欢苹果" → ("主人", "喜欢", "苹果")
        """
        ...
    
    def is_antonym(self, attitude_a: str, attitude_b: str) -> bool:
        """
        判断两个态度是否对立
        
        Args:
            attitude_a: 态度A
            attitude_b: 态度B
            
        Returns:
            是否对立
        """
        ...
    
    async def generate_conflict_reflection(
        self,
        conflict: ConflictPair
    ) -> "ReflectionItem":
        """
        生成矛盾反思
        
        Args:
            conflict: 矛盾对
            
        Returns:
            反思记忆项
            
        Example:
            "主人对苹果的态度似乎从喜欢变为讨厌了"
        """
        ...
```

### 3.6 VectorizeQueue - 向量化队列

```python
"""向量化队列管理"""

from typing import Optional, List
from enum import Enum
import asyncio


class VectorizePriority(Enum):
    """向量化优先级"""
    HIGH = "high"       # 高优先级 (importance >= 0.7)
    NORMAL = "normal"   # 普通优先级


class VectorizeQueue:
    """
    向量化队列
    
    职责:
    - 管理待向量化的记忆队列
    - 按优先级异步处理
    - 程序关闭时持久化队列
    
    Attributes:
        high_priority_queue: 高优先级队列
        normal_queue: 普通队列
        worker_task: 后台Worker任务
        embedding_client: Embedding客户端
    """
    
    def __init__(
        self,
        config: "VectorizeConfig",
        embedding_client: "EmbeddingClient",
        faiss_index: "FAISSIndexWrapper"
    ) -> None:
        """
        初始化队列
        
        Args:
            config: 向量化配置
            embedding_client: Embedding客户端
            faiss_index: FAISS索引包装器
        """
        ...
    
    async def start(self) -> None:
        """启动后台Worker"""
        ...
    
    async def stop(self) -> None:
        """停止Worker并持久化队列"""
        ...
    
    def enqueue(
        self,
        memory_id: str,
        content: str,
        importance: float
    ) -> None:
        """
        加入向量化队列
        
        Args:
            memory_id: 记忆ID
            content: 记忆内容
            importance: 重要度
            
        Note:
            importance >= 0.7 加入高优先级队列
        """
        ...
    
    async def _worker_loop(self) -> None:
        """后台Worker循环"""
        ...
    
    async def _process_batch(
        self,
        items: List["PendingVectorize"]
    ) -> int:
        """
        批量处理
        
        Args:
            items: 待处理项
            
        Returns:
            成功处理数量
        """
        ...
    
    async def save_pending_queue(self, path: str) -> None:
        """持久化待处理队列"""
        ...
    
    async def load_pending_queue(self, path: str) -> int:
        """加载待处理队列"""
        ...
    
    def get_queue_length(self) -> Tuple[int, int]:
        """
        获取队列长度
        
        Returns:
            (高优先级数量, 普通数量)
        """
        ...
```

---

## 4. 数据模型

### 4.1 MemoryItem - 记忆项

```python
"""记忆项数据模型"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class MemoryType(Enum):
    FACT = "fact"
    EPISODE = "episode"
    RELATION = "relation"
    REFLECTION = "reflection"


@dataclass
class MemoryItem:
    """
    记忆项
    
    Attributes:
        id: 唯一标识符 (UUID)
        content: 记忆内容
        memory_type: 记忆类型
        importance: 重要度 (0-1)
        created_at: 创建时间
        updated_at: 更新时间
        access_count: 访问次数
        last_accessed: 最后访问时间
        decay_factor: 衰减因子 (0-1)
        tags: 标签列表
        metadata: 元数据
        is_vectorized: 是否已向量化
        is_archived: 是否已归档
        conflict_flag: 是否标记为矛盾
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
        """有效重要度 = 原始重要度 × 衰减因子"""
        return self.importance * self.decay_factor
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        ...
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        """从字典创建"""
        ...


@dataclass
class FactItem:
    """
    事实记忆项
    
    Attributes:
        subject: 主语
        predicate: 谓语
        obj: 宾语
        confidence: 置信度
        source_memory_ids: 来源记忆ID
    """
    
    subject: str
    predicate: str
    obj: str
    confidence: float = 1.0
    source_memory_ids: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class EpisodeItem:
    """
    情景记忆项
    
    Attributes:
        summary: 情景摘要
        emotion_tag: 情感标签
        affinity_change: 好感度变化
        participants: 参与者
    """
    
    summary: str
    emotion_tag: Optional[str] = None
    affinity_change: int = 0
    participants: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
```

### 4.2 RetrievalResult - 检索结果

```python
"""检索结果数据模型"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class RankedMemory:
    """
    排序后的记忆
    
    Attributes:
        memory: 记忆项
        final_score: 综合评分
        similarity_score: 相似度分数
        recency_score: 时间新近度分数
        retrieval_source: 检索来源 (fts5/vector/both)
    """
    
    memory: "MemoryItem"
    final_score: float
    similarity_score: float
    recency_score: float
    retrieval_source: str


@dataclass
class RetrievalResult:
    """
    检索结果
    
    Attributes:
        memories: 检索到的记忆列表
        no_relevant_memory: 是否无相关记忆
        strategy_used: 使用的检索策略
        total_candidates: 候选总数
        retrieval_time_ms: 检索耗时
        query: 原始查询
    """
    
    memories: List[RankedMemory] = field(default_factory=list)
    no_relevant_memory: bool = False
    strategy_used: str = "unknown"
    total_candidates: int = 0
    retrieval_time_ms: float = 0.0
    query: str = ""
    
    @property
    def has_results(self) -> bool:
        """是否有检索结果"""
        return len(self.memories) > 0 and not self.no_relevant_memory


@dataclass
class MemoryIndexItem:
    """
    记忆索引项（用于Prompt注入）
    
    Attributes:
        id: 记忆ID (如 #mem_001)
        time_ago: 时间描述 (如 "3天前")
        summary: 20字摘要
        importance: 重要度
        is_high_priority: 是否高优先级
    """
    
    id: str
    time_ago: str
    summary: str
    importance: float
    is_high_priority: bool = False
    
    def format_for_prompt(self) -> str:
        """格式化为Prompt字符串"""
        priority_mark = "⭐" if self.is_high_priority else ""
        return f"#{self.id} [{self.time_ago}] {self.summary} (重要度{self.importance:.1f}) {priority_mark}"
```

### 4.3 TimeWindow - 时间窗口

```python
"""时间窗口数据模型"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class TimeWindow:
    """
    时间窗口
    
    Attributes:
        start: 开始时间
        end: 结束时间
        source_keyword: 触发关键词
    """
    
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    source_keyword: Optional[str] = None
    
    @classmethod
    def from_keyword(cls, keyword: str) -> Optional["TimeWindow"]:
        """
        从关键词推断时间窗口
        
        Args:
            keyword: 时间关键词
            
        Returns:
            时间窗口，无法推断则返回None
            
        Mappings:
            - "刚才/刚刚" → 1小时内
            - "今天" → 当天
            - "昨天" → 24-48小时
            - "最近/这几天" → 3天内
            - "上次/之前" → 7天内
            - "以前/很久" → 30天内
        """
        ...
    
    @classmethod
    def last_hours(cls, hours: int) -> "TimeWindow":
        """最近N小时"""
        ...
    
    @classmethod
    def last_days(cls, days: int) -> "TimeWindow":
        """最近N天"""
        ...
```

---

## 5. 配置Schema

### 5.1 memory_settings.json

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MemorySettings",
  "description": "记忆系统配置",
  "type": "object",
  "properties": {
    "storage": {
      "type": "object",
      "properties": {
        "db_path": {
          "type": "string",
          "default": "./data/memory.db",
          "description": "SQLite数据库路径"
        },
        "faiss_index_path": {
          "type": "string",
          "default": "./data/memory.faiss",
          "description": "FAISS索引文件路径"
        },
        "archive_path": {
          "type": "string",
          "default": "./data/archive/",
          "description": "归档目录"
        },
        "enable_encryption": {
          "type": "boolean",
          "default": false,
          "description": "是否启用加密"
        }
      }
    },
    
    "embedding": {
      "type": "object",
      "properties": {
        "model": {
          "type": "string",
          "default": "text-embedding-3-small",
          "description": "Embedding模型"
        },
        "dimension": {
          "type": "integer",
          "default": 768,
          "description": "向量维度"
        },
        "batch_size": {
          "type": "integer",
          "default": 32,
          "description": "批处理大小"
        }
      }
    },
    
    "retrieval": {
      "type": "object",
      "properties": {
        "strategy_selection": {
          "type": "object",
          "properties": {
            "enable_smart_selection": {
              "type": "boolean",
              "default": true,
              "description": "启用智能策略选择"
            },
            "fallback_strategy": {
              "type": "string",
              "enum": ["FTS5_PRIMARY", "VECTOR_PRIMARY", "PARALLEL"],
              "default": "PARALLEL",
              "description": "回退策略"
            }
          }
        },
        "fts5_top_k": {
          "type": "integer",
          "default": 15
        },
        "vector_top_k": {
          "type": "integer",
          "default": 20
        },
        "final_top_k": {
          "type": "integer",
          "default": 5
        },
        "similarity_threshold": {
          "type": "number",
          "default": 0.65,
          "description": "相关性阈值"
        },
        "weights": {
          "type": "object",
          "properties": {
            "similarity": { "type": "number", "default": 0.4 },
            "recency": { "type": "number", "default": 0.3 },
            "importance": { "type": "number", "default": 0.2 },
            "frequency": { "type": "number", "default": 0.1 }
          }
        }
      }
    },
    
    "async_vectorization": {
      "type": "object",
      "properties": {
        "enable": {
          "type": "boolean",
          "default": true
        },
        "high_priority_threshold": {
          "type": "number",
          "default": 0.7,
          "description": "高优先级阈值"
        },
        "batch_size": {
          "type": "integer",
          "default": 10
        },
        "process_interval_seconds": {
          "type": "integer",
          "default": 60
        }
      }
    },
    
    "lifecycle": {
      "type": "object",
      "properties": {
        "decay_rate": {
          "type": "number",
          "default": 0.98,
          "description": "每日衰减率"
        },
        "archive_threshold_days": {
          "type": "integer",
          "default": 30
        },
        "archive_percentile": {
          "type": "integer",
          "default": 20,
          "description": "归档百分位（保留Top 80%）"
        },
        "max_memories": {
          "type": "integer",
          "default": 50000
        }
      }
    },
    
    "conflict_detection": {
      "type": "object",
      "properties": {
        "enable": {
          "type": "boolean",
          "default": true
        },
        "antonym_pairs": {
          "type": "array",
          "items": {
            "type": "array",
            "items": { "type": "string" },
            "minItems": 2,
            "maxItems": 2
          },
          "default": [
            ["喜欢", "讨厌"],
            ["喜欢", "不喜欢"],
            ["爱", "恨"],
            ["想要", "不想要"]
          ]
        },
        "conflict_window_hours": {
          "type": "integer",
          "default": 168,
          "description": "矛盾检测时间窗口（小时）"
        }
      }
    },
    
    "importance_rules": {
      "type": "object",
      "properties": {
        "affinity_change_threshold": {
          "type": "integer",
          "default": 5
        },
        "level_up_importance": {
          "type": "number",
          "default": 0.95
        },
        "keyword_boost": {
          "type": "array",
          "items": { "type": "string" },
          "default": ["生日", "重要", "记住", "喜欢", "讨厌"]
        },
        "default_importance": {
          "type": "number",
          "default": 0.5
        }
      }
    }
  }
}
```

---

## 6. 异常定义

```python
"""记忆模块异常定义"""


class MemoryError(Exception):
    """记忆模块基础异常"""
    pass


class MemoryNotFoundError(MemoryError):
    """记忆不存在"""
    
    def __init__(self, memory_id: str):
        self.memory_id = memory_id
        super().__init__(f"Memory not found: {memory_id}")


class RetrievalError(MemoryError):
    """检索失败"""
    
    def __init__(self, message: str, strategy: str = "unknown"):
        self.strategy = strategy
        super().__init__(f"Retrieval failed [{strategy}]: {message}")


class VectorizeError(MemoryError):
    """向量化失败"""
    
    def __init__(self, memory_id: str, reason: str):
        self.memory_id = memory_id
        self.reason = reason
        super().__init__(f"Vectorize failed for {memory_id}: {reason}")


class ConflictDetectionError(MemoryError):
    """矛盾检测失败"""
    pass


class ArchivalError(MemoryError):
    """归档失败"""
    pass


class MemoryQuotaExceededError(MemoryError):
    """记忆配额超限"""
    
    def __init__(self, current: int, max_allowed: int):
        self.current = current
        self.max_allowed = max_allowed
        super().__init__(
            f"Memory quota exceeded: {current}/{max_allowed}"
        )
```

---

## 7. 使用示例

### 7.1 基本记忆操作

```python
from rainze.memory import MemoryManager, MemoryType
from rainze.memory.models import MemoryItem

async def memory_usage_example():
    # 初始化
    manager = MemoryManager(config, storage, rust_core)
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
    result = await manager.search(
        query="之前主人说喜欢什么水果",
        top_k=5
    )
    
    if result.has_results:
        for ranked in result.memories:
            print(f"[{ranked.final_score:.2f}] {ranked.memory.content}")
    else:
        print("未找到相关记忆")
    
    # 获取记忆索引（用于Prompt）
    index_list = await manager.get_memory_index(
        query="水果偏好",
        count=30
    )
    for item in index_list:
        print(item.format_for_prompt())
```

### 7.2 记忆协调器使用

```python
from rainze.memory import MemoryCoordinator, SceneType

async def coordinator_example():
    coordinator = MemoryCoordinator(memory_manager, config)
    
    # 场景分类
    scene = coordinator.classify_scene(
        event_type="user_message",
        has_user_input=True
    )  # → SceneType.COMPLEX
    
    # 准备上下文
    context = await coordinator.prepare_context(
        scene_type=scene,
        query="你还记得我之前说喜欢什么吗？"
    )
    
    print(f"Identity: {len(context.identity_context)} tokens")
    print(f"Working: {len(context.working_context)} tokens")
    print(f"Longterm: {len(context.longterm_context)} tokens")
    print(f"Total: {context.total_tokens} tokens")
```

### 7.3 生命周期管理

```python
async def lifecycle_example():
    # 执行记忆整合（建议在用户空闲时）
    result = await manager.run_consolidation()
    print(f"生成反思: {result.generated_reflections}")
    print(f"检测矛盾: {result.detected_conflicts}")
    print(f"提取事实: {result.extracted_facts}")
    
    # 执行衰减
    decayed = await manager.run_decay()
    print(f"衰减记忆: {decayed} 条")
    
    # 归档旧记忆
    archived = await manager.archive_old_memories()
    print(f"归档记忆: {archived} 条")
```

---

## 8. 测试要点

### 8.1 单元测试

| 测试类 | 测试点 |
|--------|--------|
| `TestMemoryManager` | 记忆CRUD、检索、索引生成 |
| `TestHybridRetriever` | 策略选择、FTS5检索、向量检索、结果合并 |
| `TestImportanceEvaluator` | 规则评估、关键词检测 |
| `TestConflictDetector` | 态度提取、矛盾检测、反思生成 |
| `TestVectorizeQueue` | 入队、优先级排序、批处理、持久化 |
| `TestDecayManager` | 衰减计算、有效重要度 |
| `TestArchivalManager` | 动态阈值、归档条件判断 |

### 8.2 集成测试

| 测试场景 | 验证点 |
|----------|--------|
| 完整对话流程 | 记忆创建 → 向量化 → 检索 → 注入Prompt |
| 矛盾检测流程 | 对立记忆 → 检测 → 生成Reflection |
| 生命周期流程 | 衰减 → 归档 → 恢复 |
| 异常恢复 | 向量化失败 → 回退FTS5检索 |

### 8.3 性能测试

| 指标 | 目标值 |
|------|--------|
| 记忆创建延迟 | <50ms |
| FTS5检索延迟 | <100ms |
| 向量检索延迟 | <200ms |
| 混合检索延迟 | <300ms |
| 10k记忆下检索 | <500ms |

---

## 9. 依赖关系

### 9.1 内部依赖

```
MOD-Memory
├── MOD-Core (ConfigManager, EventBus, Logger)
├── MOD-Storage (Database, Repository, FAISSIndex)
└── MOD-RustCore (FAISSWrapper, Reranker, EntityDetector)
```

### 9.2 外部依赖

| 包 | 版本 | 用途 |
|---|------|------|
| `sqlalchemy` | >=2.0 | 数据库ORM |
| `faiss-cpu` | >=1.9 | 向量索引 |
| `sentence-transformers` | >=3.3 | 本地Embedding回退 |
| `jieba` | >=0.42 | 中文分词 |

---

## 10. 变更记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0.0 | 2025-12-29 | 初始版本 |

---

**文档生成**: Claude Opus 4.5
**审核状态**: 待审核
