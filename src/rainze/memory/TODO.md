# TODO - Memory 模块

记忆系统模块的任务追踪。

## 进行中 (In Progress)

_当前无进行中任务_

## 待办 (Backlog)

### 高优先级 (P0)

- [ ] 实现向量检索 (FAISS) ~3d #feature
  - [ ] 集成 FAISS 索引
  - [ ] 实现 VectorSearcher
  - [ ] 实现 HybridRetriever 混合检索

- [ ] 实现 Identity Layer (Layer 1) ~2d #feature
  - [ ] 系统提示词管理
  - [ ] 用户档案管理

### 中优先级 (P1)

- [ ] 实现重要度自动评估 ~1d #feature
  - [ ] ImportanceEvaluator 规则评估
  - [ ] LLM 评估（可选）

- [ ] 实现记忆衰减机制 ~1d #feature
  - [ ] DecayManager 衰减计算
  - [ ] 定时衰减任务

- [ ] 实现记忆归档 ~1d #feature
  - [ ] ArchivalManager
  - [ ] 动态阈值计算

### 低优先级 (P2)

- [ ] 实现矛盾检测 ~2d #feature
  - [ ] ConflictDetector
  - [ ] 态度三元组提取
  - [ ] Reflection 生成

- [ ] 实现向量化队列 ~1d #feature
  - [ ] VectorizeQueue
  - [ ] 后台 Worker

- [ ] 添加单元测试 ~2d #test
  - [ ] MemoryManager 测试
  - [ ] FTSSearcher 测试
  - [ ] WorkingMemory 测试

### 技术债务

- [ ] 添加更多类型注解测试 #refactor
- [ ] 优化 FTS5 查询性能 #perf
- [ ] 添加指标监控 #observability

## 已完成 ✓

- [x] 基础模块结构搭建 2025-12-30
- [x] MemoryItem, FactItem, EpisodeItem 数据模型 2025-12-30
- [x] RetrievalResult, MemoryIndexItem 数据模型 2025-12-30
- [x] WorkingMemory (Layer 2) 实现 2025-12-30
- [x] FTSSearcher FTS5 全文检索 2025-12-30
- [x] MemoryManager 主入口类 2025-12-30
- [x] 异常定义 2025-12-30
- [x] 模块文档 (README.md) 2025-12-30
