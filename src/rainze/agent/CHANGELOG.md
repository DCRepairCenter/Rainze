# Changelog

All notable changes to the Agent module will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 待添加功能...

## [0.1.0] - 2025-12-30

### Added

#### UnifiedContextManager (UCM)
- 实现统一上下文管理器作为所有用户交互的唯一入口点
- `process_interaction()` 方法处理所有类型的交互请求
- `get_context_summary()` 方法获取 UCM 状态摘要
- 支持自定义处理器注册 `register_custom_handler()`
- 记忆写入策略配置 (FULL/SUMMARY/RESULT_ONLY/NONE)

#### SceneClassifier
- 实现场景分类器，无 API 调用的纯规则匹配
- 支持 SIMPLE/MEDIUM/COMPLEX 三种场景类型
- 简单事件类型集合 (click, drag, hover 等)
- 中等事件类型集合 (hourly_chime, system_warning 等)
- 复杂场景关键词检测
- 自定义分类规则支持

#### TierHandlerRegistry
- 层级处理器注册表，管理 Tier1/2/3 处理器
- 带降级链的处理方法 `handle_with_fallback()`

#### Tier1TemplateHandler
- 模板响应处理器，响应时间 <50ms
- 预设模板库 (click, drag, hover, game_interaction)
- 随机选择模板增加自然感
- 支持自定义模板添加

#### Tier2RuleHandler
- 规则生成处理器，响应时间 <100ms
- 整点报时规则 (分时段问候)
- 系统警告规则 (CPU/内存/电量)
- 天气更新规则
- 主动问候规则
- 工具执行结果规则
- 支持自定义规则注册

#### Tier3LLMHandler
- LLM 生成处理器，响应时间 <3s
- 占位实现 (AI 服务模块待集成)
- 简单关键词响应映射
- 兜底模板支持

#### 异常定义
- UCMError 基础异常
- ClassificationError 分类错误
- HandlerError 处理器错误

#### 数据类
- InteractionContext 内部上下文
- ClassifiedScene 分类结果
- ClassificationResult 详细分类结果
- TierResponse 层级响应
- MemoryWriteConfig 记忆写入配置

### Documentation
- README.md 模块说明文档
- TODO.md 任务追踪
- CHANGELOG.md 变更记录

### Notes
- 遵循 PRD §0.5a 统一上下文管理器设计
- 遵循 MOD-Agent.md 模块设计规范
- 所有共享类型从 `rainze.core.contracts` 导入
- 中英双语注释
