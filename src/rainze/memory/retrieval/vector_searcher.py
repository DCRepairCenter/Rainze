"""
FAISS 向量检索器
FAISS Vector Searcher

本模块实现基于 FAISS 的向量相似度检索功能。
This module implements FAISS-based vector similarity search.

Reference:
    - MOD-Memory.md §3.3: HybridRetriever - FAISS 检索
    - PRD §0.4: 混合存储系统

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

# FAISS 延迟导入 / Lazy import FAISS
_faiss_module = None

logger = logging.getLogger(__name__)


def _get_faiss() -> Any:
    """
    获取 FAISS 模块（延迟导入）
    Get FAISS module (lazy import)

    Returns:
        faiss module or raises RuntimeError if not available
    """
    global _faiss_module
    if _faiss_module is None:
        try:
            import faiss

            _faiss_module = faiss
        except ImportError as e:
            raise RuntimeError(
                "faiss-cpu is required for VectorSearcher. "
                "Install it with: pip install faiss-cpu"
            ) from e
    return _faiss_module


@dataclass
class VectorSearcherConfig:
    """
    FAISS 检索配置
    FAISS search configuration

    Attributes:
        index_path: 索引文件路径 / Index file path
        dimension: 向量维度 / Vector dimension
        index_type: 索引类型 / Index type (flat/ivf/hnsw)
        nlist: IVF 聚类数 / IVF cluster count
        nprobe: IVF 搜索探针数 / IVF search probe count
        ef_search: HNSW 搜索参数 / HNSW search parameter
        use_gpu: 是否使用 GPU / Whether to use GPU
        top_k: 默认返回数量 / Default return count
    """

    index_path: Path = Path("./data/faiss/memory.index")
    dimension: int = 384  # paraphrase-multilingual-MiniLM-L12-v2 维度
    index_type: str = "flat"  # flat | ivf | hnsw
    nlist: int = 100  # IVF 聚类数
    nprobe: int = 10  # IVF 搜索探针数
    ef_search: int = 64  # HNSW 搜索参数
    use_gpu: bool = False
    top_k: int = 15


class VectorSearcher:
    """
    FAISS 向量检索器
    FAISS vector searcher

    基于 FAISS 实现高效的向量相似度检索。
    Implements efficient vector similarity search using FAISS.

    Attributes:
        config: 检索配置 / Search configuration
        _index: FAISS 索引 / FAISS index
        _id_map: ID 映射表 / ID mapping table
        _initialized: 是否已初始化 / Whether initialized

    Example:
        >>> searcher = VectorSearcher(VectorSearcherConfig(dimension=384))
        >>> searcher.initialize()
        >>> searcher.add_vectors(["mem_001"], embeddings)
        >>> results = await searcher.search(query_vector, top_k=5)
        >>> for memory_id, score in results:
        ...     print(f"{memory_id}: {score:.4f}")
    """

    def __init__(self, config: Optional[VectorSearcherConfig] = None) -> None:
        """
        初始化向量检索器
        Initialize vector searcher

        Args:
            config: 检索配置，None 则使用默认配置 / Config, None for default
        """
        self.config = config or VectorSearcherConfig()
        self._index: Optional[object] = None
        self._id_map: Dict[int, str] = {}  # FAISS 内部ID → 记忆ID
        self._reverse_id_map: Dict[str, int] = {}  # 记忆ID → FAISS 内部ID
        self._next_id: int = 0
        self._initialized: bool = False

    def initialize(self, load_existing: bool = True) -> None:
        """
        初始化 FAISS 索引
        Initialize FAISS index

        Args:
            load_existing: 是否加载已存在的索引 / Whether to load existing index

        Raises:
            RuntimeError: 当 FAISS 未安装时 / When FAISS not installed
        """
        _get_faiss()  # 验证 FAISS 可用 / Verify FAISS available

        # 尝试加载已有索引 / Try to load existing index
        if load_existing and self.config.index_path.exists():
            self._load_index()
            return

        # 创建新索引 / Create new index
        self._create_index()

        self._initialized = True
        logger.info(
            f"VectorSearcher initialized. Type: {self.config.index_type}, "
            f"Dimension: {self.config.dimension}"
        )

    def _create_index(self) -> None:
        """
        创建新的 FAISS 索引
        Create new FAISS index
        """
        faiss = _get_faiss()
        dim = self.config.dimension

        if self.config.index_type == "flat":
            # Flat L2 索引（精确搜索）/ Flat L2 index (exact search)
            self._index = faiss.IndexFlatIP(dim)  # 内积相似度
        elif self.config.index_type == "ivf":
            # IVF 索引（近似搜索）/ IVF index (approximate search)
            quantizer = faiss.IndexFlatIP(dim)
            self._index = faiss.IndexIVFFlat(
                quantizer, dim, self.config.nlist, faiss.METRIC_INNER_PRODUCT
            )
        elif self.config.index_type == "hnsw":
            # HNSW 索引（图搜索）/ HNSW index (graph search)
            self._index = faiss.IndexHNSWFlat(dim, 32, faiss.METRIC_INNER_PRODUCT)
        else:
            raise ValueError(f"Unknown index type: {self.config.index_type}")

        # 包装为 IDMap 以支持自定义 ID
        # Wrap with IDMap to support custom IDs
        self._index = faiss.IndexIDMap(self._index)

        self._id_map = {}
        self._reverse_id_map = {}
        self._next_id = 0
        self._initialized = True

    def _load_index(self) -> None:
        """
        从文件加载索引
        Load index from file
        """
        import json

        faiss = _get_faiss()

        logger.info(f"Loading FAISS index from {self.config.index_path}")

        self._index = faiss.read_index(str(self.config.index_path))

        # 加载 ID 映射 / Load ID mapping
        id_map_path = self.config.index_path.with_suffix(".json")
        if id_map_path.exists():
            with open(id_map_path, encoding="utf-8") as f:
                data = json.load(f)
                # JSON keys are strings, convert to int
                self._id_map = {int(k): v for k, v in data["id_map"].items()}
                self._reverse_id_map = data.get("reverse_id_map", {})
                self._next_id = data.get("next_id", len(self._id_map))

        self._initialized = True
        logger.info(f"FAISS index loaded. Total vectors: {self._index.ntotal}")  # type: ignore[union-attr]

    def save(self) -> None:
        """
        保存索引到文件
        Save index to file
        """
        import json

        if not self._initialized or self._index is None:
            raise RuntimeError(
                "VectorSearcher not initialized. Call initialize() first."
            )

        faiss = _get_faiss()

        # 确保目录存在 / Ensure directory exists
        self.config.index_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存 FAISS 索引 / Save FAISS index
        faiss.write_index(self._index, str(self.config.index_path))

        # 保存 ID 映射 / Save ID mapping
        id_map_path = self.config.index_path.with_suffix(".json")
        with open(id_map_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "id_map": {str(k): v for k, v in self._id_map.items()},
                    "reverse_id_map": self._reverse_id_map,
                    "next_id": self._next_id,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        logger.info(f"FAISS index saved to {self.config.index_path}")

    def add_vectors(
        self,
        memory_ids: List[str],
        embeddings: "NDArray[np.float32]",
    ) -> int:
        """
        添加向量到索引
        Add vectors to index

        Args:
            memory_ids: 记忆 ID 列表 / Memory ID list
            embeddings: 向量数组 (N, dimension) / Embedding array

        Returns:
            添加的向量数量 / Number of vectors added

        Raises:
            RuntimeError: 当未初始化时 / When not initialized
            ValueError: 当维度不匹配时 / When dimension mismatch
        """
        if not self._initialized or self._index is None:
            raise RuntimeError(
                "VectorSearcher not initialized. Call initialize() first."
            )

        if len(memory_ids) != embeddings.shape[0]:
            raise ValueError(
                f"Number of IDs ({len(memory_ids)}) != "
                f"number of vectors ({embeddings.shape[0]})"
            )

        if embeddings.shape[1] != self.config.dimension:
            raise ValueError(
                f"Vector dimension ({embeddings.shape[1]}) != "
                f"expected ({self.config.dimension})"
            )

        # 分配内部 ID / Assign internal IDs
        internal_ids = []
        for memory_id in memory_ids:
            if memory_id in self._reverse_id_map:
                # 已存在，跳过 / Already exists, skip
                logger.warning(f"Memory {memory_id} already in index, skipping")
                continue

            internal_id = self._next_id
            self._next_id += 1

            self._id_map[internal_id] = memory_id
            self._reverse_id_map[memory_id] = internal_id
            internal_ids.append(internal_id)

        if not internal_ids:
            return 0

        # 过滤对应的向量 / Filter corresponding vectors
        valid_indices = [
            i for i, mid in enumerate(memory_ids) if mid in self._reverse_id_map
        ]
        valid_embeddings = embeddings[valid_indices]

        # 添加到 FAISS / Add to FAISS
        ids_array = np.array(internal_ids, dtype=np.int64)
        self._index.add_with_ids(valid_embeddings, ids_array)  # type: ignore[attr-defined]

        logger.debug(f"Added {len(internal_ids)} vectors to FAISS index")
        return len(internal_ids)

    def search(
        self,
        query_vector: "NDArray[np.float32]",
        top_k: Optional[int] = None,
        threshold: float = 0.0,
    ) -> List[Tuple[str, float]]:
        """
        向量相似度搜索
        Vector similarity search

        Args:
            query_vector: 查询向量 / Query vector
            top_k: 返回数量 / Return count
            threshold: 最小相似度阈值 / Minimum similarity threshold

        Returns:
            (memory_id, score) 列表，按相似度降序 / List sorted by similarity desc

        Raises:
            RuntimeError: 当未初始化时 / When not initialized
        """
        if not self._initialized or self._index is None:
            raise RuntimeError(
                "VectorSearcher not initialized. Call initialize() first."
            )

        k = top_k or self.config.top_k

        # 确保查询向量是 2D / Ensure query vector is 2D
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)

        # 检查维度 / Check dimension
        if query_vector.shape[1] != self.config.dimension:
            raise ValueError(
                f"Query dimension ({query_vector.shape[1]}) != "
                f"expected ({self.config.dimension})"
            )

        # 执行搜索 / Execute search
        # 如果索引为空，直接返回空结果
        if self._index.ntotal == 0:  # type: ignore[attr-defined]
            return []

        # 调整 k 不超过索引中的向量数
        actual_k = min(k, self._index.ntotal)  # type: ignore[attr-defined]

        distances, indices = self._index.search(query_vector, actual_k)  # type: ignore[attr-defined]

        # 转换结果 / Convert results
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx == -1:  # FAISS 返回 -1 表示无效
                continue

            if dist < threshold:
                continue

            memory_id = self._id_map.get(int(idx))
            if memory_id is None:
                logger.warning(f"Unknown internal ID: {idx}")
                continue

            results.append((memory_id, float(dist)))

        return results

    def remove_vectors(self, memory_ids: List[str]) -> int:
        """
        从索引删除向量
        Remove vectors from index

        注意: FAISS 的 IndexIDMap 不支持高效删除，
        这里通过重建索引实现（适用于小规模删除）。

        Args:
            memory_ids: 要删除的记忆 ID / Memory IDs to remove

        Returns:
            删除的向量数量 / Number of vectors removed
        """
        if not self._initialized or self._index is None:
            raise RuntimeError(
                "VectorSearcher not initialized. Call initialize() first."
            )

        # 获取要删除的内部 ID / Get internal IDs to remove
        internal_ids_to_remove = []
        for memory_id in memory_ids:
            internal_id = self._reverse_id_map.get(memory_id)
            if internal_id is not None:
                internal_ids_to_remove.append(internal_id)
                del self._reverse_id_map[memory_id]
                del self._id_map[internal_id]

        if not internal_ids_to_remove:
            return 0

        # FAISS IndexIDMap 支持 remove_ids
        ids_to_remove = np.array(internal_ids_to_remove, dtype=np.int64)
        removed = self._index.remove_ids(ids_to_remove)  # type: ignore[attr-defined]

        logger.debug(f"Removed {removed} vectors from FAISS index")
        return int(removed)

    def has_vector(self, memory_id: str) -> bool:
        """
        检查记忆是否已向量化
        Check if memory is vectorized

        Args:
            memory_id: 记忆 ID / Memory ID

        Returns:
            是否存在 / Whether exists
        """
        return memory_id in self._reverse_id_map

    def get_vector_count(self) -> int:
        """
        获取索引中的向量数量
        Get vector count in index

        Returns:
            向量数量 / Vector count
        """
        if not self._initialized or self._index is None:
            return 0
        return self._index.ntotal  # type: ignore[no-any-return, attr-defined]

    @property
    def is_initialized(self) -> bool:
        """
        检查是否已初始化
        Check if initialized

        Returns:
            是否已初始化 / Whether initialized
        """
        return self._initialized

    def close(self) -> None:
        """
        关闭并释放资源
        Close and release resources
        """
        self._index = None
        self._id_map.clear()
        self._reverse_id_map.clear()
        self._initialized = False
        logger.info("VectorSearcher closed")
