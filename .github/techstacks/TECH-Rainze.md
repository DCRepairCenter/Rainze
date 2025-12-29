# Rainze - AI桌面宠物 技术选型报告

> **版本**: v1.0.1
> **作者**: Technical Specification Writer (AI-assisted)
> **团队**: Rainze Development Team
> **评审人**: GitHub Copilot (技术审核)
> **创建时间**: 2025-12-29
> **最后更新**: 2025-12-29
> **关联PRD**: PRD-Rainze.md v3.0.3

---

## 1. 引言

### 1.1 概述

本文档为 **Rainze AI桌面宠物** 项目的技术选型报告，基于 PRD v3.0.3 的需求定义，对项目涉及的关键技术进行深度分析和选型论证。

**项目核心定位**: 一个云端AI驱动的桌面宠物应用，强调智能陪伴、轻度养成、效率工具整合。

**核心设计哲学**:

- AI生成为主，配置为辅，预设文本仅作紧急兜底
- 云端LLM优先，本地LLM仅作为可选的离线应急插件
- 桌面应用轻量化，常驻内存 <100MB

### 1.2 术语表

| 术语 | 定义 |
|------|------|
| **LLM** | Large Language Model，大语言模型 |
| **FAISS** | Facebook AI Similarity Search，向量相似度搜索库 |
| **FTS5** | Full-Text Search 5，SQLite全文搜索扩展 |
| **PyO3** | Rust与Python互操作的绑定库 |
| **Maturin** | Rust Python扩展的构建工具 |
| **ReAct** | Reasoning + Acting，LLM推理-行动模式 |
| **PII** | Personally Identifiable Information，个人身份信息 |
| **TTL** | Time To Live，缓存过期时间 |

### 1.3 项目背景与目标

**项目目标**:

1. 构建一个AI驱动的桌面宠物，支持智能对话、情感陪伴、效率工具
2. 采用混合架构(Python + Rust)，兼顾开发效率与性能
3. 实现3层记忆系统（身份层、工作记忆、长期记忆）
4. 支持插件扩展，允许用户自定义功能

**技术目标**:

- 应用启动时间 <3秒
- 常驻内存 <100MB
- AI响应延迟 <2秒（Tier3场景）
- 支持离线降级运行

### 1.4 约束条件

**开发环境**:

- 操作系统: Windows 11 Pro Workstation (25H2)
- CPU: AMD RYZEN AI MAX+ 395 (32核 @ 5.15GHz)
- GPU: AMD Radeon 8060S (16GB, 集成)
- 内存: 48GB DDR5
- Python: 3.12.12 (via uv)
- Rust: 1.92.0

**技术约束**:

- 单用户桌面应用，无需分布式架构
- 主要目标平台为Windows，跨平台为次要目标
- 网络依赖云端LLM，需要良好的离线降级策略

---

## 2. 技术架构总览

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户交互层 (GUI)                          │
│                   PySide6 (Qt6) - 透明窗口                       │
├─────────────────────────────────────────────────────────────────┤
│                       业务逻辑层 (Python)                        │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │ 对话管理器   │ 状态系统     │ 工具调用     │ 插件系统     │  │
│  │ (Context)    │ (State)      │ (Tool Use)   │ (Plugin)     │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                    AI服务层 (Python + Rust)                      │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │ Prompt构建   │ LLM调用      │ 记忆检索     │ 响应生成     │  │
│  │ (Python)     │ (Python)     │ (Rust)       │ (Python)     │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                       数据持久层 (Rust + Python)                 │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │ SQLite       │ FAISS        │ JSON配置     │ 文件存储     │  │
│  │ (结构化数据) │ (向量索引)   │ (配置管理)   │ (日志/备份)  │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 混合架构说明 (Python + Rust)

**Python层** (业务逻辑 + AI调用):

- GUI渲染 (PySide6)
- LLM API调用与Prompt构建
- 插件系统与配置管理
- 用户交互处理
- 状态管理与事件循环

**Rust层** (性能关键路径):

- 记忆检索引擎 (FAISS封装 + 重排序)
- 向量化批处理
- 系统状态监控 (CPU/内存/窗口检测)
- 用户活动检测 (全屏/会议应用识别)

**通信方式**: Maturin/PyO3 直接绑定 (零拷贝)

---

## 3. 技术选型详解

### 3.1 主开发语言: Python 3.12+

**选型理由**:

| 维度 | 评估 |
|------|------|
| **AI生态** | ★★★★★ 最完善的AI/ML库生态，LangChain、OpenAI SDK、Sentence-Transformers等 |
| **开发效率** | ★★★★★ 快速迭代，适合原型开发和功能验证 |
| **GUI支持** | ★★★★☆ PySide6提供完整Qt6绑定 |
| **跨平台** | ★★★★☆ 良好的跨平台能力 |
| **性能** | ★★★☆☆ 计算密集任务需要Rust辅助 |

**版本选择: Python 3.12.12**

- 当前稳定版本，支持最新语言特性
- 类型提示增强 (PEP 695 Type Parameter Syntax)
- 性能提升约5-10%
- 更好的错误消息
- 与主流库的兼容性良好

**包管理工具: uv**

- 极快的依赖解析和安装速度 (比pip快10-100x)
- 内置虚拟环境管理
- 兼容pip和pyproject.toml
- Rust编写，跨平台
- Astral团队维护 (ruff同一团队)

```toml
# pyproject.toml 配置示例
[project]
name = "rainze"
version = "0.1.0"
requires-python = ">=3.12"

[tool.uv]
package = true
dev-dependencies = [
    "pytest>=8.0",
    "ruff>=0.8",
    "mypy>=1.13",
]
```

### 3.2 性能层: Rust

**选型理由**:

| 维度 | 评估 |
|------|------|
| **性能** | ★★★★★ 原生编译，无GC，接近C++性能 |
| **安全性** | ★★★★★ 内存安全、线程安全 |
| **Python互操作** | ★★★★★ PyO3提供零拷贝绑定 |
| **并发** | ★★★★★ async/await + tokio生态 |
| **学习曲线** | ★★☆☆☆ 相对陡峭 |

**版本选择: Rust 1.92.0**

- 当前最新稳定版本 (2025年12月发布)
- 完善的async生态
- 成熟的错误处理模式

**Rust模块职责**:

```rust
// rainze_core/src/lib.rs (伪代码示例)
use pyo3::prelude::*;

#[pymodule]
fn rainze_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(search_memories, m)?)?;
    m.add_function(wrap_pyfunction!(get_system_status, m)?)?;
    m.add_function(wrap_pyfunction!(detect_user_activity, m)?)?;
    m.add_function(wrap_pyfunction!(batch_vectorize, m)?)?;
    Ok(())
}
```

**构建工具: Maturin**

- 专为Rust Python扩展设计
- 自动处理ABI兼容性
- 支持pyo3和rust-cpython
- 简化CI/CD流程

```toml
# Cargo.toml
[package]
name = "rainze_core"
version = "0.1.0"
edition = "2024"

[lib]
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.23", features = ["extension-module"] }
faiss = "0.12"
sysinfo = "0.32"
tokio = { version = "1", features = ["full"] }
rayon = "1.10"  # 并行计算
```

### 3.3 GUI框架: PySide6 (Qt6)

**备选方案对比**:

| 框架 | 透明窗口 | 动画性能 | 打包体积 | 开发效率 | 社区活跃度 |
|------|----------|----------|----------|----------|------------|
| **PySide6** | ★★★★★ | ★★★★★ | ★★★☆☆ (50MB+) | ★★★★☆ | ★★★★☆ |
| PyQt6 | ★★★★★ | ★★★★★ | ★★★☆☆ | ★★★★☆ | ★★★★☆ |
| Tauri | ★★★★☆ | ★★★★☆ | ★★★★★ (5MB) | ★★★☆☆ | ★★★★★ |
| Electron | ★★★★☆ | ★★★☆☆ | ★☆☆☆☆ (150MB+) | ★★★★★ | ★★★★★ |
| Tkinter | ★★☆☆☆ | ★★☆☆☆ | ★★★★★ (内置) | ★★★☆☆ | ★★★☆☆ |

**选择PySide6的理由**:

1. **透明窗口支持**: Qt6原生支持透明窗口、无边框窗口，桌宠必需
2. **动画性能**: QPropertyAnimation + QStateMachine 提供流畅动画
3. **成熟稳定**: Qt6.x版本稳定，大量生产案例
4. **官方维护**: 由Qt公司官方维护，LGPL许可
5. **Python生态兼容**: 与asyncio、numpy等无缝集成

**关键技术点**:

```python
# 透明窗口配置示例
from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Qt

class PetWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 无边框 + 透明背景 + 始终置顶
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 启用鼠标穿透(可选区域)
        # self.setAttribute(Qt.WA_TransparentForMouseEvents)
```

### 3.4 存储方案: FAISS + SQLite

**备选方案对比**:

| 方案 | 内存占用 | 启动速度 | 部署复杂度 | 适用场景 |
|------|----------|----------|------------|----------|
| **FAISS + SQLite** | ~10MB/万条 | <1秒 | 纯文件，零配置 | ✅ 单用户桌面应用 |
| ChromaDB | ~200-400MB常驻 | 3-5秒 | 需启动服务 | 多用户/服务端 |
| LanceDB | ~50-100MB | 1-2秒 | 纯文件，较轻 | 中等规模 |
| Qdrant | ~300MB+ | 5秒+ | 需Docker/服务 | 生产级服务端 |
| Milvus | ~500MB+ | 10秒+ | 分布式，重型 | 大规模向量搜索 |

**选择FAISS + SQLite的理由**:

1. **单用户场景匹配**: 无需分布式/多租户能力
2. **启动体验**: 用户期望应用秒开，一体化数据库服务化架构拖慢启动
3. **内存敏感**: 桌宠应该是轻量应用，常驻内存 <100MB
4. **成熟稳定**:
   - FAISS: Meta开源的工业级向量搜索库
   - SQLite: 最广泛部署的嵌入式数据库
5. **离线友好**: 纯文件存储，便于备份/迁移，无需额外进程

**FAISS索引选择**:

| 索引类型 | 适用规模 | 精度 | 速度 | 内存 |
|----------|----------|------|------|------|
| **IndexFlatIP** | <10k | 100% | 较慢 | O(n) |
| **IndexIVFFlat** | 10k-100k | ~95% | 快 | O(n) + 聚类 |
| IndexHNSW | >100k | ~90% | 极快 | O(n×M) |

**推荐策略**:

- 记忆数 <10,000: 使用 `IndexFlatIP` (精确搜索)
- 记忆数 ≥10,000: 切换为 `IndexIVFFlat` (近似搜索)

**SQLite增强**:

- **FTS5**: 全文搜索，支持中文分词
- **SQLCipher** (可选): AES-256加密

```python
# 混合检索示例
async def hybrid_search(query: str, top_k: int = 5):
    # 1. FTS5关键词搜索
    fts_results = await fts5_search(query, limit=15)
    
    # 2. FAISS向量搜索
    query_vector = await embed(query)
    faiss_results = await faiss_search(query_vector, limit=20)
    
    # 3. 合并去重 + 重排序
    combined = merge_results(fts_results, faiss_results)
    return rerank(combined, top_k)
```

### 3.5 LLM集成策略

**云端LLM为主**:

| 模型 | 用途 | 优势 | 成本 |
|------|------|------|------|
| **Claude claude-sonnet-4-20250514** | 主模型 | 高质量对话、指令遵循强 | ~$3/1M tokens |
| GPT-4o-mini | 备选/轻量任务 | 快速、便宜 | ~$0.15/1M tokens |
| text-embedding-3-small | 向量化 | 768维，效果好 | ~$0.02/1M tokens |

**本地LLM作为可选插件**:

| 模型 | 参数量 | 量化 | 内存 | 适用场景 |
|------|--------|------|------|----------|
| Qwen2-1.5B | 1.5B | Q4_K_M | ~1GB | 离线应急 |
| Llama-3.2-1B | 1B | Q4_K_M | ~800MB | 轻量设备 |

**降级链设计**:

```
Tier3 (LLM生成) → Response Cache → Local LLM (插件) 
                → Tier2 (规则生成) → Tier1 (模板) → 预设兜底
```

### 3.6 打包分发: PyInstaller / Nuitka

**备选方案对比**:

| 工具 | 打包体积 | 启动速度 | 反编译难度 | 兼容性 |
|------|----------|----------|------------|--------|
| **PyInstaller** | ~80-150MB | 3-5秒 | 低 | ★★★★★ |
| **Nuitka** | ~50-100MB | 1-3秒 | 高 | ★★★★☆ |
| cx_Freeze | ~70-120MB | 3-5秒 | 低 | ★★★☆☆ |
| PyOxidizer | ~60-100MB | 2-4秒 | 中 | ★★★☆☆ |

**推荐策略**:

- **开发阶段**: PyInstaller (快速打包，调试方便)
- **生产发布**: Nuitka (编译优化，启动更快，代码保护更好)

```bash
# PyInstaller 打包命令
pyinstaller --onefile --windowed \
    --add-data "assets;assets" \
    --add-data "config;config" \
    --icon=assets/icon.ico \
    rainze.py

# Nuitka 打包命令
nuitka --standalone --onefile \
    --enable-plugin=pyside6 \
    --windows-disable-console \
    --windows-icon-from-ico=assets/icon.ico \
    --include-data-dir=assets=assets \
    --include-data-dir=config=config \
    rainze.py
```

---

## 4. 核心模块技术方案

### 4.1 记忆系统

**3层记忆架构**:

| 层级 | 名称 | 存储位置 | 用途 | TTL |
|------|------|----------|------|-----|
| Layer 1 | Identity Layer | 文件 | 角色设定、用户档案 | 永久 |
| Layer 2 | Working Memory | 内存 | 会话上下文、实时状态 | Session |
| Layer 3 | Long-term Memory | SQLite + FAISS | Facts/Episodes/Relations | 动态衰减 |

**记忆写入流程**:

```
对话结束 → 重要度评估 → 写入SQLite → 加入向量化队列 → 后台Worker处理 → 更新FAISS索引
```

**向量化策略**:

- **全异步**: 不阻塞主流程
- **优先级队列**: 重要记忆优先处理
- **批量处理**: 每次处理10条，间隔60秒
- **回退机制**: 向量化失败不影响FTS5检索

### 4.2 Prompt构建系统

**增量式构建 + Token预算管理**:

| 模式 | 总预算 | 适用场景 |
|------|--------|----------|
| Lite | 16k | 新用户、快速响应 |
| Standard | 32k | 日常陪伴 (默认) |
| Deep | 64k | 深度对话、复杂任务 |

**记忆索引策略**:

- 检索Top 30相关记忆
- 仅显示索引 (ID + 时间 + 20字摘要)
- 全文注入Top 3最相关记忆
- 支持按需展开 `[RECALL:#mem_xxx]`

### 4.3 响应生成策略

**3层响应Tier**:

| Tier | 名称 | 适用场景 | 延迟 | 成本 |
|------|------|----------|------|------|
| Tier 1 | 模板响应 | 点击、拖拽、简单反馈 | <50ms | 0 |
| Tier 2 | 规则生成 | 整点报时、系统警告 | <100ms | 0 |
| Tier 3 | LLM生成 | 自由对话、情感分析 | 500-2000ms | API费用 |

**场景分类规则**:

```python
def classify_scene(event) -> SceneType:
    if event.type in ["click", "drag", "hover"]:
        return SceneType.SIMPLE  # → Tier 1
    elif event.type in ["hourly_chime", "system_warning"]:
        return SceneType.MEDIUM  # → Tier 2
    else:
        return SceneType.COMPLEX  # → Tier 3
```

### 4.4 动画系统

**5层动画架构**:

| 层级 | 内容 | 更新频率 |
|------|------|----------|
| Layer 0 | 基础 (角色主体) | 换装时 |
| Layer 1 | 待机 (呼吸、微动) | 持续循环 |
| Layer 2 | 表情 (眼睛、嘴巴) | emotion_tag变化时 |
| Layer 3 | 动作 (挥手、跳跃) | 事件触发 |
| Layer 4 | 特效 (星星、爱心) | 情绪强烈时 |
| Layer 5 | 口型 (TTS同步) | 说话时 |

**动画与AI解耦**:

- 文本显示与动画并行处理
- 立即播放"思考中"动画
- 收到emotion_tag后切换表情
- 支持动画叠加

### 4.5 插件系统

**插件架构设计**:

```python
# 插件接口定义
class PluginInterface(Protocol):
    name: str
    version: str
    
    def on_load(self) -> None: ...
    def on_unload(self) -> None: ...
    def on_event(self, event: Event) -> Optional[Response]: ...
```

**插件隔离**:

- 独立Python进程 (可选)
- 权限声明机制
- 沙箱执行环境

---

## 5. 性能与可靠性

### 5.1 性能指标

| 指标 | 目标值 | 测量方法 |
|------|--------|----------|
| 应用启动时间 | <3秒 | 冷启动到窗口可见 |
| 常驻内存 | <100MB | 空闲状态 |
| Tier 1响应 | <50ms | 模板响应延迟 |
| Tier 2响应 | <100ms | 规则生成延迟 |
| Tier 3响应 | <2秒 | LLM生成延迟 (P95) |
| 记忆检索 | <200ms | 混合检索延迟 |
| 向量化 | <500ms/条 | 单条记忆向量化 |

### 5.2 可靠性设计

**降级策略**:

1. API超时 → Response Cache
2. Cache未命中 → Local LLM (如安装)
3. Local LLM不可用 → 规则生成
4. 规则失败 → 预设兜底

**错误恢复**:

- 指数退避重试 (500ms → 1s → 2s)
- 状态回滚机制
- 错误监控告警

### 5.3 可观测性

**追踪系统**:

- 每次交互生成trace_id
- 每个操作生成span_id
- 记录执行时间、状态、元数据

**监控指标**:

- API延迟、错误率
- 内存使用、缓存命中率
- 每日Token消耗

**日志管理**:

- 滚动保留7天
- 按级别分类 (DEBUG/INFO/WARN/ERROR)
- 支持日报生成

---

## 6. 安全与隐私

### 6.1 隐私保护

**PII检测与脱敏**:

- 正则匹配: 手机号、邮箱、身份证、银行卡
- NER识别: 地址、姓名、公司名
- 处理: 存储和API发送前脱敏

**数据加密** (可选):

- SQLCipher AES-256加密
- 密钥本地存储或用户自定义

### 6.2 API安全

**密钥管理**:

- 环境变量存储
- 不在代码中硬编码
- 支持多API密钥轮换

**请求安全**:

- HTTPS强制
- 请求速率限制
- 异常请求监控

---

## 7. 开发与部署

### 7.1 开发环境

```bash
# 环境初始化
uv venv
uv pip install -e ".[dev]"

# Rust模块编译
cd rainze_core
maturin develop

# 运行测试
pytest tests/
ruff check src/
mypy src/
```

### 7.2 目录结构

```
rainze/
├── src/
│   └── rainze/
│       ├── __init__.py
│       ├── main.py              # 入口
│       ├── gui/                 # PySide6 GUI
│       ├── core/                # 核心逻辑
│       │   ├── context.py       # 上下文管理
│       │   ├── memory.py        # 记忆系统
│       │   ├── prompt.py        # Prompt构建
│       │   ├── generation.py    # 响应生成
│       │   └── state.py         # 状态系统
│       ├── tools/               # 工具调用
│       ├── plugins/             # 插件系统
│       └── utils/               # 工具函数
├── rainze_core/                 # Rust模块
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs
│       ├── memory_search.rs
│       ├── system_monitor.rs
│       └── vectorize.rs
├── config/                      # 配置文件
├── assets/                      # 资源文件
├── data/                        # 数据目录
├── tests/                       # 测试
├── pyproject.toml
└── README.md
```

### 7.3 CI/CD

```yaml
# .github/workflows/build.yml
name: Build

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --all-extras
      - run: uv run pytest
      - run: uv run ruff check
      - run: uv run mypy src/

  build:
    needs: test
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - uses: dtolnay/rust-toolchain@stable
      - run: uv sync
      - run: cd rainze_core && maturin build --release
      - run: uv run nuitka ...
```

---

## 8. 风险评估

### 8.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| LLM API不稳定 | 高 | 中 | 多层降级策略、Response Cache |
| Rust/Python互操作复杂 | 中 | 中 | 充分测试、简化接口 |
| 内存占用超标 | 中 | 低 | 性能监控、惰性加载 |
| 打包体积过大 | 低 | 中 | Nuitka优化、资源压缩 |

### 8.2 依赖风险

| 依赖 | 风险 | 替代方案 |
|------|------|----------|
| PySide6 | 低 (Qt官方) | PyQt6 |
| FAISS | 低 (Meta维护) | Hnswlib |
| OpenAI API | 中 (商业服务) | 多API Provider支持 |
| uv | 低 (Astral维护) | pip + venv |

---

## 9. 未来扩展

### 9.1 短期计划 (v1.x)

- 完善核心对话功能
- 实现基础工具调用
- 优化启动性能

### 9.2 中期计划 (v2.x)

- 多语言支持 (英语、日语)
- 跨平台支持 (macOS, Linux)
- 语音交互 (TTS/STT)

### 9.3 长期愿景

- 本地LLM深度集成
- 多角色切换
- 社区插件生态

---

## 10. 参考资源

### 10.1 官方文档

- [PySide6 Documentation](https://doc.qt.io/qtforpython-6/)
- [PyO3 User Guide](https://pyo3.rs/)
- [FAISS Wiki](https://github.com/facebookresearch/faiss/wiki)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Anthropic API Reference](https://docs.anthropic.com/)

### 10.2 相关项目

- [LangChain](https://github.com/langchain-ai/langchain)
- [Sentence Transformers](https://www.sbert.net/)
- [Maturin](https://github.com/PyO3/maturin)

---

## 附录

### A. 配置文件清单

| 文件 | 用途 |
|------|------|
| `config/api_settings.json` | API配置 (LLM Provider、密钥、模型选择) |
| `config/memory_settings.json` | 记忆系统配置 (检索策略、向量化、生命周期) |
| `config/generation_settings.json` | 响应生成配置 (Tier分层、降级链、缓存) |
| `config/context_manager_settings.json` | 统一上下文管理器配置 |
| `config/conversation_settings.json` | 对话系统配置 (会话管理、情绪推断) |
| `config/prompt_templates.json` | Prompt模板配置 (场景指令、输出格式) |
| `config/animation_settings.json` | 动画系统配置 |
| `config/state_settings.json` | 状态系统配置 (心情、能量、饥饿度、好感度) |
| `config/proactivity_settings.json` | 主动行为配置 (免打扰、频率控制) |
| `config/behavior_plan_settings.json` | 行为计划配置 |
| `config/tool_settings.json` | 工具调用配置 |
| `config/privacy_settings.json` | 隐私设置 (PII检测、脱敏规则) |
| `config/observability_settings.json` | 可观测性配置 (日志、追踪、指标) |
| `data/system_prompt.txt` | 角色系统提示词 |
| `data/master_profile.json` | 用户档案 |

### B. 核心依赖版本

```toml
[project]
dependencies = [
    # GUI框架
    "pyside6>=6.8",
    
    # HTTP客户端
    "httpx>=0.28",
    
    # LLM SDK
    "openai>=1.58",
    "anthropic>=0.40",
    
    # 向量化与检索
    "sentence-transformers>=3.3",
    "faiss-cpu>=1.9",
    
    # 数据库与ORM
    "sqlalchemy>=2.0",
    
    # 数据验证
    "pydantic>=2.10",
    "pydantic-settings>=2.7",
    
    # 日志与调试
    "structlog>=24.4",
    "rich>=13.9",
    
    # 中文分词 (用于实体词检测)
    "jieba>=0.42",
    
    # 异步支持
    "anyio>=4.7",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "ruff>=0.8",
    "mypy>=1.13",
    "pre-commit>=4.0",
]
```

### C. 与PRD关键章节对应关系

| PRD章节 | 技术报告对应 | 说明 |
|---------|-------------|------|
| 0.2 记忆层次架构 | 3.4 存储方案 + 4.1 记忆系统 | 3层记忆模型实现 |
| 0.3 混合响应策略 | 4.3 响应生成策略 | Tier1/2/3分层 |
| 0.4 混合存储系统 | 3.4 存储方案 | FAISS + SQLite |
| 0.5 Prompt构建 | 4.2 Prompt构建系统 | 增量式 + 索引式 |
| 0.5a 统一上下文管理器 | 4.3 响应生成策略 | UCM架构 |
| 0.6 降级链 | 3.5 LLM集成 + 5.2 可靠性 | Fallback 1-5 |
| 0.6a 状态系统 | 4.1 状态定义 | 轻度养成机制 |
| 0.7 Agent自主循环 | 4.3 响应生成策略 | Workflow vs Agent |

---

**文档版本历史**:

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0.0 | 2025-12-29 | 初始版本 |
| v1.0.1 | 2025-12-29 | 技术审核：修正Rust edition、补充配置文件清单、完善依赖说明 |
