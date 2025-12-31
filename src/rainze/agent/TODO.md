# TODO - Agent 模块

统一上下文管理器 (UCM) 和 Agent 自主循环模块。

## 进行中 (In Progress)

- [x] UCM 基础实现 ~2d #feature 2025-12-30
  - [x] UnifiedContextManager 类
  - [x] SceneClassifier 场景分类器
  - [x] TierHandlerRegistry 层级处理器
  - [x] Tier1TemplateHandler
  - [x] Tier2RuleHandler
  - [x] Tier3LLMHandler (占位实现)

## 待办 (Backlog)

### P0 - 核心功能

- [ ] 可观测性集成 ~1d #feature
  - [ ] 接入 Tracer.span() 追踪
  - [ ] 添加 metrics 收集

- [ ] Memory 集成 ~2d #feature
  - [ ] 记忆检索实现
  - [ ] 记忆写入实现
  - [ ] 聚合策略实现

- [ ] State 集成 ~1d #feature
  - [ ] 状态更新
  - [ ] 情感同步

- [ ] AI 服务集成 ~2d #feature
  - [ ] Tier3LLMHandler 完整实现
  - [ ] 提示词模板管理

### P1 - Agent 循环

- [ ] AgentLoop 自主循环 ~3d #feature
  - [ ] 5阶段循环实现
  - [ ] 感知上下文构建
  - [ ] 候选事件评估

- [ ] BehaviorPlanner 行为计划 ~2d #feature
  - [ ] 意图规则引擎
  - [ ] 计划生成与注入

- [ ] IntentRecognizer 意图识别 ~1d #feature
  - [ ] 指令检测
  - [ ] 关键词匹配
  - [ ] 实体提取

- [ ] ConversationManager 对话管理 ~2d #feature
  - [ ] 会话生命周期
  - [ ] 历史压缩
  - [ ] 话题追踪

### P2 - 主动行为

- [ ] ProactiveBehaviorRegistry ~2d #feature
  - [ ] 行为注册表
  - [ ] 默认行为注册
  - [ ] 冷却时间管理

- [ ] 主动行为实现 ~3d #feature
  - [ ] 整点报时
  - [ ] 系统警告
  - [ ] 闲聊触发
  - [ ] 睡眠触发

### P3 - 增强功能

- [ ] 配置文件支持 ~1d #enhancement
  - [ ] context_manager_settings.json
  - [ ] agent_loop_settings.json
  - [ ] 配置热重载

- [ ] 单元测试 ~2d #test
  - [ ] UCM 测试
  - [ ] SceneClassifier 测试
  - [ ] TierHandlers 测试

## 已完成 ✓

- [x] 模块初始化 2025-12-30
  - [x] 目录结构创建
  - [x] __init__.py 导出配置
  - [x] README.md 文档
  - [x] CHANGELOG.md 初始化
