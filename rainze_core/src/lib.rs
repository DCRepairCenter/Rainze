//! Rainze Core - Rust 性能模块
//!
//! 提供 Rainze AI 桌面宠物应用的性能关键功能。
//! Provides performance-critical functionality for Rainze AI Desktop Pet.
//!
//! # Modules / 模块
//!
//! - `memory_search`: FAISS 向量检索封装 / FAISS vector search wrapper
//! - `system_monitor`: 系统状态监控 / System status monitoring
//! - `text_process`: 文本处理工具 / Text processing utilities
//!
//! # Example / 示例
//!
//! ```python
//! import rainze_core
//!
//! # 系统监控 / System monitoring
//! monitor = rainze_core.SystemMonitor()
//! print(f"CPU: {monitor.get_cpu_usage()}%")
//! print(f"Memory: {monitor.get_memory_usage()}%")
//! ```
//!
//! # Reference / 参考
//!
//! - TECH: .github/techstacks/TECH-Rainze.md §3.2
//! - MOD: .github/prds/modules/MOD-RustCore.md

use pyo3::prelude::*;

pub mod memory_search;
pub mod system_monitor;
pub mod text_process;

/// Rainze Core Python 模块
/// Rainze Core Python module
///
/// 导出所有 Rust 功能到 Python。
/// Exports all Rust functionality to Python.
#[pymodule]
fn rainze_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // 注册系统监控类 / Register system monitor class
    m.add_class::<system_monitor::SystemMonitor>()?;

    // 注册版本信息 / Register version info
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;

    Ok(())
}
