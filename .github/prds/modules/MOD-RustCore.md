# MOD-RustCore - Rust性能模块 子PRD

> **模块版本**: v1.0.0
> **创建日期**: 2025-12-29
> **关联PRD**: PRD-Rainze.md v3.0.3 §0.0
> **关联技术栈**: TECH-Rainze.md §3.2

---

## 1. 模块概述

### 1.1 模块定位

RustCore模块是Rainze项目的**性能关键路径层**，使用Rust语言实现，通过PyO3/Maturin提供Python绑定。负责处理计算密集型任务，包括：

- 向量相似度搜索（FAISS封装）
- 批量向量化处理
- 系统状态监控（CPU/内存/进程）
- 用户活动检测（全屏/会议应用识别）
- 文本处理与分词

### 1.2 设计原则

1. **零拷贝传输**: 利用PyO3的零拷贝能力，减少Python-Rust边界开销
2. **异步优先**: 使用tokio运行时处理I/O密集任务
3. **并行计算**: 使用rayon进行数据并行处理
4. **内存安全**: 严格遵循Rust所有权模型，无unsafe代码泄露
5. **错误透明**: Rust错误转换为Python异常，保持调试友好

### 1.3 性能目标

| 操作 | 目标延迟 | 说明 |
|------|----------|------|
| 向量搜索 (10k条) | <50ms | FAISS IndexFlatIP |
| 批量向量化 (32条) | <200ms | 不含API调用 |
| 系统状态查询 | <10ms | CPU/内存/进程 |
| 全屏检测 | <5ms | Windows API |
| 中文分词 | <20ms | 单条文本 |

---

## 2. 目录结构

```
rainze_core/                      # Rust crate根目录
├── Cargo.toml                    # Rust包配置
├── src/
│   ├── lib.rs                    # PyO3模块入口
│   ├── memory_search/            # 记忆检索子模块
│   │   ├── mod.rs
│   │   ├── faiss_wrapper.rs      # FAISS封装
│   │   ├── reranker.rs           # 重排序算法
│   │   └── cache.rs              # 检索缓存
│   ├── vectorize/                # 向量化子模块
│   │   ├── mod.rs
│   │   ├── batch_processor.rs    # 批处理器
│   │   └── queue.rs              # 优先级队列
│   ├── system_monitor/           # 系统监控子模块
│   │   ├── mod.rs
│   │   ├── cpu.rs                # CPU监控
│   │   ├── memory.rs             # 内存监控
│   │   ├── process.rs            # 进程监控
│   │   └── activity.rs           # 用户活动检测
│   ├── text_process/             # 文本处理子模块
│   │   ├── mod.rs
│   │   ├── tokenizer.rs          # 中文分词
│   │   └── entity.rs             # 实体词检测
│   └── utils/                    # 工具模块
│       ├── mod.rs
│       ├── error.rs              # 错误类型
│       └── config.rs             # 配置读取
└── tests/                        # 测试目录
    ├── test_memory_search.rs
    ├── test_system_monitor.rs
    └── test_text_process.rs
```

---

## 3. 类/结构体设计

### 3.1 模块入口 (lib.rs)

```rust
//! Rainze Core - Rust性能模块
//! 
//! 提供以下功能的Python绑定:
//! - 记忆检索 (FAISS + 重排序)
//! - 系统监控 (CPU/内存/进程)
//! - 文本处理 (分词/实体识别)
//! - 批量向量化队列管理

use pyo3::prelude::*;

/// PyO3模块注册
#[pymodule]
fn rainze_core(m: &Bound<'_, PyModule>) -> PyResult<()>;
```

### 3.2 记忆检索模块 (memory_search/)

#### 3.2.1 FAISSWrapper

```rust
/// FAISS索引封装器
/// 
/// 支持IndexFlatIP和IndexIVFFlat两种索引类型
/// 根据数据量自动选择最优索引
#[pyclass]
pub struct FAISSWrapper {
    /// 内部索引实例
    index: FAISSIndex,
    /// 向量维度
    dimension: usize,
    /// 当前向量数量
    count: usize,
    /// 索引类型
    index_type: IndexType,
}

#[pymethods]
impl FAISSWrapper {
    /// 创建新索引
    /// 
    /// # Arguments
    /// * `dimension` - 向量维度 (默认768)
    /// * `index_type` - 索引类型 ("flat" | "ivf")
    /// 
    /// # Returns
    /// FAISSWrapper实例
    #[new]
    #[pyo3(signature = (dimension=768, index_type="flat"))]
    pub fn new(dimension: usize, index_type: &str) -> PyResult<Self>;

    /// 添加向量到索引
    /// 
    /// # Arguments
    /// * `ids` - 向量ID列表
    /// * `vectors` - 向量数据 (numpy array, shape: [n, dimension])
    /// 
    /// # Errors
    /// - 维度不匹配
    /// - ID重复
    pub fn add(&mut self, ids: Vec<String>, vectors: PyReadonlyArrayDyn<f32>) -> PyResult<()>;

    /// 搜索最相似向量
    /// 
    /// # Arguments
    /// * `query` - 查询向量 (numpy array, shape: [dimension])
    /// * `top_k` - 返回数量
    /// 
    /// # Returns
    /// Vec<(id, similarity_score)>
    pub fn search(&self, query: PyReadonlyArrayDyn<f32>, top_k: usize) -> PyResult<Vec<(String, f32)>>;

    /// 删除向量
    pub fn remove(&mut self, ids: Vec<String>) -> PyResult<usize>;

    /// 保存索引到文件
    pub fn save(&self, path: &str) -> PyResult<()>;

    /// 从文件加载索引
    #[staticmethod]
    pub fn load(path: &str) -> PyResult<Self>;

    /// 获取索引统计信息
    pub fn stats(&self) -> PyResult<IndexStats>;
}

/// 索引类型枚举
pub enum IndexType {
    /// 精确搜索，适用于<10k条
    Flat,
    /// 近似搜索，适用于>=10k条
    IVF { nlist: usize, nprobe: usize },
}

/// 索引统计信息
#[pyclass]
pub struct IndexStats {
    #[pyo3(get)]
    pub dimension: usize,
    #[pyo3(get)]
    pub count: usize,
    #[pyo3(get)]
    pub index_type: String,
    #[pyo3(get)]
    pub memory_bytes: usize,
}
```

#### 3.2.2 Reranker

```rust
/// 重排序器
/// 
/// 对初步检索结果进行多因素重排序
#[pyclass]
pub struct Reranker {
    /// 权重配置
    weights: RerankerWeights,
    /// 时间衰减参数
    recency_decay_days: f32,
}

/// 重排序权重配置
#[derive(Clone)]
#[pyclass]
pub struct RerankerWeights {
    #[pyo3(get, set)]
    pub similarity: f32,      // 相似度权重 (默认0.4)
    #[pyo3(get, set)]
    pub recency: f32,         // 时间权重 (默认0.3)
    #[pyo3(get, set)]
    pub importance: f32,      // 重要度权重 (默认0.2)
    #[pyo3(get, set)]
    pub frequency: f32,       // 访问频率权重 (默认0.1)
}

/// 记忆条目元数据
#[pyclass]
pub struct MemoryMeta {
    #[pyo3(get)]
    pub id: String,
    #[pyo3(get)]
    pub created_at: i64,      // Unix timestamp
    #[pyo3(get)]
    pub importance: f32,
    #[pyo3(get)]
    pub access_count: u32,
    #[pyo3(get)]
    pub similarity: f32,      // 初始相似度
}

#[pymethods]
impl Reranker {
    /// 创建重排序器
    #[new]
    #[pyo3(signature = (weights=None, recency_decay_days=7.0))]
    pub fn new(weights: Option<RerankerWeights>, recency_decay_days: f32) -> Self;

    /// 执行重排序
    /// 
    /// # Arguments
    /// * `candidates` - 候选记忆列表
    /// * `current_time` - 当前Unix时间戳
    /// * `top_k` - 返回数量
    /// 
    /// # Returns
    /// 重排序后的(id, final_score)列表
    pub fn rerank(
        &self, 
        candidates: Vec<MemoryMeta>, 
        current_time: i64, 
        top_k: usize
    ) -> Vec<(String, f32)>;

    /// 更新权重配置
    pub fn set_weights(&mut self, weights: RerankerWeights);
}
```

#### 3.2.3 SearchCache

```rust
/// 检索缓存
/// 
/// LRU缓存策略，支持TTL过期
#[pyclass]
pub struct SearchCache {
    /// LRU缓存
    cache: LruCache<String, CachedResult>,
    /// 最大条目数
    max_entries: usize,
    /// TTL秒数
    ttl_seconds: u64,
}

/// 缓存条目
struct CachedResult {
    results: Vec<(String, f32)>,
    created_at: Instant,
}

#[pymethods]
impl SearchCache {
    #[new]
    #[pyo3(signature = (max_entries=100, ttl_seconds=300))]
    pub fn new(max_entries: usize, ttl_seconds: u64) -> Self;

    /// 获取缓存
    /// 
    /// # Arguments
    /// * `cache_key` - 缓存键 (通常是query的hash)
    pub fn get(&mut self, cache_key: &str) -> Option<Vec<(String, f32)>>;

    /// 设置缓存
    pub fn set(&mut self, cache_key: &str, results: Vec<(String, f32)>);

    /// 清空缓存
    pub fn clear(&mut self);

    /// 获取缓存统计
    pub fn stats(&self) -> CacheStats;
}

#[pyclass]
pub struct CacheStats {
    #[pyo3(get)]
    pub size: usize,
    #[pyo3(get)]
    pub hit_count: u64,
    #[pyo3(get)]
    pub miss_count: u64,
    #[pyo3(get)]
    pub hit_rate: f32,
}
```

### 3.3 向量化模块 (vectorize/)

#### 3.3.1 VectorizeQueue

```rust
/// 向量化优先级队列
/// 
/// 管理待向量化的记忆条目，支持优先级排序
#[pyclass]
pub struct VectorizeQueue {
    /// 高优先级队列 (importance >= 0.7)
    high_priority: VecDeque<QueueItem>,
    /// 普通优先级队列
    normal_priority: VecDeque<QueueItem>,
    /// 高优先级阈值
    high_threshold: f32,
}

/// 队列条目
#[pyclass]
pub struct QueueItem {
    #[pyo3(get)]
    pub memory_id: String,
    #[pyo3(get)]
    pub content: String,
    #[pyo3(get)]
    pub importance: f32,
    #[pyo3(get)]
    pub retry_count: u32,
    #[pyo3(get)]
    pub created_at: i64,
}

#[pymethods]
impl VectorizeQueue {
    #[new]
    #[pyo3(signature = (high_threshold=0.7))]
    pub fn new(high_threshold: f32) -> Self;

    /// 添加到队列
    /// 
    /// 根据importance自动分配到高/普通优先级队列
    pub fn push(&mut self, item: QueueItem);

    /// 批量获取待处理项
    /// 
    /// # Arguments
    /// * `batch_size` - 批次大小
    /// 
    /// # Returns
    /// 优先返回高优先级队列
    pub fn pop_batch(&mut self, batch_size: usize) -> Vec<QueueItem>;

    /// 将失败项重新入队
    pub fn retry(&mut self, item: QueueItem) -> bool;

    /// 队列长度
    pub fn len(&self) -> usize;

    /// 是否为空
    pub fn is_empty(&self) -> bool;

    /// 保存队列到文件 (程序关闭时)
    pub fn save(&self, path: &str) -> PyResult<()>;

    /// 从文件加载队列 (程序启动时)
    #[staticmethod]
    pub fn load(path: &str) -> PyResult<Self>;
}
```

#### 3.3.2 BatchProcessor

```rust
/// 批处理器
/// 
/// 并行处理向量化任务
#[pyclass]
pub struct BatchProcessor {
    /// 最大并发数
    max_concurrency: usize,
    /// 单条超时(毫秒)
    timeout_ms: u64,
}

#[pymethods]
impl BatchProcessor {
    #[new]
    #[pyo3(signature = (max_concurrency=4, timeout_ms=5000))]
    pub fn new(max_concurrency: usize, timeout_ms: u64) -> Self;

    /// 批量处理文本预处理
    /// 
    /// 在发送到Embedding API前进行预处理:
    /// - 文本清洗
    /// - 长度截断
    /// - Token估算
    /// 
    /// # Arguments
    /// * `texts` - 待处理文本列表
    /// * `max_tokens` - 最大token数
    /// 
    /// # Returns
    /// 预处理后的文本列表
    pub fn preprocess_batch(&self, texts: Vec<String>, max_tokens: usize) -> Vec<String>;

    /// 估算token数量
    pub fn estimate_tokens(&self, text: &str) -> usize;
}
```

### 3.4 系统监控模块 (system_monitor/)

#### 3.4.1 SystemMonitor

```rust
/// 系统监控器
/// 
/// 监控CPU、内存、进程状态
#[pyclass]
pub struct SystemMonitor {
    /// 系统信息句柄
    sys: System,
    /// 刷新间隔(秒)
    refresh_interval: u64,
    /// 上次刷新时间
    last_refresh: Instant,
}

/// 系统状态快照
#[pyclass]
pub struct SystemStatus {
    #[pyo3(get)]
    pub cpu_usage: f32,           // CPU使用率 (0-100)
    #[pyo3(get)]
    pub memory_usage: f32,        // 内存使用率 (0-100)
    #[pyo3(get)]
    pub memory_used_mb: u64,      // 已用内存(MB)
    #[pyo3(get)]
    pub memory_total_mb: u64,     // 总内存(MB)
    #[pyo3(get)]
    pub timestamp: i64,           // 采集时间
}

#[pymethods]
impl SystemMonitor {
    #[new]
    #[pyo3(signature = (refresh_interval=5))]
    pub fn new(refresh_interval: u64) -> Self;

    /// 获取系统状态
    /// 
    /// 如果距上次刷新超过refresh_interval，自动刷新
    pub fn get_status(&mut self) -> SystemStatus;

    /// 强制刷新
    pub fn refresh(&mut self);

    /// 检查CPU是否过载
    pub fn is_cpu_overloaded(&mut self, threshold: f32) -> bool;

    /// 检查内存是否紧张
    pub fn is_memory_low(&mut self, threshold: f32) -> bool;
}
```

#### 3.4.2 ProcessMonitor

```rust
/// 进程监控器
/// 
/// 监控特定进程的运行状态
#[pyclass]
pub struct ProcessMonitor {
    /// 监控的进程名列表
    watched_processes: HashSet<String>,
    /// 系统句柄
    sys: System,
}

/// 进程信息
#[pyclass]
pub struct ProcessInfo {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub pid: u32,
    #[pyo3(get)]
    pub cpu_usage: f32,
    #[pyo3(get)]
    pub memory_mb: u64,
    #[pyo3(get)]
    pub is_running: bool,
}

#[pymethods]
impl ProcessMonitor {
    #[new]
    pub fn new() -> Self;

    /// 添加监控进程
    pub fn watch(&mut self, process_name: &str);

    /// 移除监控进程
    pub fn unwatch(&mut self, process_name: &str);

    /// 检查进程是否运行
    pub fn is_running(&mut self, process_name: &str) -> bool;

    /// 获取进程信息
    pub fn get_info(&mut self, process_name: &str) -> Option<ProcessInfo>;

    /// 获取所有监控进程的状态
    pub fn get_all_watched(&mut self) -> Vec<ProcessInfo>;

    /// 检测游戏进程
    /// 
    /// 传入游戏进程白名单，返回正在运行的游戏
    pub fn detect_games(&mut self, game_list: Vec<String>) -> Vec<String>;

    /// 检测会议应用
    pub fn detect_meeting_apps(&mut self, app_list: Vec<String>) -> Vec<String>;
}
```

#### 3.4.3 ActivityDetector

```rust
/// 用户活动检测器
/// 
/// 检测全屏状态、会议模式等
#[pyclass]
pub struct ActivityDetector {
    /// 缓存的全屏状态
    cached_fullscreen: Option<bool>,
    /// 缓存时间
    cache_time: Instant,
    /// 缓存有效期(毫秒)
    cache_ttl_ms: u64,
}

/// 活动状态
#[pyclass]
pub struct ActivityStatus {
    #[pyo3(get)]
    pub is_fullscreen: bool,           // 是否全屏
    #[pyo3(get)]
    pub fullscreen_app: Option<String>, // 全屏应用名
    #[pyo3(get)]
    pub is_in_meeting: bool,           // 是否在会议中
    #[pyo3(get)]
    pub meeting_app: Option<String>,   // 会议应用名
    #[pyo3(get)]
    pub active_window_title: String,   // 当前活动窗口标题
    #[pyo3(get)]
    pub idle_seconds: u64,             // 空闲秒数
}

#[pymethods]
impl ActivityDetector {
    #[new]
    #[pyo3(signature = (cache_ttl_ms=1000))]
    pub fn new(cache_ttl_ms: u64) -> Self;

    /// 获取完整活动状态
    pub fn get_status(&mut self, meeting_apps: Vec<String>) -> ActivityStatus;

    /// 检测是否全屏
    /// 
    /// Windows: 使用 GetForegroundWindow + IsZoomed
    pub fn is_fullscreen(&mut self) -> bool;

    /// 获取当前活动窗口标题
    pub fn get_active_window_title(&self) -> String;

    /// 获取用户空闲时间
    /// 
    /// Windows: 使用 GetLastInputInfo
    pub fn get_idle_time(&self) -> u64;
}
```

### 3.5 文本处理模块 (text_process/)

#### 3.5.1 ChineseTokenizer

```rust
/// 中文分词器
/// 
/// 基于jieba-rs实现，支持自定义词典
#[pyclass]
pub struct ChineseTokenizer {
    /// jieba分词器
    jieba: Jieba,
    /// 是否启用HMM
    use_hmm: bool,
}

#[pymethods]
impl ChineseTokenizer {
    #[new]
    #[pyo3(signature = (use_hmm=true))]
    pub fn new(use_hmm: bool) -> Self;

    /// 分词
    /// 
    /// # Arguments
    /// * `text` - 待分词文本
    /// * `cut_all` - 是否全模式
    /// 
    /// # Returns
    /// 分词结果列表
    pub fn cut(&self, text: &str, cut_all: bool) -> Vec<String>;

    /// 搜索引擎模式分词
    pub fn cut_for_search(&self, text: &str) -> Vec<String>;

    /// 添加自定义词
    pub fn add_word(&mut self, word: &str, freq: Option<usize>, tag: Option<&str>);

    /// 加载自定义词典
    pub fn load_userdict(&mut self, path: &str) -> PyResult<()>;

    /// 词性标注
    pub fn tag(&self, text: &str) -> Vec<(String, String)>;
}
```

#### 3.5.2 EntityDetector

```rust
/// 实体词检测器
/// 
/// 检测文本中的实体词，用于记忆检索策略选择
#[pyclass]
pub struct EntityDetector {
    /// 分词器
    tokenizer: ChineseTokenizer,
    /// 实体词性标签
    entity_pos_tags: HashSet<String>,
    /// 最小实体长度
    min_entity_length: usize,
}

/// 实体检测结果
#[pyclass]
pub struct EntityResult {
    #[pyo3(get)]
    pub has_entities: bool,
    #[pyo3(get)]
    pub entities: Vec<String>,
    #[pyo3(get)]
    pub entity_count: usize,
}

#[pymethods]
impl EntityDetector {
    /// 创建实体检测器
    /// 
    /// # Arguments
    /// * `entity_pos_tags` - 实体词性标签列表 (默认: n, nr, ns, nt, nz, vn)
    /// * `min_entity_length` - 最小实体长度 (默认: 2)
    #[new]
    #[pyo3(signature = (entity_pos_tags=None, min_entity_length=2))]
    pub fn new(entity_pos_tags: Option<Vec<String>>, min_entity_length: usize) -> Self;

    /// 检测实体
    pub fn detect(&self, text: &str) -> EntityResult;

    /// 检测时间指代词
    /// 
    /// 返回匹配的时间窗口
    pub fn detect_time_reference(&self, text: &str) -> Option<TimeWindow>;
}

/// 时间窗口
#[pyclass]
pub struct TimeWindow {
    #[pyo3(get)]
    pub keyword: String,          // 匹配的关键词
    #[pyo3(get)]
    pub start_hours_ago: Option<i64>,
    #[pyo3(get)]
    pub end_hours_ago: Option<i64>,
}
```

### 3.6 错误类型 (utils/error.rs)

```rust
use pyo3::exceptions::PyException;
use pyo3::create_exception;

// 定义Python异常类型
create_exception!(rainze_core, RainzeError, PyException);
create_exception!(rainze_core, FAISSError, RainzeError);
create_exception!(rainze_core, SystemMonitorError, RainzeError);
create_exception!(rainze_core, TokenizerError, RainzeError);
create_exception!(rainze_core, CacheError, RainzeError);

/// 错误类型枚举
#[derive(Debug)]
pub enum CoreError {
    /// FAISS相关错误
    FAISSError(String),
    /// 维度不匹配
    DimensionMismatch { expected: usize, got: usize },
    /// 索引未找到
    IndexNotFound(String),
    /// IO错误
    IOError(std::io::Error),
    /// 系统监控错误
    SystemError(String),
    /// 分词错误
    TokenizerError(String),
    /// 序列化错误
    SerializationError(String),
}

impl From<CoreError> for PyErr {
    fn from(err: CoreError) -> PyErr {
        match err {
            CoreError::FAISSError(msg) => FAISSError::new_err(msg),
            CoreError::DimensionMismatch { expected, got } => {
                FAISSError::new_err(format!("Dimension mismatch: expected {}, got {}", expected, got))
            }
            CoreError::IndexNotFound(id) => FAISSError::new_err(format!("Index not found: {}", id)),
            CoreError::IOError(e) => RainzeError::new_err(format!("IO error: {}", e)),
            CoreError::SystemError(msg) => SystemMonitorError::new_err(msg),
            CoreError::TokenizerError(msg) => TokenizerError::new_err(msg),
            CoreError::SerializationError(msg) => RainzeError::new_err(format!("Serialization error: {}", msg)),
        }
    }
}
```

---

## 4. 配置Schema

### 4.1 Cargo.toml

```toml
[package]
name = "rainze_core"
version = "0.1.0"
edition = "2024"
authors = ["Rainze Team"]
description = "Rainze AI Desktop Pet - Rust Performance Core"
license = "MIT"

[lib]
name = "rainze_core"
crate-type = ["cdylib"]

[dependencies]
# Python绑定
pyo3 = { version = "0.23", features = ["extension-module", "anyhow"] }
numpy = "0.23"

# FAISS绑定
faiss = "0.12"

# 系统信息
sysinfo = "0.32"

# Windows API
winapi = { version = "0.3", features = ["winuser", "processthreadsapi"] }

# 异步运行时
tokio = { version = "1", features = ["full"] }

# 并行计算
rayon = "1.10"

# 中文分词
jieba-rs = "0.7"

# 序列化
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

# LRU缓存
lru = "0.12"

# 日志
tracing = "0.1"

# 错误处理
anyhow = "1.0"
thiserror = "2.0"

[dev-dependencies]
criterion = "0.5"
tempfile = "3.14"

[profile.release]
lto = true
codegen-units = 1
opt-level = 3
```

### 4.2 运行时配置 (rust_core_settings.json)

```json
{
  "$schema": "rust_core_settings.schema.json",
  "version": "1.0.0",
  
  "faiss": {
    "default_dimension": 768,
    "auto_switch_threshold": 10000,
    "ivf_nlist": 100,
    "ivf_nprobe": 10
  },
  
  "reranker": {
    "weights": {
      "similarity": 0.4,
      "recency": 0.3,
      "importance": 0.2,
      "frequency": 0.1
    },
    "recency_decay_days": 7
  },
  
  "search_cache": {
    "max_entries": 100,
    "ttl_seconds": 300
  },
  
  "vectorize_queue": {
    "high_priority_threshold": 0.7,
    "max_retries": 3,
    "pending_file": "./data/pending_vectorization.json"
  },
  
  "system_monitor": {
    "refresh_interval_seconds": 5,
    "cpu_warning_threshold": 85,
    "memory_warning_threshold": 90
  },
  
  "activity_detector": {
    "cache_ttl_ms": 1000,
    "meeting_apps": [
      "Teams.exe", "Zoom.exe", "WeChat.exe", 
      "TencentMeeting.exe", "DingTalk.exe", "Feishu.exe"
    ],
    "game_processes": [
      "League of Legends.exe", "GenshinImpact.exe",
      "Valorant.exe", "PUBG.exe", "csgo.exe"
    ]
  },
  
  "tokenizer": {
    "use_hmm": true,
    "userdict_path": "./config/userdict.txt",
    "entity_pos_tags": ["n", "nr", "ns", "nt", "nz", "vn"],
    "min_entity_length": 2
  },
  
  "time_reference_rules": {
    "刚才|刚刚": { "hours": 1 },
    "今天": { "hours": 24 },
    "昨天": { "hours_range": [24, 48] },
    "最近|这几天": { "days": 3 },
    "上次|之前": { "days": 7 },
    "以前|很久": { "days": 30 }
  }
}
```

---

## 5. Python绑定接口

### 5.1 模块导出

```python
"""
rainze_core - Rust性能模块Python绑定

使用示例:
    from rainze_core import (
        FAISSWrapper, Reranker, SearchCache,
        VectorizeQueue, SystemMonitor, ActivityDetector,
        ChineseTokenizer, EntityDetector
    )
"""

# 类型存根文件 (rainze_core.pyi)
from typing import List, Tuple, Optional, Dict

class FAISSWrapper:
    def __init__(self, dimension: int = 768, index_type: str = "flat") -> None: ...
    def add(self, ids: List[str], vectors: "np.ndarray") -> None: ...
    def search(self, query: "np.ndarray", top_k: int) -> List[Tuple[str, float]]: ...
    def remove(self, ids: List[str]) -> int: ...
    def save(self, path: str) -> None: ...
    @staticmethod
    def load(path: str) -> "FAISSWrapper": ...
    def stats(self) -> "IndexStats": ...

class IndexStats:
    dimension: int
    count: int
    index_type: str
    memory_bytes: int

class RerankerWeights:
    similarity: float
    recency: float
    importance: float
    frequency: float
    def __init__(
        self, 
        similarity: float = 0.4,
        recency: float = 0.3,
        importance: float = 0.2,
        frequency: float = 0.1
    ) -> None: ...

class MemoryMeta:
    id: str
    created_at: int
    importance: float
    access_count: int
    similarity: float

class Reranker:
    def __init__(
        self, 
        weights: Optional[RerankerWeights] = None,
        recency_decay_days: float = 7.0
    ) -> None: ...
    def rerank(
        self, 
        candidates: List[MemoryMeta], 
        current_time: int, 
        top_k: int
    ) -> List[Tuple[str, float]]: ...
    def set_weights(self, weights: RerankerWeights) -> None: ...

class SearchCache:
    def __init__(self, max_entries: int = 100, ttl_seconds: int = 300) -> None: ...
    def get(self, cache_key: str) -> Optional[List[Tuple[str, float]]]: ...
    def set(self, cache_key: str, results: List[Tuple[str, float]]) -> None: ...
    def clear(self) -> None: ...
    def stats(self) -> "CacheStats": ...

class CacheStats:
    size: int
    hit_count: int
    miss_count: int
    hit_rate: float

class QueueItem:
    memory_id: str
    content: str
    importance: float
    retry_count: int
    created_at: int
    def __init__(
        self, 
        memory_id: str, 
        content: str, 
        importance: float
    ) -> None: ...

class VectorizeQueue:
    def __init__(self, high_threshold: float = 0.7) -> None: ...
    def push(self, item: QueueItem) -> None: ...
    def pop_batch(self, batch_size: int) -> List[QueueItem]: ...
    def retry(self, item: QueueItem) -> bool: ...
    def __len__(self) -> int: ...
    def is_empty(self) -> bool: ...
    def save(self, path: str) -> None: ...
    @staticmethod
    def load(path: str) -> "VectorizeQueue": ...

class SystemStatus:
    cpu_usage: float
    memory_usage: float
    memory_used_mb: int
    memory_total_mb: int
    timestamp: int

class SystemMonitor:
    def __init__(self, refresh_interval: int = 5) -> None: ...
    def get_status(self) -> SystemStatus: ...
    def refresh(self) -> None: ...
    def is_cpu_overloaded(self, threshold: float) -> bool: ...
    def is_memory_low(self, threshold: float) -> bool: ...

class ProcessInfo:
    name: str
    pid: int
    cpu_usage: float
    memory_mb: int
    is_running: bool

class ProcessMonitor:
    def __init__(self) -> None: ...
    def watch(self, process_name: str) -> None: ...
    def unwatch(self, process_name: str) -> None: ...
    def is_running(self, process_name: str) -> bool: ...
    def get_info(self, process_name: str) -> Optional[ProcessInfo]: ...
    def get_all_watched(self) -> List[ProcessInfo]: ...
    def detect_games(self, game_list: List[str]) -> List[str]: ...
    def detect_meeting_apps(self, app_list: List[str]) -> List[str]: ...

class ActivityStatus:
    is_fullscreen: bool
    fullscreen_app: Optional[str]
    is_in_meeting: bool
    meeting_app: Optional[str]
    active_window_title: str
    idle_seconds: int

class ActivityDetector:
    def __init__(self, cache_ttl_ms: int = 1000) -> None: ...
    def get_status(self, meeting_apps: List[str]) -> ActivityStatus: ...
    def is_fullscreen(self) -> bool: ...
    def get_active_window_title(self) -> str: ...
    def get_idle_time(self) -> int: ...

class ChineseTokenizer:
    def __init__(self, use_hmm: bool = True) -> None: ...
    def cut(self, text: str, cut_all: bool = False) -> List[str]: ...
    def cut_for_search(self, text: str) -> List[str]: ...
    def add_word(
        self, 
        word: str, 
        freq: Optional[int] = None, 
        tag: Optional[str] = None
    ) -> None: ...
    def load_userdict(self, path: str) -> None: ...
    def tag(self, text: str) -> List[Tuple[str, str]]: ...

class EntityResult:
    has_entities: bool
    entities: List[str]
    entity_count: int

class TimeWindow:
    keyword: str
    start_hours_ago: Optional[int]
    end_hours_ago: Optional[int]

class EntityDetector:
    def __init__(
        self, 
        entity_pos_tags: Optional[List[str]] = None,
        min_entity_length: int = 2
    ) -> None: ...
    def detect(self, text: str) -> EntityResult: ...
    def detect_time_reference(self, text: str) -> Optional[TimeWindow]: ...

# 异常类型
class RainzeError(Exception): ...
class FAISSError(RainzeError): ...
class SystemMonitorError(RainzeError): ...
class TokenizerError(RainzeError): ...
class CacheError(RainzeError): ...
```

---

## 6. 使用示例

### 6.1 记忆检索

```python
import numpy as np
from rainze_core import FAISSWrapper, Reranker, MemoryMeta, RerankerWeights

# 创建FAISS索引
faiss = FAISSWrapper(dimension=768, index_type="flat")

# 添加向量
ids = ["mem_001", "mem_002", "mem_003"]
vectors = np.random.randn(3, 768).astype(np.float32)
faiss.add(ids, vectors)

# 搜索
query = np.random.randn(768).astype(np.float32)
results = faiss.search(query, top_k=10)  # [(id, score), ...]

# 重排序
reranker = Reranker(
    weights=RerankerWeights(similarity=0.4, recency=0.3, importance=0.2, frequency=0.1),
    recency_decay_days=7.0
)

candidates = [
    MemoryMeta(id="mem_001", created_at=1735400000, importance=0.8, access_count=5, similarity=0.9),
    MemoryMeta(id="mem_002", created_at=1735300000, importance=0.5, access_count=2, similarity=0.85),
]
final_results = reranker.rerank(candidates, current_time=int(time.time()), top_k=5)
```

### 6.2 系统监控

```python
from rainze_core import SystemMonitor, ProcessMonitor, ActivityDetector

# 系统状态监控
monitor = SystemMonitor(refresh_interval=5)
status = monitor.get_status()
print(f"CPU: {status.cpu_usage}%, Memory: {status.memory_usage}%")

if monitor.is_cpu_overloaded(threshold=85):
    print("CPU过载警告!")

# 进程监控
process_monitor = ProcessMonitor()
process_monitor.watch("chrome.exe")
process_monitor.watch("code.exe")

if process_monitor.is_running("chrome.exe"):
    info = process_monitor.get_info("chrome.exe")
    print(f"Chrome PID: {info.pid}, Memory: {info.memory_mb}MB")

# 检测游戏进程
games = process_monitor.detect_games([
    "League of Legends.exe", "GenshinImpact.exe", "Valorant.exe"
])
if games:
    print(f"检测到游戏: {games}")

# 用户活动检测
activity = ActivityDetector(cache_ttl_ms=1000)
status = activity.get_status(meeting_apps=["Teams.exe", "Zoom.exe"])

if status.is_fullscreen:
    print(f"用户正在全屏使用: {status.fullscreen_app}")
if status.is_in_meeting:
    print(f"用户正在开会: {status.meeting_app}")
if status.idle_seconds > 300:
    print(f"用户已空闲 {status.idle_seconds} 秒")
```

### 6.3 文本处理

```python
from rainze_core import ChineseTokenizer, EntityDetector

# 分词
tokenizer = ChineseTokenizer(use_hmm=True)
words = tokenizer.cut("我喜欢吃苹果和香蕉")
print(words)  # ['我', '喜欢', '吃', '苹果', '和', '香蕉']

# 词性标注
tags = tokenizer.tag("我喜欢吃苹果")
print(tags)  # [('我', 'r'), ('喜欢', 'v'), ('吃', 'v'), ('苹果', 'n')]

# 添加自定义词
tokenizer.add_word("忆雨之岚", freq=10000, tag="nr")

# 实体检测
detector = EntityDetector(
    entity_pos_tags=["n", "nr", "ns", "nt", "nz"],
    min_entity_length=2
)
result = detector.detect("我之前说过喜欢苹果")
if result.has_entities:
    print(f"检测到实体: {result.entities}")

# 时间指代检测
time_ref = detector.detect_time_reference("昨天你说的那件事")
if time_ref:
    print(f"时间窗口: {time_ref.keyword} -> {time_ref.start_hours_ago}h ~ {time_ref.end_hours_ago}h")
```

---

## 7. 测试要点

### 7.1 单元测试

| 测试项 | 测试内容 | 预期结果 |
|--------|----------|----------|
| FAISS索引创建 | 创建Flat和IVF索引 | 成功创建，stats正确 |
| FAISS添加/搜索 | 添加1000条向量后搜索 | 返回正确top_k结果 |
| FAISS持久化 | save后load | 数据完整恢复 |
| 重排序准确性 | 验证各权重因素影响 | 排序符合预期 |
| 缓存命中 | 相同查询多次请求 | 第二次命中缓存 |
| 缓存过期 | 等待TTL后请求 | 缓存未命中 |
| 队列优先级 | 高低优先级混合入队 | 高优先级先出队 |
| CPU监控 | 获取CPU使用率 | 0-100范围内 |
| 内存监控 | 获取内存使用情况 | 数值合理 |
| 全屏检测 | 最大化窗口后检测 | 正确识别 |
| 空闲时间 | 无操作后检测 | 时间递增 |
| 中文分词 | 分词各种中文文本 | 结果正确 |
| 实体检测 | 检测名词性实体 | 正确识别 |
| 时间指代 | 检测时间关键词 | 返回正确窗口 |

### 7.2 性能测试

```rust
// benches/memory_search_bench.rs
use criterion::{criterion_group, criterion_main, Criterion};

fn bench_faiss_search(c: &mut Criterion) {
    // 准备10k条向量的索引
    let mut faiss = FAISSWrapper::new(768, "flat").unwrap();
    // ... 添加数据
    
    c.bench_function("faiss_search_10k", |b| {
        b.iter(|| {
            let query = /* random vector */;
            faiss.search(&query, 20)
        })
    });
}

fn bench_rerank(c: &mut Criterion) {
    let reranker = Reranker::new(None, 7.0);
    let candidates: Vec<MemoryMeta> = /* 100 candidates */;
    
    c.bench_function("rerank_100", |b| {
        b.iter(|| {
            reranker.rerank(candidates.clone(), 1735400000, 10)
        })
    });
}

criterion_group!(benches, bench_faiss_search, bench_rerank);
criterion_main!(benches);
```

### 7.3 集成测试

| 测试场景 | 测试步骤 | 验收标准 |
|----------|----------|----------|
| 完整检索流程 | 添加 → 搜索 → 重排序 → 缓存 | 端到端延迟<100ms |
| 高并发搜索 | 并发10个搜索请求 | 无死锁，结果正确 |
| 索引重建 | 删除50%数据后重建 | 搜索结果正确 |
| 异常恢复 | 模拟进程崩溃重启 | 队列数据恢复 |
| Python-Rust边界 | 大数组传输 | 无内存泄漏 |

---

## 8. 依赖关系

### 8.1 外部依赖

| 依赖 | 版本 | 用途 | 许可证 |
|------|------|------|--------|
| pyo3 | 0.23 | Python绑定 | Apache-2.0/MIT |
| numpy | 0.23 | NumPy绑定 | BSD-3-Clause |
| faiss | 0.12 | 向量搜索 | MIT |
| sysinfo | 0.32 | 系统信息 | MIT |
| winapi | 0.3 | Windows API | Apache-2.0/MIT |
| tokio | 1.x | 异步运行时 | MIT |
| rayon | 1.10 | 并行计算 | Apache-2.0/MIT |
| jieba-rs | 0.7 | 中文分词 | MIT |
| serde | 1.0 | 序列化 | Apache-2.0/MIT |
| lru | 0.12 | LRU缓存 | MIT |

### 8.2 内部模块依赖

```
rainze_core
├── memory_search
│   ├── faiss_wrapper (外部: faiss)
│   ├── reranker
│   └── cache (外部: lru)
├── vectorize
│   ├── queue
│   └── batch_processor
├── system_monitor (外部: sysinfo, winapi)
│   ├── cpu
│   ├── memory
│   ├── process
│   └── activity
├── text_process (外部: jieba-rs)
│   ├── tokenizer
│   └── entity
└── utils
    ├── error (外部: pyo3, thiserror)
    └── config (外部: serde)
```

### 8.3 被依赖模块

- **MOD-Memory**: 使用FAISSWrapper进行向量检索
- **MOD-Storage**: 使用VectorizeQueue管理向量化任务
- **MOD-State**: 使用SystemMonitor获取系统状态
- **MOD-Agent**: 使用ActivityDetector检测用户活动
- **MOD-AI**: 使用EntityDetector选择检索策略

---

## 9. 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0.0 | 2025-12-29 | 初始版本：FAISS封装、系统监控、文本处理 |

---

## 附录

### A. 构建说明

```bash
# 开发模式构建
cd rainze_core
maturin develop

# 发布模式构建
maturin build --release

# 运行测试
cargo test

# 运行性能测试
cargo bench

# 生成文档
cargo doc --open
```

### B. 平台兼容性

| 平台 | 支持状态 | 说明 |
|------|----------|------|
| Windows 10/11 | ✅ 完全支持 | 主目标平台 |
| macOS | ⚠️ 部分支持 | 需移除winapi依赖 |
| Linux | ⚠️ 部分支持 | 需移除winapi依赖 |

### C. 性能调优建议

1. **FAISS索引选择**: 数据量<10k用Flat，>=10k用IVF
2. **缓存大小**: 根据内存情况调整max_entries
3. **刷新间隔**: 非关键监控可增大refresh_interval
4. **并行度**: 根据CPU核数调整rayon线程池

---

> **文档生成**: Claude Opus 4.5
> **审核状态**: 待技术审核
> **下次更新**: 随代码实现同步更新
