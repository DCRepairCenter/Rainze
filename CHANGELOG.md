# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **项目初始化** - 完整的 Python + Rust 混合项目结构
  - `pyproject.toml` - Python 包配置 (uv + hatchling)
  - `rainze_core/Cargo.toml` - Rust crate 配置 (PyO3 + Maturin)
  - `src/rainze/` - Python 源码目录结构
  - `config/` - JSON 配置文件 (app_settings, api_settings, scene_tier_mapping)
  - `.pre-commit-config.yaml` - 预提交钩子配置
  - `.gitignore` - Git 忽略规则
  - `tests/` - 测试框架 (pytest)
- **Rust 核心模块** (rainze_core)
  - `SystemMonitor` - 系统监控 (CPU/内存/会议应用检测)
  - 占位模块: `memory_search`, `text_process`
- **开发工具配置**
  - ruff (linter + formatter)
  - mypy (type checker)
  - pytest + pytest-asyncio
  - pre-commit hooks

- **文档梳理** - 为全仓目录补充 README/CHANGELOG/TODO，占位联系信息与路线图，便于后续迭代对齐 PRD/TECH。  
- **跨模块契约规范** (PRD §0.15) - 统一数据结构和接口定义
  - `EmotionTag` - 情感标签契约 (core.contracts.emotion)
  - `SceneType/ResponseTier` - 场景分类契约 (core.contracts.scene)
  - `InteractionRequest/Response` - 交互契约 (core.contracts.interaction)
  - `IRustBridge` 接口族 - Rust边界契约 (core.contracts.rust_bridge)
  - `Tracer/TraceSpan` - 可观测性契约 (core.observability)
- **场景-Tier中央配置表** (config/scene_tier_mapping.json)
- **MOD-Core 扩展**
  - contracts/ 目录 - 跨模块契约定义
  - observability/ 目录 - 统一追踪器实现
- **MOD-Features-Basic 扩展**
  - BaseFeature 基类 - 统一功能接口
  - FeatureRegistry - 功能注册表
- **MOD-Plugins 权限模型增强**
  - PluginPermission Flag - 权限标志组合
  - ResourceLimits - 资源限制配置
  - 按插件类型的默认权限/限制

### Changed

- **PRD-Rainze.md** v3.0.3 → v3.1.0
  - 新增 §0.15 跨模块契约规范章节
- **MOD-Core** v1.0.0 → v1.1.0
  - 新增 contracts/ 和 observability/ 目录
- **MOD-AI** v1.0.0 → v1.1.0
  - SceneClassifier 改为引用 core.contracts.scene
  - 删除重复的 SceneComplexity 枚举定义
- **MOD-Agent** v1.0.0 → v1.1.0
  - UCM.process_interaction() 使用统一 InteractionRequest/Response
  - 删除重复的 InteractionType/SceneType 枚举定义
  - 添加可观测性 Tracer.span() 支持
- **MOD-State** v1.0.0 → v1.1.0
  - IntensityParser 返回统一 EmotionTag 类型
- **MOD-RustCore** v1.0.0 → v1.1.0
  - 新增 Rust/Python 边界职责表
  - 明确回退策略
- **MOD-Features-Basic** v1.0.0 → v1.1.0
  - 功能清单增加场景类型列
  - 新增 base.py (BaseFeature) 和 registry.py
- **MOD-Plugins** v1.0.0 → v1.1.0
  - 权限模型改用 Flag 枚举支持组合
  - 新增 ResourceLimits 资源限制
  - 新增插件与Tools/Features边界说明
- **modules/README.md** v1.0.0 → v1.1.0
  - 模块依赖矩阵更新为包含 (含contracts)
  - 新增跨模块契约章节

### Fixed

- 解决多个模块重复定义 SceneType/EmotionTag 的问题
- 统一 UCM 为交互唯一入口，禁止其他模块绕过

---

## [Initial] - 2025-12-29

### Added

- 项目文档基础设施
  - Keep a Changelog 规范参考文档
  - Conventional Commits 规范参考文档
  - Product Requirements Analyst 角色定义
  - Technical Specification Writer 角色定义
  - Rainze 技术选型报告 (TECH-Rainze.md v1.0.1)
- 模块设计文档 (.github/prds/modules/)
  - 3层架构定义 (基础设施层、业务逻辑层、应用层)
  - 11个模块的详细设计文档
  - 开发阶段规划 (MVP → Core → Full)
- AI Agent 定义
  - API Designer Agent (api-designer.agent.md)
  - Rust Coder Agent (rust-coder.agent.md)
- Rust 代码风格指南 (.github/references/rust/style.md)
- Git 配置
  - .gitattributes 行尾符规范化配置

[unreleased]: https://github.com/begonia/Rainze/compare/HEAD
