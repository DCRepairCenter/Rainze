# Rainze 项目 Copilot 指南

## 项目概述

Rainze 是一个 **AI 驱动的桌面宠物应用** 的规划仓库，采用 Python + Rust 混合架构。本仓库主要存储 AI 提示工程模板、PRD 文档和技术规范。

**核心设计哲学**：AI 生成为主，配置为辅，预设文本仅作紧急兜底。

## 仓库结构

```
.github/
├── agents/       # AI Agent 定义文件 (*.agent.md)
├── instructions/ # 路径特定指令 (*.instructions.md)
├── prds/         # 产品需求文档 (PRD-*.md)
├── prompts/      # 元提示模板 (已迁移至 agents/)
├── references/   # 参考规范 (conventional-commit.md 等)
├── roles/        # 角色定义 (完整指南)
└── techstacks/   # 技术选型报告 (TECH-*.md)
```

## AI Agent 系统

### 可用 Agents

| Agent | 用途 | 触发方式 |
|-------|------|----------|
| `repo-scanner` | 扫描仓库生成索引 | "scan repo" |
| `prompt-generator` | 生成 init/qa 提示 | "generate prompts" |
| `prompt-optimizer` | 对抗性优化提示 | "optimize prompts" |
| `prd-analyst` | PRD 结构化分析 | "analyze PRD" |
| `tech-spec-writer` | 技术规范撰写 | "write tech spec" |
| `commit-helper` | Conventional Commits | "create commit" |

### APE 工作流（优化版）

1. **Phase 1**: `agents/repo-scanner.agent.md` → 生成 `.prompt/repo-index.md`（索引，非复制）
2. **Phase 2**: `agents/prompt-generator.agent.md` → 生成 `.prompt/init.prompt.md` 和 `.prompt/qa-deep.prompt.md`
3. **Phase 3**: `agents/prompt-optimizer.agent.md` → 对抗性迭代优化

**关键优化**：使用文件引用 `[name](path#L1-L50)` 代替内容复制，大幅减少 token 消耗。

## 技术栈 (目标应用)

| 层级 | 技术 | 用途 |
|------|------|------|
| GUI | PySide6 (Qt6) | 透明窗口、动画渲染 |
| 业务逻辑 | Python 3.12+ | LLM 调用、插件系统 |
| 性能关键 | Rust (PyO3/Maturin) | 向量检索、系统监控 |
| 存储 | FAISS + SQLite | 向量索引 + 结构化数据 |

## 文档编写约定

### PRD 文档格式

使用 **Interface Flow** 结构化格式，参考 [roles/product-requirements-analyst.md](.github/roles/product-requirements-analyst.md)：

```
[界面名称]
|-- 元素A
|-- 元素B + 元素C
\-- 最后一个元素
```

### Commit 规范

遵循 Conventional Commits，参考 [references/git/conventional-commit.md](.github/references/git/conventional-commit.md)：

```
feat(scope): 描述
fix(scope): 描述
docs: 更新文档
```

## 关键规则

1. **索引优先**：使用文件引用 `[name](path#L1-L50)` 而非复制文件内容
2. **源码权威性**：`.prompt/` 生成的文件仅作参考，实际源码是唯一真相来源
3. **语言约定**：自然语言输出使用简体中文，代码/路径/变量名保持原样
4. **证据规则**：指出问题时必须引用文件路径和行号
5. **不做处方**：分析问题时专注诊断，不主动提供修改建议

## 开发环境

- Windows 11 Pro (25H2)
- Python 3.12.12 (via uv)
- Rust 1.92.0
- 目标内存占用 <100MB

---

> 如需了解完整产品需求，请阅读 [prds/PRD-Rainze.md](.github/prds/PRD-Rainze.md)
