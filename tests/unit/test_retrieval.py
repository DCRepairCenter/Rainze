"""
记忆检索系统单元测试
Memory Retrieval System Unit Tests

测试 FAISS 向量检索、FTS5 全文检索和混合检索功能。
Tests for FAISS vector search, FTS5 full-text search, and hybrid retrieval.

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import pytest
from pathlib import Path

from rainze.memory import MemoryItem, MemoryType
from rainze.memory.retrieval import (
    EmbedderConfig,
    FTSConfig,
    FTSSearcher,
    HybridRetriever,
    HybridRetrieverConfig,
    RetrievalStrategy,
    TextEmbedder,
    VectorSearcher,
    VectorSearcherConfig,
)


# ============================================================================
# TextEmbedder Tests
# ============================================================================


class TestTextEmbedder:
    """文本嵌入器测试 / Text embedder tests"""

    @pytest.fixture
    def embedder_config(self) -> EmbedderConfig:
        """Embedding 配置 fixture"""
        return EmbedderConfig(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            device="cpu",
            normalize=True,
        )

    @pytest.mark.slow
    def test_embedder_initialize(self, embedder_config: EmbedderConfig) -> None:
        """测试 Embedder 初始化 / Test embedder initialization"""
        embedder = TextEmbedder(embedder_config)
        assert not embedder.is_initialized

        embedder.initialize()
        assert embedder.is_initialized
        assert embedder.dimension == 384  # MiniLM-L12 维度

        embedder.close()
        assert not embedder.is_initialized

    @pytest.mark.slow
    def test_embedder_embed_texts(self, embedder_config: EmbedderConfig) -> None:
        """测试文本向量化 / Test text embedding"""
        embedder = TextEmbedder(embedder_config)
        embedder.initialize()

        texts = ["主人喜欢吃苹果", "今天天气很好", "Hello World"]
        result = embedder.embed(texts)

        assert result.dimension == 384
        assert result.embeddings.shape == (3, 384)
        assert len(result.texts) == 3

        embedder.close()

    @pytest.mark.slow
    def test_embedder_embed_single(self, embedder_config: EmbedderConfig) -> None:
        """测试单文本向量化 / Test single text embedding"""
        embedder = TextEmbedder(embedder_config)
        embedder.initialize()

        vec = embedder.embed_single("测试文本")
        assert vec.shape == (384,)

        embedder.close()

    @pytest.mark.slow
    def test_embedder_embed_empty(self, embedder_config: EmbedderConfig) -> None:
        """测试空列表向量化 / Test empty list embedding"""
        embedder = TextEmbedder(embedder_config)
        embedder.initialize()

        result = embedder.embed([])
        assert result.embeddings.shape == (0, 384)

        embedder.close()

    def test_embedder_not_initialized_error(self) -> None:
        """测试未初始化时抛出异常 / Test error when not initialized"""
        embedder = TextEmbedder()

        with pytest.raises(RuntimeError, match="not initialized"):
            embedder.embed(["test"])

        with pytest.raises(RuntimeError, match="not initialized"):
            _ = embedder.dimension


# ============================================================================
# VectorSearcher Tests
# ============================================================================


class TestVectorSearcher:
    """FAISS 向量检索器测试 / FAISS vector searcher tests"""

    @pytest.fixture
    def vector_config(self, tmp_path: Path) -> VectorSearcherConfig:
        """向量检索配置 fixture"""
        return VectorSearcherConfig(
            index_path=tmp_path / "test.index",
            dimension=384,
            index_type="flat",
        )

    @pytest.fixture
    def embedder(self) -> TextEmbedder:
        """预初始化的 Embedder fixture"""
        config = EmbedderConfig(device="cpu")
        embedder = TextEmbedder(config)
        embedder.initialize()
        yield embedder
        embedder.close()

    @pytest.mark.slow
    def test_vector_searcher_initialize(
        self, vector_config: VectorSearcherConfig
    ) -> None:
        """测试向量检索器初始化 / Test vector searcher initialization"""
        searcher = VectorSearcher(vector_config)
        assert not searcher.is_initialized

        searcher.initialize(load_existing=False)
        assert searcher.is_initialized
        assert searcher.get_vector_count() == 0

        searcher.close()
        assert not searcher.is_initialized

    @pytest.mark.slow
    def test_vector_searcher_add_and_search(
        self,
        vector_config: VectorSearcherConfig,
        embedder: TextEmbedder,
    ) -> None:
        """测试添加向量和搜索 / Test add vectors and search"""
        searcher = VectorSearcher(vector_config)
        searcher.initialize(load_existing=False)

        # 添加向量
        texts = ["主人喜欢吃苹果", "今天天气很好", "主人说工作压力大"]
        embeddings = embedder.embed(texts).embeddings
        memory_ids = ["mem_001", "mem_002", "mem_003"]

        added = searcher.add_vectors(memory_ids, embeddings)
        assert added == 3
        assert searcher.get_vector_count() == 3

        # 搜索
        query_vec = embedder.embed_single("苹果水果")
        results = searcher.search(query_vec, top_k=3)

        assert len(results) == 3
        # 第一个结果应该是关于苹果的记忆
        assert results[0][0] == "mem_001"
        assert results[0][1] > 0  # 相似度分数 > 0

        searcher.close()

    @pytest.mark.slow
    def test_vector_searcher_remove(
        self,
        vector_config: VectorSearcherConfig,
        embedder: TextEmbedder,
    ) -> None:
        """测试删除向量 / Test remove vectors"""
        searcher = VectorSearcher(vector_config)
        searcher.initialize(load_existing=False)

        texts = ["文本1", "文本2", "文本3"]
        embeddings = embedder.embed(texts).embeddings
        memory_ids = ["mem_001", "mem_002", "mem_003"]

        searcher.add_vectors(memory_ids, embeddings)
        assert searcher.get_vector_count() == 3

        removed = searcher.remove_vectors(["mem_002"])
        assert removed == 1
        assert searcher.get_vector_count() == 2
        assert not searcher.has_vector("mem_002")
        assert searcher.has_vector("mem_001")

        searcher.close()

    @pytest.mark.slow
    def test_vector_searcher_save_load(
        self,
        vector_config: VectorSearcherConfig,
        embedder: TextEmbedder,
    ) -> None:
        """测试保存和加载索引 / Test save and load index"""
        # 创建并保存
        searcher = VectorSearcher(vector_config)
        searcher.initialize(load_existing=False)

        texts = ["测试文本1", "测试文本2"]
        embeddings = embedder.embed(texts).embeddings
        searcher.add_vectors(["mem_001", "mem_002"], embeddings)
        searcher.save()
        searcher.close()

        # 重新加载
        searcher2 = VectorSearcher(vector_config)
        searcher2.initialize(load_existing=True)

        assert searcher2.get_vector_count() == 2
        assert searcher2.has_vector("mem_001")

        searcher2.close()


# ============================================================================
# FTSSearcher Tests
# ============================================================================


class TestFTSSearcher:
    """FTS5 全文检索器测试 / FTS5 full-text searcher tests"""

    @pytest.fixture
    def fts_config(self, tmp_path: Path) -> FTSConfig:
        """FTS 配置 fixture"""
        return FTSConfig(
            db_path=tmp_path / "test_memory.db",
            top_k=10,
        )

    @pytest.fixture
    def sample_memories(self) -> list[MemoryItem]:
        """示例记忆 fixture"""
        return [
            MemoryItem(
                id="mem_001",
                content="主人喜欢吃苹果和香蕉",
                memory_type=MemoryType.FACT,
                importance=0.8,
            ),
            MemoryItem(
                id="mem_002",
                content="今天天气很好，适合出门散步",
                memory_type=MemoryType.EPISODE,
                importance=0.5,
            ),
            MemoryItem(
                id="mem_003",
                content="主人说工作压力很大，需要休息",
                memory_type=MemoryType.EPISODE,
                importance=0.7,
            ),
        ]

    async def test_fts_initialize(self, fts_config: FTSConfig) -> None:
        """测试 FTS 初始化 / Test FTS initialization"""
        fts = FTSSearcher(fts_config)
        assert not fts.is_initialized

        await fts.initialize()
        assert fts.is_initialized

        await fts.close()
        assert not fts.is_initialized

    async def test_fts_insert_and_search(
        self,
        fts_config: FTSConfig,
        sample_memories: list[MemoryItem],
    ) -> None:
        """测试插入和搜索 / Test insert and search"""
        fts = FTSSearcher(fts_config)
        await fts.initialize()

        # 插入记忆
        for mem in sample_memories:
            await fts.insert_memory(mem)

        count = await fts.get_memory_count()
        assert count == 3

        # 搜索
        results = await fts.search("苹果", top_k=3)
        assert len(results) >= 1
        assert results[0][0] == "mem_001"  # 应该匹配关于苹果的记忆

        await fts.close()

    async def test_fts_search_with_filters(
        self,
        fts_config: FTSConfig,
        sample_memories: list[MemoryItem],
    ) -> None:
        """测试带过滤条件的搜索 / Test search with filters"""
        fts = FTSSearcher(fts_config)
        await fts.initialize()

        for mem in sample_memories:
            await fts.insert_memory(mem)

        # 按类型过滤
        results = await fts.search(
            "主人",
            memory_types=["fact"],
        )
        assert len(results) >= 1
        # 只应返回 FACT 类型的记忆
        for mem_id, _ in results:
            data = await fts.get_memory_by_id(mem_id)
            assert data["memory_type"] == "fact"

        await fts.close()

    async def test_fts_update_memory(
        self,
        fts_config: FTSConfig,
        sample_memories: list[MemoryItem],
    ) -> None:
        """测试更新记忆 / Test update memory"""
        fts = FTSSearcher(fts_config)
        await fts.initialize()

        await fts.insert_memory(sample_memories[0])

        # 更新重要度
        updated = await fts.update_memory("mem_001", {"importance": 0.95})
        assert updated

        data = await fts.get_memory_by_id("mem_001")
        assert data["importance"] == 0.95

        await fts.close()

    async def test_fts_delete_memory(
        self,
        fts_config: FTSConfig,
        sample_memories: list[MemoryItem],
    ) -> None:
        """测试删除记忆 / Test delete memory"""
        fts = FTSSearcher(fts_config)
        await fts.initialize()

        await fts.insert_memory(sample_memories[0])
        count = await fts.get_memory_count()
        assert count == 1

        deleted = await fts.delete_memory("mem_001")
        assert deleted

        count = await fts.get_memory_count()
        assert count == 0

        await fts.close()


# ============================================================================
# HybridRetriever Tests
# ============================================================================


class TestHybridRetriever:
    """混合检索器测试 / Hybrid retriever tests"""

    @pytest.fixture
    def hybrid_config(self, tmp_path: Path) -> HybridRetrieverConfig:
        """混合检索配置 fixture"""
        config = HybridRetrieverConfig()
        config.fts_config.db_path = tmp_path / "hybrid_memory.db"
        config.vector_config.index_path = tmp_path / "hybrid.index"
        config.vector_config.dimension = 384
        config.top_k = 5
        return config

    @pytest.fixture
    def sample_memories(self) -> list[MemoryItem]:
        """示例记忆 fixture"""
        return [
            MemoryItem(
                id="h_001",
                content="主人最喜欢的水果是苹果，每天都要吃一个",
                memory_type=MemoryType.FACT,
                importance=0.9,
            ),
            MemoryItem(
                id="h_002",
                content="主人今天加班到很晚才回家",
                memory_type=MemoryType.EPISODE,
                importance=0.6,
            ),
            MemoryItem(
                id="h_003",
                content="主人说周末想去爬山锻炼身体",
                memory_type=MemoryType.EPISODE,
                importance=0.7,
            ),
            MemoryItem(
                id="h_004",
                content="主人不喜欢吃香蕉",
                memory_type=MemoryType.FACT,
                importance=0.5,
            ),
        ]

    @pytest.mark.slow
    async def test_hybrid_initialize(
        self, hybrid_config: HybridRetrieverConfig
    ) -> None:
        """测试混合检索器初始化 / Test hybrid retriever initialization"""
        retriever = HybridRetriever(hybrid_config)
        assert not retriever.is_initialized

        await retriever.initialize()
        assert retriever.is_initialized

        await retriever.close()
        assert not retriever.is_initialized

    @pytest.mark.slow
    async def test_hybrid_add_and_retrieve(
        self,
        hybrid_config: HybridRetrieverConfig,
        sample_memories: list[MemoryItem],
    ) -> None:
        """测试添加记忆和混合检索 / Test add memories and hybrid retrieval"""
        retriever = HybridRetriever(hybrid_config)
        await retriever.initialize()

        # 添加记忆
        for mem in sample_memories:
            await retriever.add_memory(mem)

        stats = await retriever.get_stats()
        assert stats["fts_memory_count"] == 4
        assert stats["vector_count"] == 4

        # 混合检索
        result = await retriever.retrieve("主人喜欢什么水果", top_k=3)

        assert result.has_results
        assert result.strategy_used == "hybrid"
        assert result.retrieval_time_ms > 0
        assert len(result.memories) <= 3

        # 第一个结果应该是关于苹果的记忆
        top_memory = result.top_memory
        assert top_memory is not None
        assert "苹果" in top_memory.memory.content

        await retriever.close()

    @pytest.mark.slow
    async def test_hybrid_retrieval_strategies(
        self,
        hybrid_config: HybridRetrieverConfig,
        sample_memories: list[MemoryItem],
    ) -> None:
        """测试不同检索策略 / Test different retrieval strategies"""
        retriever = HybridRetriever(hybrid_config)
        await retriever.initialize()

        for mem in sample_memories:
            await retriever.add_memory(mem)

        # FTS Only
        result_fts = await retriever.retrieve(
            "苹果", strategy=RetrievalStrategy.FTS_ONLY
        )
        assert result_fts.strategy_used == "fts_only"

        # Vector Only
        result_vec = await retriever.retrieve(
            "主人喜欢吃的东西", strategy=RetrievalStrategy.VECTOR_ONLY
        )
        assert result_vec.strategy_used == "vector_only"

        # Adaptive
        result_adaptive = await retriever.retrieve(
            "苹果", strategy=RetrievalStrategy.ADAPTIVE
        )
        # 短查询应该选择 FTS
        assert result_adaptive.strategy_used == "fts_only"

        await retriever.close()

    @pytest.mark.slow
    async def test_hybrid_remove_memory(
        self,
        hybrid_config: HybridRetrieverConfig,
        sample_memories: list[MemoryItem],
    ) -> None:
        """测试删除记忆 / Test remove memory"""
        retriever = HybridRetriever(hybrid_config)
        await retriever.initialize()

        await retriever.add_memory(sample_memories[0])

        stats_before = await retriever.get_stats()
        assert stats_before["fts_memory_count"] == 1

        removed = await retriever.remove_memory("h_001")
        assert removed

        stats_after = await retriever.get_stats()
        assert stats_after["fts_memory_count"] == 0

        await retriever.close()

    @pytest.mark.slow
    async def test_hybrid_empty_result(
        self, hybrid_config: HybridRetrieverConfig
    ) -> None:
        """测试空结果 / Test empty result"""
        retriever = HybridRetriever(hybrid_config)
        await retriever.initialize()

        # 没有添加任何记忆，检索应返回空
        result = await retriever.retrieve("任何查询")

        assert not result.has_results
        assert result.no_relevant_memory or len(result.memories) == 0

        await retriever.close()
