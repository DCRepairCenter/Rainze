"""
文本嵌入服务
Text Embedding Service

本模块提供文本向量化功能，支持多种 Embedding 模型。
This module provides text vectorization using various embedding models.

Reference:
    - MOD-Memory.md §3.3: HybridRetriever - 向量检索
    - PRD §0.4: 混合存储系统

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional, Sequence

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

# 延迟导入 sentence-transformers / Lazy import sentence-transformers
_sentence_transformer_model = None

logger = logging.getLogger(__name__)


@dataclass
class EmbedderConfig:
    """
    Embedding 配置
    Embedding configuration

    Attributes:
        model_name: 模型名称 / Model name
        device: 设备 (cpu/cuda) / Device
        normalize: 是否归一化 / Whether to normalize
        batch_size: 批量大小 / Batch size
        cache_dir: 模型缓存目录 / Model cache directory
    """

    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    device: str = "cpu"
    normalize: bool = True
    batch_size: int = 32
    cache_dir: Optional[str] = None


@dataclass
class EmbeddingResult:
    """
    Embedding 结果
    Embedding result

    Attributes:
        embeddings: 向量数组 / Embedding vectors
        dimension: 向量维度 / Vector dimension
        texts: 原始文本 / Original texts
    """

    embeddings: "NDArray[np.float32]"
    dimension: int
    texts: List[str] = field(default_factory=list)


class TextEmbedder:
    """
    文本嵌入服务
    Text embedding service

    使用 SentenceTransformer 将文本转换为向量。
    Converts text to vectors using SentenceTransformer.

    Attributes:
        config: 配置 / Configuration
        _model: SentenceTransformer 模型 / Model instance
        _dimension: 向量维度 / Vector dimension

    Example:
        >>> embedder = TextEmbedder()
        >>> embedder.initialize()
        >>> result = embedder.embed(["你好世界", "Hello World"])
        >>> print(result.dimension)
        384
    """

    def __init__(self, config: Optional[EmbedderConfig] = None) -> None:
        """
        初始化 Embedder
        Initialize Embedder

        Args:
            config: 配置，None 则使用默认配置 / Config, None for default
        """
        self.config = config or EmbedderConfig()
        self._model: Optional[object] = None
        self._dimension: int = 0
        self._initialized: bool = False

    def initialize(self) -> None:
        """
        初始化模型（懒加载）
        Initialize model (lazy loading)

        首次调用时加载模型到内存。
        Loads model into memory on first call.

        Raises:
            RuntimeError: 当 sentence-transformers 未安装时
        """
        if self._initialized:
            return

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise RuntimeError(
                "sentence-transformers is required for TextEmbedder. "
                "Install it with: pip install sentence-transformers"
            ) from e

        logger.info(f"Loading embedding model: {self.config.model_name}")

        self._model = SentenceTransformer(
            self.config.model_name,
            device=self.config.device,
            cache_folder=self.config.cache_dir,
        )

        # 获取向量维度 / Get embedding dimension
        test_embedding = self._model.encode(["test"], convert_to_numpy=True)
        self._dimension = test_embedding.shape[1]

        self._initialized = True
        logger.info(
            f"Embedding model loaded. Dimension: {self._dimension}, "
            f"Device: {self.config.device}"
        )

    def embed(
        self,
        texts: Sequence[str],
        batch_size: Optional[int] = None,
    ) -> EmbeddingResult:
        """
        将文本转换为向量
        Convert texts to vectors

        Args:
            texts: 文本列表 / List of texts
            batch_size: 批量大小，None 使用配置值 / Batch size, None for config

        Returns:
            EmbeddingResult 包含向量和元数据 / Result with vectors and metadata

        Raises:
            RuntimeError: 当未初始化时 / When not initialized
        """
        if not self._initialized or self._model is None:
            raise RuntimeError("TextEmbedder not initialized. Call initialize() first.")

        if not texts:
            return EmbeddingResult(
                embeddings=np.array([], dtype=np.float32).reshape(0, self._dimension),
                dimension=self._dimension,
                texts=[],
            )

        bs = batch_size or self.config.batch_size

        # 编码文本 / Encode texts
        embeddings: NDArray[np.float32] = self._model.encode(  # type: ignore[attr-defined]
            list(texts),
            batch_size=bs,
            convert_to_numpy=True,
            normalize_embeddings=self.config.normalize,
            show_progress_bar=len(texts) > 100,
        )

        return EmbeddingResult(
            embeddings=embeddings.astype(np.float32),
            dimension=self._dimension,
            texts=list(texts),
        )

    def embed_single(self, text: str) -> "NDArray[np.float32]":
        """
        单文本向量化（便捷方法）
        Single text embedding (convenience method)

        Args:
            text: 文本 / Text

        Returns:
            向量数组 / Embedding vector
        """
        result = self.embed([text])
        embedding: NDArray[np.float32] = result.embeddings[0]
        return embedding

    @property
    def dimension(self) -> int:
        """
        获取向量维度
        Get embedding dimension

        Returns:
            向量维度 / Vector dimension

        Raises:
            RuntimeError: 当未初始化时 / When not initialized
        """
        if not self._initialized:
            raise RuntimeError("TextEmbedder not initialized. Call initialize() first.")
        return self._dimension

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
        释放模型资源
        Release model resources
        """
        self._model = None
        self._initialized = False
        self._dimension = 0
        logger.info("TextEmbedder closed")
