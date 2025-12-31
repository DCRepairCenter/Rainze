# TODO - State Module

状态管理模块，负责桌宠核心状态维护。
State management module for pet core state maintenance.

## 进行中 (In Progress)

_当前无进行中任务 / No tasks in progress_

## 待办 (Backlog)

- [ ] 实现 sync/ 子模块（状态存储和检查点）~2d #feature
  - [ ] StateStore 状态存储
  - [ ] CheckpointManager 检查点管理
  - [ ] StateCache 内存缓存
  - [ ] ChangeNotifier 变更通知
- [ ] 实现 HungerManager 饥饿度管理 ~4h #feature
- [ ] 实现 CoinsManager 金币管理 ~4h #feature
- [ ] 实现 IntensityParser 情感强度解析 ~4h #feature
- [ ] 添加状态配置文件加载 ~2h #enhancement
- [ ] 添加单元测试 ~4h #test
- [ ] 集成测试与其他模块 ~4h #test

## 已完成 ✓

- [x] 创建模块目录结构 2025-12-30
- [x] 实现 MoodState, MoodSubState 枚举 2025-12-30
- [x] 实现 EmotionStateMachine 情绪状态机 2025-12-30
- [x] 实现 AttributeManager 抽象基类 2025-12-30
- [x] 实现 EnergyManager 能量管理 2025-12-30
- [x] 实现 AffinityManager 好感度管理 2025-12-30
- [x] 实现 StateManager 状态管理器 2025-12-30
- [x] 实现状态事件模型 2025-12-30
- [x] 创建模块 README.md 2025-12-30
