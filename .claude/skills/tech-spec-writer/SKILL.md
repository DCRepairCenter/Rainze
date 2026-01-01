---
name: tech-spec-writer
description: Technical specification writer. Use when creating detailed technical documentation, API specifications, or architecture documents.
---

# Tech Spec Writer Skill

Write detailed technical specifications and architecture documents.

## Document Structure

```markdown
# TECH-{ModuleName}: {模块名称}

## 1. 概述 / Overview
{模块职责和核心功能}

## 2. 架构 / Architecture
{分层设计、组件关系}

## 3. 接口定义 / Interface Definitions
{公共 API、数据类型}

## 4. 数据流 / Data Flow
{输入输出、处理流程}

## 5. 依赖 / Dependencies
{外部依赖、内部依赖}

## 6. 配置 / Configuration
{配置项、环境变量}

## 7. 错误处理 / Error Handling
{异常类型、处理策略}

## 8. 性能考量 / Performance Considerations
{响应时间、资源使用}

## 9. 测试策略 / Testing Strategy
{单元测试、集成测试}
```

## Conventions

- Use bilingual section headers (中文 / English)
- Include code examples for interfaces
- Reference contract types from `core.contracts`
- Specify response tier requirements (Tier1: <50ms, Tier2: <100ms, Tier3: <3s)

## Reference Documents

- Main tech stack: `.github/techstacks/TECH-Rainze.md`
- Module designs: `.github/prds/modules/MOD-*.md`
- PRD: `.github/prds/PRD-Rainze.md`
