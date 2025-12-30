# TODO - rainze_core

Rust 性能模块任务追踪 / Rust performance module task tracking

## 进行中 (In Progress)

- [ ] 完善 `SystemMonitor` 全屏检测 ~2d #feature
  - [ ] 实现 Windows API 调用
  - [ ] 测试多显示器场景

## 待办 (Backlog)

- [ ] 实现 `MemorySearcher` FAISS 封装 ~5d #feature
  - [ ] 研究 faiss-rs crate 可用性
  - [ ] 设计 Python 接口
  - [ ] 实现向量搜索
  - [ ] 实现重排序功能

- [ ] 实现 `TextProcessor` 文本处理 ~3d #feature
  - [ ] 中文分词集成
  - [ ] 实体检测功能

- [ ] 添加基准测试 ~1d #test
  - [ ] memory_search benchmark
  - [ ] system_monitor benchmark

## 已完成 ✓

- [x] 项目初始化 2025-12-30
- [x] Cargo.toml 配置 2025-12-30
- [x] SystemMonitor 基础实现 2025-12-30
- [x] PyO3 模块导出 2025-12-30
