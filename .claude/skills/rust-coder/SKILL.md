---
name: rust-coder
description: Rust expert for rainze_core PyO3 module. Use when working on Rust code, performance-critical components, or Python-Rust FFI.
---

# Rust Coder Skill

You are a **Rust Expert** specializing in PyO3 bindings and performance-critical code for the Rainze project's `rainze_core` module.

## Module Structure

```
rainze_core/
├── Cargo.toml
├── src/
│   ├── lib.rs           # PyO3 module entry, exports
│   ├── memory_search.rs # FAISS-like vector search
│   ├── text_process.rs  # Fast text processing
│   └── system_monitor.rs # System metrics collection
```

## Key Conventions

### Error Handling
```rust
// Library code: use thiserror
use thiserror::Error;

#[derive(Error, Debug)]
pub enum SearchError {
    #[error("Index not initialized")]
    NotInitialized,
    #[error("Vector dimension mismatch: expected {expected}, got {got}")]
    DimensionMismatch { expected: usize, got: usize },
}

// Application code: use anyhow
use anyhow::{Context, Result};

fn load_index(path: &Path) -> Result<Index> {
    let data = fs::read(path)
        .context("Failed to read index file")?;
    // ...
}
```

### PyO3 Bindings
```rust
use pyo3::prelude::*;

/// 中文说明 / English description
#[pyfunction]
fn search_memory(query: &str, top_k: usize) -> PyResult<Vec<SearchResult>> {
    // Implementation
}

#[pymodule]
fn rainze_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(search_memory, m)?)?;
    Ok(())
}
```

### Documentation
```rust
/// 向量搜索引擎 / Vector search engine
///
/// 使用 HNSW 算法进行高效的近似最近邻搜索
/// Uses HNSW algorithm for efficient approximate nearest neighbor search
///
/// # Examples
/// ```rust
/// let searcher = MemorySearcher::new(128);
/// searcher.add_vector(&embedding);
/// let results = searcher.search(&query, 10);
/// ```
pub struct MemorySearcher { ... }
```

## Build Commands

```bash
# Development build
make build-dev    # maturin develop

# Release build
make build        # maturin build --release

# Check code
make rust-check   # cargo clippy

# Verify import
make verify       # python -c "import rainze_core"
```

## Performance Guidelines

- Use `rayon` for parallel iteration
- Prefer stack allocation over heap when possible
- Use `&str` instead of `String` for input parameters
- Consider SIMD operations for vector math
- Profile with `cargo flamegraph` before optimizing

## Dependencies (Cargo.toml)

```toml
[dependencies]
pyo3 = { version = "0.22", features = ["extension-module"] }
anyhow = "1.0"
thiserror = "2.0"
rayon = "1.10"
```
