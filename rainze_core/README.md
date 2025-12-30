# Rainze Core - Rust 性能模块

> Rainze AI 桌面宠物的高性能 Rust 核心模块

## 📖 目录

- [关于模块](#关于模块)
- [架构设计](#架构设计)
- [快速开始](#快速开始)
- [API 参考](#api-参考)
- [构建说明](#构建说明)

## 关于模块

Rainze Core 是 Rainze 应用的 Rust 性能模块，通过 PyO3 提供 Python 绑定。

### 职责

- **记忆检索**: FAISS 向量相似度搜索封装
- **系统监控**: CPU/内存使用率、全屏/会议应用检测
- **文本处理**: 高性能中文分词、实体检测

### 技术栈

* ![Rust](https://img.shields.io/badge/Rust-1.92+-orange)
* ![PyO3](https://img.shields.io/badge/PyO3-0.23-blue)

## 架构设计

```
rainze_core/
├── Cargo.toml
├── README.md
└── src/
    ├── lib.rs              # PyO3 模块导出
    ├── memory_search.rs    # FAISS 向量检索
    ├── system_monitor.rs   # 系统状态监控
    └── text_process.rs     # 文本处理工具
```

## 快速开始

### 前置条件

* Rust 1.92+
* Python 3.12+
* Maturin

### 开发构建

```bash
cd rainze_core
maturin develop
```

### 使用示例

```python
import rainze_core

# 系统监控
monitor = rainze_core.SystemMonitor()
print(f"CPU: {monitor.get_cpu_usage():.1f}%")
print(f"Memory: {monitor.get_memory_usage():.1f}%")
print(f"Fullscreen: {monitor.is_fullscreen()}")
print(f"Meeting: {monitor.is_meeting_app()}")
```

## API 参考

### `SystemMonitor`

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `get_cpu_usage()` | `float` | CPU 使用率 (0-100) |
| `get_memory_usage()` | `float` | 内存使用率 (0-100) |
| `is_fullscreen()` | `bool` | 是否有全屏应用 |
| `is_meeting_app()` | `bool` | 是否有会议应用 |
| `refresh()` | `None` | 刷新系统信息 |

## 构建说明

### 开发模式

```bash
maturin develop
```

### 发布构建

```bash
maturin build --release
```

### 运行测试

```bash
cargo test
```

## 依赖关系

### 被依赖于

- `rainze.memory` - 记忆检索
- `rainze.features` - 系统监控功能

## 参考

- [PyO3 User Guide](https://pyo3.rs/)
- [Maturin](https://github.com/PyO3/maturin)
- [MOD-RustCore.md](../.github/prds/modules/MOD-RustCore.md)
