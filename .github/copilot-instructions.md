# Rainze 项目 Copilot 指南

## 项目概述

Rainze 是一个 **AI 驱动的桌面宠物应用**的**规划仓库**（无实际代码实现），采用 Python + Rust 混合架构。本仓库存储 PRD 文档、技术规范和 AI Agent 定义。

**核心设计哲学**：AI 生成为主，配置为辅，预设文本仅作紧急兜底。

## 仓库结构

```
.github/
├── agents/       # AI Agent 定义 (*.agent.md) - 触发词见下表
├── instructions/ # 路径特定指令 (*.instructions.md)
├── prds/         # PRD-Rainze.md (6800+ 行完整需求)
├── references/   # 参考规范 (Conventional Commits, Keep a Changelog)
├── roles/        # 角色定义 (PRD分析师, 技术规范撰写)
└── techstacks/   # 技术选型报告 TECH-Rainze.md
```

## AI Agent 触发

| 触发词 | Agent | 输出 |
|--------|-------|------|
| "scan repo" | repo-scanner | `.prompt/repo-index.md` |
| "generate prompts" | prompt-generator | `.prompt/init.prompt.md` |
| "create commit" | commit-helper | Conventional Commit 消息 |
| "analyze PRD" | prd-analyst | Interface Flow 结构化分析 |
| "write tech spec" | tech-spec-writer | 技术规范文档 |
| "write rust" | rust-coder | 安全惯用的 Rust 代码 |
| "design API" | api-designer | OpenAPI 规范 + API 设计文档 |
| "write code" | code-writer | Python/Rust 代码实现 |

## 关键约定

1. **索引优先**：使用文件引用 `[name](path#L1-L50)` 而非复制内容
2. **语言约定**：自然语言用简体中文，代码/路径/变量名保持原样
3. **证据规则**：指出问题时必须引用文件路径和行号
4. **Commit 规范**：遵循 [Conventional Commits](references/git/conventional-commit.md)，AI 生成时添加 `Reviewed-by: [MODEL_NAME]`
5. **PRD 格式**：使用 Interface Flow 树形结构（`|--` / `\--`），参考 [roles/product-requirements-analyst.md](roles/product-requirements-analyst.md)
6. **Rust 风格**：遵循 [Rust Style Guide](references/rust/style.md)，优先借用而非 `.clone()`，避免滥用 `.unwrap()`

## 目标技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| GUI | PySide6 (Qt6) | 透明窗口、动画 |
| 业务 | Python 3.12+ | LLM 调用、插件 |
| 性能 | Rust (PyO3) | 向量检索、系统监控 |
| 存储 | FAISS + SQLite | 向量索引 + 结构化数据 |

## 核心文档入口

- **完整 PRD**：[prds/PRD-Rainze.md](prds/PRD-Rainze.md) (v3.0.3)
- **技术选型**：[techstacks/TECH-Rainze.md](techstacks/TECH-Rainze.md) (v1.0.1)
- **变更日志**：[CHANGELOG.md](../CHANGELOG.md)
