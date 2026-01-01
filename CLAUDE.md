# Rainze 项目指南

> AI 驱动的桌面宠物应用，采用 Python + Rust 混合架构

## 核心设计哲学

**AI 生成为主，配置为辅，预设文本仅作紧急兜底。**

## 架构概览

```
用户交互 → UCM (统一上下文管理器) → 场景分类 → Tier1/2/3 响应
                    ↓
              记忆系统 (FAISS + SQLite)
                    ↓
              Rust 性能层 (rainze_core)
```

**3 层响应策略**:
- **Tier1**: 模板响应 (<50ms) - 点击、拖拽
- **Tier2**: 规则生成 (<100ms) - 整点报时、系统警告
- **Tier3**: LLM 生成 (<3s) - 对话、情感分析

## 常用命令

```bash
# 环境初始化 (首次)
make setup              # 创建venv + 安装依赖 + 构建Rust

# 日常开发
make build-dev          # Rust 开发模式构建 (maturin develop)
make verify             # 验证 rainze_core 是否可导入
make run                # 运行应用

# 代码质量
make check              # 运行 lint + typecheck + test
make lint               # ruff check
make format             # ruff 格式化
make typecheck          # mypy 类型检查
make rust-check         # cargo clippy

# 测试
make test               # pytest 全量测试
make test-unit          # 仅单元测试
make test-cov           # 带覆盖率报告

# 构建发布
make build              # Rust release 模式构建
make package            # 构建 wheel 包
```

## 关键约定

### 跨模块契约 (PRD §0.15)

**IMPORTANT**: 所有共享类型必须从 `rainze.core.contracts` 导入，禁止重复定义！

```python
# ✅ 正确
from rainze.core.contracts import EmotionTag, SceneType

# ❌ 错误 - 不要在其他模块重复定义
class EmotionTag: ...  # NEVER DO THIS
```

### UCM 入口规则

所有用户交互 **必须** 经过 UCM (统一上下文管理器)，禁止直接调用 AI 服务。

### 代码规范

- **Python**: 全函数类型注解，Google-style docstrings，line-length=88
- **Rust**: 使用 `anyhow` (应用) / `thiserror` (库)，`///` 文档注释
- **双语注释**: `中文说明 / English description`
- **Lint**: ruff 启用 E/W/F/I/B/C4/UP/ARG/SIM/TCH/PTH/ERA/PL/RUF 规则

### 测试规范

- 单元测试放 `tests/unit/`，集成测试放 `tests/integration/`
- 使用 `pytest.mark.slow` 标记耗时测试
- 异步测试自动识别 (`asyncio_mode="auto"`)
- 覆盖率目标: `src/rainze/` 目录

### Commit 规范

遵循 Conventional Commits，AI 生成时添加 `Reviewed-by: [MODEL_NAME]`

```
feat|fix|docs|style|refactor|perf|test|chore|build|ci
```

## 项目结构

| 目录 | 说明 |
|------|------|
| `src/rainze/` | Python 主代码 |
| `src/rainze/core/contracts/` | 跨模块共享类型 ⚠️ |
| `rainze_core/` | Rust 性能模块 (PyO3) |
| `config/` | JSON 配置文件 |
| `.github/prds/` | PRD 需求文档 |
| `.github/prds/modules/` | 模块设计文档 (MOD-*.md) |

## 核心文档参考

- **PRD**: `.github/prds/PRD-Rainze.md` - 完整产品需求
- **技术选型**: `.github/techstacks/TECH-Rainze.md` - 技术决策
- **模块设计**: `.github/prds/modules/MOD-{name}.md` - 具体模块规格

## 自定义代理触发

使用 `/agents` 查看可用的专门代理，或直接请求：

| 用途 | 请求示例 |
|------|----------|
| 代码编写 | "use code-writer agent to implement..." |
| Rust 开发 | "use rust-coder agent for..." |
| 提交消息 | "use commit-helper to create commit" |
| PRD 分析 | "use prd-analyst to analyze..." |
| 技术规范 | "use tech-spec-writer to create..." |
| API 设计 | "use api-designer for..." |
