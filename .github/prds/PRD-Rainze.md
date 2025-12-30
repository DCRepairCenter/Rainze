# Rainze - AI桌面宠物 产品需求文档 (PRD)

> **版本**: v3.1.0
> **日期**: 2025-12-30
> **文档类型**: Interface Flow 结构化需求

---

## Task Definition

```
Task Definition:
|-- Goal: 构建一个AI驱动的桌面宠物应用，支持交互、陪伴、效率工具等场景
|-- Core Philosophy: AI生成为主，配置为辅，预设文本仅作紧急兜底
|-- Constraints:
|    |-- 第一部分功能：本地逻辑运行，AI生成内容
|    \-- 第二部分功能：需配置环境，依赖API
\-- Output Specification:
     |-- Tone: Technical + Casual (面向开发者与用户)
     |-- Format: Interface Flow 结构化文档
     \-- Detail Level: In-depth
```

**核心设计原则**:

```
配置文件 = 参数说明书
AI生成 = 主要方式 (正常场景)
规则生成 = 降级方案 (API暂时不可用时)
预设文本 = 最后手段 (以下情况触发):
          a. API回复过慢/无响应/报错
          b. API回复截断 (内容不完整)
          c. 网络断开 (完全离线)
```

---

# 第零部分：AI驱动核心架构

> **核心理念**: 这是一个**云端AI驱动**的桌面宠物，依赖云端LLM提供智能交互能力，配置文件只存储参数和规则，文本内容由AI实时生成，预设文本仅作兜底使用
> **设计哲学**: 让AI理解上下文并生成个性化内容，而非从JSON中读取死板的预设文本
> **技术定位**: 云端优先，本地LLM仅作为可选的离线应急插件

---

## 0.0 技术选型说明 (Tech Stack Justification)

> **本节说明**: 记录关键技术决策的理由，避免后续开发者质疑或重复讨论

### 开发框架

| 技术 | 选型 | 理由 |
|------|------|------|
| **主语言** | Python 3.10+ | 生态丰富，AI库完善，开发效率高 |
| **性能层** | Rust (Maturin/PyO3) | 性能关键路径用Rust实现，通过PyO3暴露给Python |
| **GUI框架** | PySide6 (Qt6) | 跨平台、性能好、支持透明窗口、动画流畅 |
| **打包工具** | PyInstaller / Nuitka | 支持单文件分发，用户无需安装Python |

### 混合架构说明 (Rust + Python)

```
[Hybrid Architecture]
|
|-- Python层 (业务逻辑 + AI调用):
|    |-- GUI渲染 (PySide6)
|    |-- LLM API调用与Prompt构建
|    |-- 插件系统与配置管理
|    \-- 用户交互处理
|
|-- Rust层 (性能关键路径):
|    |-- 记忆检索引擎 (FAISS封装 + 重排序)
|    |-- 向量化批处理
|    |-- 系统状态监控 (CPU/内存/窗口检测)
|    \-- 用户活动检测 (全屏/会议应用识别)
|
\-- 通信方式: Maturin/PyO3 直接绑定 (零拷贝)
```

**为什么用Rust处理这些模块?**

1. **记忆检索**: 涉及大量向量计算和重排序，Rust可显著降低延迟
2. **系统监控**: 需要频繁调用系统API，Rust更高效且无GIL限制
3. **用户检测**: 实时检测全屏/会议状态，需要低延迟响应
4. **批处理**: 向量化操作天然适合Rust的并行能力

### 存储方案：FAISS + SQLite vs 一体化向量数据库

**最终选择**: FAISS + SQLite 混合存储

**为什么不用 ChromaDB / LanceDB / Qdrant?**

| 方案 | 内存占用 | 启动速度 | 部署复杂度 | 适用场景 |
|------|----------|----------|------------|----------|
| **FAISS + SQLite** | ~10MB/万条 | <1秒 | 纯文件，零配置 | 单用户桌面应用 |
| ChromaDB | ~200-400MB常驻 | 3-5秒 | 需启动服务 | 多用户/服务端 |
| LanceDB | ~50-100MB | 1-2秒 | 纯文件，较轻 | 中等规模 |
| Qdrant | ~300MB+ | 5秒+ | 需Docker/服务 | 生产级服务端 |

**关键决策依据**:

1. **桌面宠物是单用户场景**: 无需分布式/多租户能力，一体化数据库过于重型
2. **启动体验优先**: 用户期望应用秒开，ChromaDB的服务化架构会拖慢启动
3. **内存敏感**: 桌宠应该是轻量应用，常驻内存应<100MB，ChromaDB基础占用已超标
4. **成熟稳定**: FAISS是Meta开源的工业级库，SQLite是最广泛部署的嵌入式数据库
5. **离线友好**: 纯文件存储，便于备份/迁移，无需额外进程

**FAISS注意事项**:

- FAISS索引需要序列化/反序列化（已在启动/关闭时处理）
- 使用`IndexFlatIP`(小规模)或`IndexIVFFlat`(大规模)索引类型
- 索引与SQLite记录通过ID映射关联

### LLM调用策略：云端为主

**核心定位**: 这是一个**云端AI驱动**的桌面宠物

| 模式 | 定位 | 说明 |
|------|------|------|
| **云端LLM** | 主要方式 | 提供高质量响应 |
| **Response Cache** | 降级方案1 | 复用历史高质量响应 |
| **本地LLM** | 可选插件 | 离线应急，非核心依赖 |
| **规则生成** | 降级方案2 | API不可用时的规则模板 |
| **预设文本** | 最后手段 | 完全离线时的兜底 |

**为什么不以本地LLM为主?**

1. **用户体验**: 本地小模型(1-3B)质量远不如云端大模型，桌宠核心价值在于智能陪伴
2. **硬件门槛**: 运行本地LLM需要较好的CPU/GPU，会劝退大量用户
3. **包体积**: 量化后的小模型仍需1-2GB，影响分发
4. **API额度充足**: 有大量免费额度，无需过度优化成本

---

## 0.1 设计原则对比

| 维度 | ❌ 错误设计 (预设文本) | ✅ 正确设计  |
|------|---------------------|---------------------|
| **交互响应** | `"response": "这个苹果真甜！"` | `"attributes": {"taste": "sweet"}` → AI生成个性化响应 |
| **时间问候** | `"06-11": "早安~"` | AI根据时间+用户状态+历史生成独特问候 |
| **系统警告** | `"messages": ["CPU快冒烟了"]` | AI根据CPU占用率+当前任务生成贴切吐槽 |
| **事件生成** | 预设事件库随机抽取 | AI根据上下文创造全新事件 |
| **配置作用** | 存储台词剧本 | 存储参数、规则、属性描述 |

**核心区别示例** - 喂食响应:

```json
// ❌ 错误：预设文本
{
  "apple": {
    "response_template": "这个苹果真甜！"  // 永远重复同一句话
  }
}

// ✅ 正确：AI驱动
{
  "apple": {
    "attributes": {
      "taste": "sweet",
      "texture": "crisp",
      "temperature": "cool"
    }
  }
}
→ AI根据属性+心情+时间生成：
  - "哇！这个苹果好甜好脆！谢谢主人~"
  - "嘎嘣脆的苹果！正好解渴呢！"
  - "唔...虽然有点凉，但是很好吃！"
```

---

### 0.2 记忆层次架构 (Memory Hierarchy)

> **设计理念**: 简化的3层记忆模型，边界清晰，易于实现和维护
> **改进说明**: 原5层架构存在Episodic/Semantic边界模糊问题，Environmental本质是实时感知而非记忆

```
[Memory Architecture - 3层简化模型]
|
|-- Layer 1: Identity Layer (身份层) ⭐ 不可变
|    |-- 存储: ./config/system_prompt.txt + ./data/master_profile.json
|    |-- 内容:
|    |    |-- 角色基础设定、性格、说话风格、行为准则
|    |    \-- 用户昵称、生日、对宠物的称呼、关系设定
|    |-- 注入: 始终注入，优先级最高
|    |-- 更新: 仅用户主动修改
|    \-- TTL: 永久
|
|-- Layer 2: Working Memory (工作记忆) ⭐ 会话级
|    |-- 存储: 内存 (RAM)
|    |-- 内容:
|    |    |-- 当前会话上下文 (最近K轮对话，K可配置)
|    |    |-- 实时状态 (心情、能量、饥饿度、好感度)
|    |    |-- 当前事件上下文 (事件类型、相关对象)
|    |    \-- 环境感知 (时间/天气/系统状态，按需刷新)
|    |-- 注入: 始终注入
|    |-- 更新: 每次交互实时更新
|    \-- TTL: Session结束即清空
|
\-- Layer 3: Long-term Memory (长期记忆) ⭐ 统一持久化
     |-- 存储: FAISS向量索引 + SQLite关系库
     |-- 子类型:
     |    |-- Facts (事实): 用户偏好、重要信息、长期习惯
     |    |    |-- 示例: "主人喜欢苹果"、"主人生日是10月5日"
     |    |    \-- 存储: SQLite user_facts 表
     |    |
     |    |-- Episodes (情景): 交互摘要、情感事件、重要对话
     |    |    |-- 示例: "2024-12-28 主人说工作压力大"
     |    |    |-- 存储: SQLite episodes 表 + FAISS向量索引
     |    |    \-- 检索: 语义相似度 + 时间加权
     |    |
     |    \-- Relations (关系): 实体关系图 (可选扩展)
     |         |-- 示例: 主人 -[喜欢]-> 苹果, 主人 -[讨厌]-> 加班
     |         \-- 存储: SQLite relations 表
     |
     |-- 检索策略 (Retrieval):
     |    |-- 触发条件: 用户提到"之前/上次/记得"等词，或COMPLEX场景
     |    |-- 混合检索: FTS5关键词 + FAISS向量，结果合并去重
     |    |-- 重排序: Recency(0.3) + Importance(0.3) + Similarity(0.4)
     |    \-- 阈值门控: score < 0.65 视为无相关记忆
     |
     |-- 遗忘策略 (Forgetting):
     |    |-- 永久保留: 好感度±10以上事件、等级提升、用户标记
     |    |-- 缓慢衰减: 情感事件 (半衰期30天)
     |    |-- 快速衰减: 日常闲聊 (半衰期7天)
     |    \-- 增强学习: 被用户纠正的记忆立即更新权重
     |
     \-- TTL: 动态衰减 + 重要度保护
```

**记忆流转机制**:

```
[Memory Flow - 简化版]
|
|-- 对话发生 → Layer 2 (Working Memory) 立即更新
|
v (对话结束)
|
|-- 重要度评估:
|    |-- 好感度变化 ≥ 5 → 高重要度 (0.8+)
|    |-- 包含关键词 (记住/喜欢/讨厌/重要) → 中重要度 (0.6+)
|    \-- 普通对话 → 低重要度 (0.3-0.5)
|
|-- 写入 Layer 3:
|    |-- 高重要度: 立即写入 + 向量化
|    |-- 中/低重要度: 批量处理 (每小时)
|    \-- 提取事实: 从对话中提取 Facts
|
v (每日空闲时)
|
|-- 记忆整合:
|    |-- 生成每日Reflection总结
|    |-- 运行遗忘策略 (衰减低重要度记忆)
|    \-- 矛盾检测 (同一对象对立描述)
```

**环境感知 (Context Sensing)** - 不再作为记忆层:

```
[Context Sensing - 实时查询]
|
|-- 触发: 每次生成Prompt前
|-- 数据源:
|    |-- 时间环境: 系统时间 (本地)
|    |-- 天气状态: 天气API (缓存30分钟)
|    |-- 系统状态: Rust模块实时检测 (CPU/内存)
|    \-- 用户活动: Rust模块检测 (全屏/会议应用)
|-- 注入: 作为Working Memory的一部分
\-- 缓存: 短TTL (1-5分钟)
```

**记忆协调器 (Memory Coordinator)**:

> **设计原则**: 3层架构使协调器更简洁，场景分类决定是否检索长期记忆

```

[Memory Coordinator - Simplified]
|
|-- 职责:
|    |-- 决定是否需要检索 Layer 3 (长期记忆)
|    |-- 控制注入到Prompt的总Token量
|    \-- 缓存管理
|
|-- 场景分类 (Scene Classification):
|    |
|    |-- SIMPLE场景 (点击/拖拽/简单反馈):
|    |    |-- 注入: Layer 1 (身份) + Layer 2 (状态部分)
|    |    |-- 跳过: Layer 3 检索
|    |    \-- 延迟: <50ms
|    |
|    |-- MEDIUM场景 (整点报时/系统警告/喂食):
|    |    |-- 注入: Layer 1 + Layer 2 (含环境感知)
|    |    |-- 可选: Layer 3 Facts摘要
|    |    |-- 跳过: Layer 3 深度检索
|    |    \-- 延迟: <200ms
|    |
|    \-- COMPLEX场景 (自由对话/情感分析):
|         |-- 注入: 全部3层
|         |-- Layer 3: 完整检索 (Facts + Episodes)
|         \-- 延迟: 500-2000ms
|
|-- 记忆检索触发器:
|    |-- 关键词检测: "之前/上次/记得/你说过" → 强制检索
|    |-- 场景类型: COMPLEX → 自动检索
|    |-- 话题相似度: 与近期对话相似度<0.3 → 可能需要背景
|    \-- 其他: 跳过检索，节省延迟
|
|-- Token预算分配 (见0.5节详细配置):
|    |-- 支持三种模式: 轻量(16k) / 标准(32k) / 深度(64k)
|    |-- Layer 1 (身份): 1500-4000 tokens (随模式变化)
|    |-- Layer 2 (工作记忆): 4000-16000 tokens (可压缩)
|    |-- Layer 3 (长期记忆): 3000-16000 tokens (按需检索)
|    |-- 环境感知: 500-2000 tokens
|    \-- 总预算: 用户可在设置中选择模式
|
\-- 配置 (memory_settings.json):
     {
       "scene_layer_mapping": {
         "SIMPLE": ["layer1", "layer2_state"],
         "MEDIUM": ["layer1", "layer2", "layer3_facts_summary"],
         "COMPLEX": ["layer1", "layer2", "layer3_full"]
       },
       "token_budgets": {
         "layer1": 1500, "layer2": 2500, "layer3": 3000,
         "context": 500, "total": 10000
       },
       "retrieval_trigger_keywords": ["之前", "上次", "记得", "你说过", "以前"],
       "cache_ttl_seconds": {
         "layer3_facts": 600,
         "layer3_retrieval": 300,
         "context": 60
       }
     }

```

**Prompt注入示例** (整点报时场景 - MEDIUM):

```

{Layer 1: Identity}
[角色] 你是一只活泼的猫娘桌宠，名叫忆雨之岚，小名岚仔，英文名 Rainze，性格开朗，喜欢用"喵~"结尾。
[用户] 昵称: 海棠, 关系: 主人, 生日: 10-05

{Layer 2: Working Memory}
[状态] 好感度75(亲密), 心情Happy, 能量60%, 饥饿度30%
[环境] 22:00 周五, 天气晴朗, CPU 35%
[事件] 整点报时触发

{Layer 3: Long-term Memory - Facts摘要}
[用户画像] 作息不规律，经常熬夜工作，喜欢喝咖啡

{指令} 用简短俏皮的话问候用户，结合时间和你对他的了解

```

---

### 0.3 混合响应策略 (Hybrid Response Strategy)

> **设计理念**: 批判性使用AI能力，高频简单场景用模板保证即时响应，复杂场景才调用LLM保持个性化
> **核心原则**: 单步可完成的操作用Workflow，多步推理才用Agent模式

```

[Hybrid Response Strategy - 场景分类优先]
|
|-- Step 0: 场景分类 (Scene Classification)
|    |-- 目的: 在调用LLM前先判断场景复杂度
|    |-- 分类器: 规则匹配 (无API调用)
|    |-- 分类结果 (默认映射，可在配置中覆盖):
|    |    |-- SIMPLE: 高频简单交互 → 默认Tier 1 模板响应
|    |    |-- MEDIUM: 中等复杂度 → 默认Tier 2 规则生成
|    |    \-- COMPLEX: 需要上下文理解 → 默认Tier 3 LLM生成
|    |-- 配置覆盖: 用户可在各功能配置文件中指定响应Tier
|    \-- 配置: scene_classification_rules (可自定义)
|
|-- Tier 1: 模板响应 (Template Response) - 简单即时交互
|    |-- 适用场景:
|    |    |-- 点击反馈 (单击、双击、拖动)
|    |    |-- 简单状态变化 (被抓起、放下)
|    |    |-- 高频UI交互 (打开菜单、关闭窗口)
|    |    \-- 确认类操作 (保存成功、删除确认)
|    |-- 响应方式: 模板 + 变量填充 + 随机变体
|    |-- 延迟: <50ms
|    |-- 成本: 0 (无API调用)
|    \-- 个性化: 通过模板变体池保持新鲜感
|
|-- Tier 2: 规则生成 (Rule-Based Generation) - 状态驱动场景
|    |-- 适用场景:
|    |    |-- 整点报时 (时间+状态组合)
|    |    |-- 系统监控警告 (CPU/内存+阈值)
|    |    |-- 状态驱动事件 (能量低、饥饿)
|    |    \-- 简单条件响应 (天气评论、游戏模式切换)
|    |-- 响应方式: 规则引擎 + 状态变量 + 条件分支
|    |-- 延迟: 50-100ms
|    |-- 成本: 0 (无API调用)
|    \-- 个性化: 通过状态组合产生变化
|
|-- Tier 3: LLM生成 (AI Generation) - 需要上下文理解的场景
|    |-- 适用场景:
|    |    |-- 自由对话 (用户主动聊天)
|    |    |-- 情感分析响应 (需要理解用户情绪)
|    |    |-- 复杂事件 (随机剧情、多轮互动)
|    |    |-- 记忆相关 (需要检索历史上下文)
|    |    \-- 创造性内容 (观察日记、个性化建议)
|    |-- 响应方式: 构建Prompt → 调用LLM → 返回生成内容
|    |-- 延迟: 500-2000ms (可配置超时)
|    |-- 成本: API调用费用
|    \-- 个性化: 最高，完全上下文感知
|
\-- 降级链 (Fallback Chain): ⭐ 详见0.6节完整定义
     |-- Tier 3失败 (超时/报错/截断) → 尝试Response Cache
     |-- Cache未命中 → 尝试Local LLM (如已安装插件)
     |-- Local LLM不可用 → 降级到Tier 2规则生成
     |-- 规则生成失败 → 降级到Tier 1模板
     \-- 全部失败 → 预设兜底文本
     |-- 📌 注: 本节为概述，完整Fallback 1-5链及配置见0.6节

```

**场景分类规则** (可配置):

```

[Scene Classification Rules]
|
|-- SIMPLE场景识别 (正则/关键词匹配):
|    |-- interaction_type in ["click", "drag", "hover", "release"]
|    |-- event_type in ["ui_feedback", "state_change_simple"]
|    |-- message_length < 5 (极短输入)
|    \-- is_confirmation == true
|
|-- MEDIUM场景识别:
|    |-- event_type in ["hourly_chime", "system_warning", "weather_update"]
|    |-- has_clear_trigger == true (明确触发条件)
|    |-- requires_memory_lookup == false
|    \-- emotion_analysis_needed == false
|
\-- COMPLEX场景识别 (默认):
     |-- is_free_conversation == true
     |-- requires_memory_lookup == true
     |-- emotion_analysis_needed == true
     |-- is_creative_content == true
     \-- multi_turn_interaction == true

```

**配置文件** (`./config/generation_settings.json`):

```json
{
  "default_strategy": "ai_generation",
  "ai_generation": {
    "timeout_seconds": 5,
    "retry_attempts": 2,
    "model": "gpt-4o-mini",
    "temperature": 0.8,
    "max_tokens": 150
  },
  "template_generation": {
    "enable": true,
    "use_on_api_failure": true,
    "templates_path": "./config/generation_templates.json"
  },
  "fallback_messages": {
    "enable": true,
    "use_only_when": "complete_api_failure",
    "messages_path": "./config/fallback_messages.json"
  },
  "cache": {
    "enable_response_cache": true,
    "cache_duration_minutes": 5,
    "max_cache_entries": 100
  }
}
```

---

### 0.4 混合存储系统 (Hybrid Storage)

> **设计**: FAISS + SQLite 轻量化方案，更适合桌面应用

```
[Hybrid Storage Architecture]
|
|-- Hot Storage (热数据层) - SQLite + FTS5
|    |-- 文件: ./data/memory.db
|    |-- 存储内容:
|    |    |-- 最近30天对话记录
|    |    |-- 用户偏好结构化数据
|    |    |-- 行为模式统计
|    |    \-- 记忆元数据 (重要度、访问次数、标签)
|    |-- 查询方式: SQL + 全文搜索 (FTS5)
|    |-- 优势: 快速关系查询、支持复杂筛选
|    \-- 加密: SQLCipher可选加密
|
|-- Vector Index (向量索引层) - FAISS
|    |-- 文件: ./data/memory.faiss + ./data/memory_ids.pkl
|    |-- 存储内容:
|    |    |-- 对话摘要向量 (768维)
|    |    \-- 向量ID → SQLite记录映射
|    |-- 索引类型: IndexFlatIP (小规模) / IndexIVFFlat (大规模)
|    |-- 优势: 本地运行、无需服务器、快速相似度搜索
|    \-- 内存占用: ~10MB per 10000条记忆
|
\-- Archive Storage (归档层) - JSON
     |-- 文件: ./data/archive/{year}/{month}.json
     |-- 存储内容:
     |    |-- 超过30天的历史记录
     |    \-- 压缩后的对话摘要
     |-- 同步: 可选云端备份 (用户配置)
     \-- 用途: 数据导出、迁移、恢复
```

**记忆数据结构**:

```
[Memory Schema - SQLite]
|
|-- Table: memories
|    |-- id: TEXT PRIMARY KEY (UUID)
|    |-- created_at: TIMESTAMP
|    |-- updated_at: TIMESTAMP
|    |-- content: TEXT (记忆摘要)
|    |-- memory_type: TEXT (conversation/event/preference/fact)
|    |-- importance: REAL (0-1, LLM评分或规则计算)
|    |-- access_count: INTEGER (访问次数)
|    |-- last_accessed: TIMESTAMP
|    |-- decay_factor: REAL (衰减因子)
|    |-- tags: TEXT (JSON数组)
|    |-- metadata: TEXT (JSON对象)
|    \-- is_archived: BOOLEAN
|
|-- Table: user_preferences
|    |-- key: TEXT PRIMARY KEY
|    |-- value: TEXT
|    |-- confidence: REAL (0-1)
|    |-- source_memory_ids: TEXT (JSON数组)
|    \-- updated_at: TIMESTAMP
|
\-- Table: behavior_patterns
     |-- pattern_type: TEXT (activity_time/interaction_freq/topic_interest)
     |-- pattern_data: TEXT (JSON)
     |-- sample_count: INTEGER
     \-- last_updated: TIMESTAMP
```

**检索策略 (Retrieval Strategy)** - 智能混合检索:

```
[Multi-Strategy Retrieval - Smart Hybrid]
|
|-- 设计原则:
|    |-- 智能选择: 根据query类型自动选择最优检索策略
|    |-- FTS5+向量并行: 同时启用时取长补短
|    |-- 异步向量化: 记忆立即保存文本，向量化后台执行
|    \-- 注意力管理: 避免检索过多记忆稀释上下文
|
v (Query输入)
|
|-- Step 0: 时间窗口推断 (Time Window Inference)
|    |-- 关键词规则匹配:
|    |    |-- "刚才"/"刚刚" → 1小时内
|    |    |-- "今天" → 当天
|    |    |-- "昨天" → 24-48小时
|    |    |-- "最近"/"这几天" → 3天内
|    |    |-- "上次"/"之前" → 7天内
|    |    |-- "以前"/"很久" → 30天内
|    |    \-- 无时间指代 → 不限制
|    \-- 输出: time_window (start, end) 或 None
|
|-- Step 0.5: 检索策略智能选择 (Strategy Selection)
|    |-- 实体词检测: 使用NER或规则提取query中的实体词
|    |    |-- 实体类型: 人名、地名、物品名、时间词、专有名词
|    |    |-- 检测方法: 正则匹配 + 词性标注 (jieba/分词器)
|    |-- 策略决策:
|    |    |-- has_entity_words == true → FTS5_PRIMARY (关键词检索优先)
|    |    |    |-- 示例: "我之前说过喜欢苹果" → 提取"苹果" → FTS5检索
|    |    |-- has_entity_words == false → VECTOR_PRIMARY (语义检索优先)
|    |    |    |-- 示例: "我之前提到过最喜欢的那个东西" → 无明确实体 → 向量检索
|    |    \-- enable_parallel == true → PARALLEL (并行检索+结果合并)
|    \-- 输出: strategy_mode (FTS5_PRIMARY / VECTOR_PRIMARY / PARALLEL)
|
|-- Step 1: FTS5全文检索 (当strategy需要时)
|    |-- 条件: strategy_mode in [FTS5_PRIMARY, PARALLEL]
|    |-- 提取query中的关键词/实体词
|    |-- SQLite FTS5搜索memories.content
|    |-- 应用时间窗口过滤
|    |-- 返回: Top N候选 (N=retrieval.fts5_top_k, 默认15)
|    \-- 延迟: <50ms
|
|-- Step 2: 向量检索 (当strategy需要时)
|    |-- 条件: strategy_mode in [VECTOR_PRIMARY, PARALLEL] AND faiss_index存在
|    |-- 生成query embedding
|    |-- 检索Top N候选 (N=retrieval.vector_top_k, 默认20)
|    |-- 当PARALLEL模式: 与FTS5结果合并去重
|    |-- ⭐ 回退机制: 若向量检索结果 < min_vector_results (默认3):
|    |    |-- 自动补充FTS5检索结果
|    |    \-- 原因: 新记忆可能尚未向量化，避免漏检
|    \-- 返回: [(memory_id, similarity_score), ...]
|
|-- Step 3: 元数据重排序 (Re-ranking)
|    |-- 时间加权: recency_score = exp(-days_ago / recency_decay_days)
|    |-- 重要度加权: importance * importance_weight
|    |-- 访问频率: log(access_count + 1) * frequency_weight
|    |-- 综合评分: 权重可配置 (retrieval.weights)
|    \-- 取Top N候选 (N=retrieval.final_top_k, 默认5)
|
|-- Step 4: 阈值门控 (Threshold Gating)
|    |-- 过滤: 仅保留 final_score > similarity_threshold 的结果
|    |-- 如果全部低于阈值:
|    |    |-- 标记 no_relevant_memory = true
|    |    \-- AI生成时注入系统提示 (见memory_settings.json的no_memory_prompt)
|    \-- 输出: 有效记忆列表 (0-N条, N=retrieval.max_return)
|
|-- Step 5: 语义记忆补充 (SQLite)
|    |-- 查询相关用户偏好
|    |-- 查询匹配的行为模式
|    \-- 注入到上下文
|
\-- 输出: 结构化记忆列表 + 用户画像摘要 + no_relevant_memory标志
```

**异步向量化机制** - 全异步统一流程 ⭐ 改进:

```
[Async Vectorization Pipeline - Unified Async]
|
|-- 设计理念:
|    |-- 记忆立即可用: 文本写入SQLite后立即可通过FTS5检索
|    |-- 全异步向量化: 所有记忆统一异步处理，消除任何阻塞
|    |-- 优先级队列: 重要记忆在队列中优先处理，但不阻塞主流程
|    |-- 容错设计: 向量化失败不影响FTS5检索，回退机制保证检索完整性
|    \-- 关闭安全: 程序关闭时保存待处理队列
|
|-- 写入流程 (统一异步):
|    |-- Step 1: 记忆文本写入SQLite (is_vectorized=false)
|    |-- Step 2: 加入向量化队列 (按重要度排序)
|    |    |-- importance >= 0.7: 加入高优先级队列头部
|    |    \-- importance < 0.7: 加入普通队列尾部
|    |-- Step 3: 立即返回成功 (零阻塞)
|    \-- Step 4: 后台Worker按优先级异步处理
|
|-- 后台Worker (统一处理所有记忆):
|    |-- 触发条件:
|    |    |-- 高优先级队列非空时: 立即处理 (无需等待批量)
|    |    |-- 普通队列: 队列长度 >= batch_size (default: 10)
|    |    |-- 普通队列: 距离上次处理 >= process_interval_seconds (default: 60)
|    |    \-- 程序空闲时 (idle_trigger): 处理所有待处理记忆
|    |-- 处理顺序: 高优先级队列 > 普通队列
|    |-- 批量处理: 一次处理N条 (N=embedding.batch_size)
|    |-- 写入FAISS索引 + 更新is_vectorized=true
|    \-- 失败重试: retry_count < max_retries时重新入队
|
|-- 程序关闭时:
|    |-- 保存未处理队列到 ./data/pending_vectorization.json
|    |-- 下次启动时加载并继续处理
|    \-- 最坏情况: 部分低重要度记忆仅可FTS5检索，不影响核心功能
|
\-- 健康检查:
     |-- 周期性检查未向量化记忆数量
     |-- 超过阈值时日志警告
     \-- 提供手动触发向量化的接口
```

**记忆生命周期管理** - 改进版:

```
[Memory Lifecycle - Enhanced]
|
|-- 创建 (Creation):
|    |-- 重要事件: 立即创建 + 向量化 (importance >= 0.7)
|    |-- 普通对话: 批量处理 (每小时汇总)
|    \-- 自动评分: 规则评分 (好感度变化/关键词) 或 LLM评分
|
|-- 整合 (Consolidation) - 用户空闲时执行:
|    |-- ❌ 禁止自动合并记忆 (避免矛盾信息合并导致人格崩溃)
|    |-- ✅ 矛盾检测 (Conflict Detection):
|    |    |-- 规则检测: 同一对象的对立描述
|    |    |    |-- 模式: "[实体] + 喜欢/讨厌/爱/恨"
|    |    |    |-- 检测: 24小时内是否有矛盾记录
|    |    |    \-- 示例: "海棠喜欢苹果" vs "海棠讨厌苹果"
|    |    |-- 冲突处理:
|    |    |    |-- 标记为 conflict_flag = true
|    |    |    |-- 保留双方原始记忆 (不删除)
|    |    |    \-- 生成Reflection记录变化
|    |-- ✅ 生成Reflection (而非合并):
|    |    |-- 类型: observation (观察性总结)
|    |    |-- 内容: 总结模式但不修改原始记忆
|    |    \-- 示例: "主人最近对苹果的态度似乎有变化"
|    |-- 提取长期事实 → user_preferences表
|    |-- 更新行为模式 → behavior_patterns表
|    \-- 生成每日摘要
|
|-- 衰减 (Decay):
|    |-- 每日更新: decay_factor *= 0.98
|    |-- 访问时重置: decay_factor = 1.0
|    \-- 衰减后重要度: effective_importance = importance * decay_factor
|
\-- 归档 (Archival) - 动态阈值机制:
     |-- ⭐ 动态阈值计算 (而非固定值):
     |    |-- archive_threshold = percentile(all_effective_importance, 20)
     |    |-- 即: 保留重要度Top 80%的记忆，归档Bottom 20%
     |    |-- 优势: 自适应不同用户的记忆密度
     |    \-- 最小阈值: 0.1 (避免过度归档)
     |-- 归档条件:
     |    |-- effective_importance < archive_threshold
     |    |-- AND access_count < 2
     |    |-- AND age > 30天
     |    \-- AND 不是用户主动标记的重要记忆
     |-- 操作: 移动到archive表，从FAISS索引删除
     \-- 可恢复: 用户可手动恢复归档记忆
```

**矛盾检测规则** (Conflict Detection Rules):

```
[Conflict Detection]
|
|-- 对立词对 (Antonym Pairs):
|    |-- 喜欢 ↔ 讨厌/不喜欢
|    |-- 爱 ↔ 恨
|    |-- 想要 ↔ 不想要
|    |-- 喜欢吃 ↔ 不吃/不能吃
|    |-- 擅长 ↔ 不擅长
|    \-- 经常 ↔ 从不
|
|-- 检测流程:
|    |-- Step 1: 提取记忆中的 (实体, 态度, 对象) 三元组
|    |-- Step 2: 查找同一实体+对象的其他记忆
|    |-- Step 3: 比较态度是否对立
|    \-- Step 4: 标记冲突或生成Reflection
|
|-- 冲突处理策略:
|    |-- 时间优先: 最新记忆权重更高
|    |-- 上下文保留: 记录态度变化的时间线
|    |-- 生成观察: "[实体]对[对象]的态度从[旧态度]变为[新态度]"
|    \-- 查询时: 优先返回最新态度，但保留历史供追溯
```

**配置文件** (`./config/memory_settings.json`) - 增强版:

```json
{
  "storage": {
    "db_path": "./data/memory.db",
    "faiss_index_path": "./data/memory.faiss",
    "archive_path": "./data/archive/",
    "enable_encryption": false,
    "encryption_key_env": "RAINZE_DB_KEY"
  },
  
  "embedding": {
    "model": "text-embedding-3-small",
    "dimension": 768,
    "batch_size": 32,
    "local_fallback": "sentence-transformers/all-MiniLM-L6-v2"
  },
  
  "retrieval": {
    "strategy_selection": {
      "enable_smart_selection": true,
      "_note": "当enable_smart_selection=true时，系统根据实体词自动选择策略，fallback_strategy仅在无法判断时使用",
      "fallback_strategy": "PARALLEL",
      "strategies": {
        "FTS5_PRIMARY": "有明确实体词时优先使用关键词检索",
        "VECTOR_PRIMARY": "无明确实体词时优先使用语义检索",
        "PARALLEL": "同时使用两种检索并合并结果(智能选择无法判断时的回退策略)"
      },
      "entity_detection": {
        "use_ner": false,
        "use_jieba_pos": true,
        "entity_pos_tags": ["n", "nr", "ns", "nt", "nz", "vn"],
        "min_entity_length": 2
      }
    },
    "enable_vector_search": true,
    "fts5_top_k": 15,
    "vector_top_k": 20,
    "final_top_k": 5,
    "max_return": 5,
    "similarity_threshold": 0.65,
    "enable_threshold_gating": true,
    "recency_decay_days": 7,
    "vector_fallback": {
      "enable": true,
      "min_vector_results": 3,
      "fallback_to_fts5": true,
      "reason": "新记忆可能尚未向量化，自动补充FTS5结果避免漏检"
    },
    "weights": {
      "similarity": 0.4,
      "recency": 0.3,
      "importance": 0.2,
      "frequency": 0.1
    },
    "time_window_rules": {
      "刚才|刚刚": {"hours": 1},
      "今天": {"hours": 24},
      "昨天": {"hours_range": [24, 48]},
      "最近|这几天": {"days": 3},
      "上次|之前": {"days": 7},
      "以前|很久": {"days": 30}
    },
    "no_memory_prompt": "[系统提示: 未找到相关记忆，请坦诚告知用户你不记得，并询问更多细节，不要编造虚假记忆]"
  },
  
  "async_vectorization": {
    "enable": true,
    "mode": "unified_async",
    "high_priority_threshold": 0.7,
    "high_priority_immediate_process": true,
    "batch_size": 10,
    "process_interval_seconds": 60,
    "idle_trigger": true,
    "max_retries": 3,
    "pending_queue_path": "./data/pending_vectorization.json",
    "health_check_interval_minutes": 30,
    "warning_threshold_pending": 100
  },
  
  "lifecycle": {
    "consolidation_hour": 3,
    "decay_rate": 0.98,
    "archive_threshold_days": 30,
    "archive_strategy": "dynamic_percentile",
    "archive_percentile": 20,
    "archive_min_threshold": 0.1,
    "max_memories": 50000,
    "enable_auto_merge": false,
    "enable_conflict_detection": true,
    "generate_reflection_on_conflict": true
  },
  
  "conflict_detection": {
    "enable": true,
    "antonym_pairs": [
      ["喜欢", "讨厌"],
      ["喜欢", "不喜欢"],
      ["爱", "恨"],
      ["想要", "不想要"],
      ["擅长", "不擅长"],
      ["经常", "从不"]
    ],
    "conflict_window_hours": 168,
    "resolution_strategy": "keep_both_generate_reflection"
  },
  
  "importance_rules": {
    "affinity_change_threshold": 5,
    "level_up_importance": 0.95,
    "keyword_boost": ["生日", "重要", "记住", "喜欢", "讨厌"],
    "default_importance": 0.5
  }
}
```

---

### 0.5 AI提示词构建流程 (增量式 + 索引式)

> **性能优化**: 采用增量式构建 + TTL缓存，避免重复I/O和向量检索
> **注意力优化**: 采用记忆索引策略，解决长上下文注意力稀疏问题

```
[Incremental Prompt Builder]
|
|-- Static Context (静态上下文) - 启动时加载一次
|    |-- Layer 1: Identity Layer
|    |    |-- system_prompt.txt
|    |    \-- master_profile.json
|    |-- 缓存策略: 内存常驻，文件变更时热重载
|    \-- 刷新触发: 用户手动保存设置
|
|-- Semi-Static Context (半静态上下文) - 状态变化时刷新
|    |-- Layer 3: Long-term Memory (Facts子类型)
|    |    |-- 用户偏好摘要
|    |    \-- 行为模式摘要
|    |-- 缓存策略: TTL 10分钟
|    \-- 刷新触发: 记忆整合后 / 偏好变化时
|
|-- Dynamic Context (动态上下文) - 每次生成时刷新
|    |-- Layer 2: Working Memory
|    |    |-- 当前会话对话
|    |    |-- 实时状态
|    |    \-- 环境感知 (时间、天气、系统状态、用户活动)
|    \-- 刷新策略: 每次生成前必刷新
|
\-- Cached Retrieval (缓存检索) - 相似查询复用
     |-- Layer 3: Long-term Memory (Episodes子类型)
     |-- 缓存键: hash(event_type + context_keywords)
     |-- 缓存策略: TTL 5分钟，相似事件复用
     \-- 命中率预期: 20-30% (重复场景)
```

**记忆索引策略 (Memory Index Strategy)**:

> **设计理念**: 解决长上下文注意力稀疏问题。不直接注入大量记忆内容，而是提供索引列表，让LLM按需请求展开。

```
[Memory Index Approach]
|
|-- 问题: 长上下文 (128k+) 容易导致注意力稀疏
|    |-- 大量无关记忆分散模型注意力
|    |-- 关键信息被淹没在冗长上下文中
|    \-- Token成本高但效果不成比例
|
|-- 解决方案: 索引式检索
|    |
|    |-- Step 1: 生成记忆索引列表 (~2-3k tokens)
|    |    |-- 检索Top N相关记忆 (N=prompt.memory_index_count, 默认30)
|    |    |-- 每条只显示: ID + 时间 + 摘要(20字) + 重要度
|    |    \-- 示例:
|    |         #mem_001 [3天前] 工作压力大想休息 (重要度0.8)
|    |         #mem_042 [上周] 喜欢玩原神 (重要度0.6)
|    |         #mem_103 [昨天] 讨论了周末出游计划 (重要度0.9)
|    |
|    |-- Step 2: 初次注入索引 + 高优先级记忆全文
|    |    |-- 索引列表: 全部N条摘要
|    |    |-- 全文注入: 仅Top M最相关记忆 (M=prompt.memory_fulltext_count, 默认3)
|    |    \-- Token预算: 可配置 (prompt.token_budget)
|    |
|    |-- Step 3: 按需展开机制 (可选)
|    |    |-- LLM可输出: [RECALL:#mem_042]
|    |    |-- 系统返回该记忆完整内容
|    |    |-- LLM继续生成回复
|    |    \-- 适用于: 复杂对话需要多跳推理
|    |
|    \-- Step 4: 注意力聚焦
|         |-- 核心上下文保持精简 (~8k tokens)
|         |-- 索引提供广度，全文提供深度
|         \-- 避免注意力稀疏
```

**Prompt结构示例 (索引模式)**:

```
{Layer 1: Identity Layer} (~1k tokens)
[角色设定、性格、说话风格]

{Layer 2: Working Memory} (~2k tokens)
[当前会话最近10轮对话]
[实时状态: 心情、能量]
[环境感知: 时间、天气、系统状态]

{Layer 3: Long-term Memory - 索引} (~2k tokens)
[可用记忆索引]
1. #mem_001 [3天前] 关于工作压力的对话 (重要度0.8) ⭐
2. #mem_042 [上周] 讨论游戏攻略 (重要度0.6)
3. #mem_103 [昨天] 周末出游计划 (重要度0.9) ⭐
... (共30条)

{Layer 3: Long-term Memory - Facts摘要} (~1k tokens)
[用户偏好关键词列表]
[行为模式摘要]

{高优先级记忆全文} (~2k tokens)
[#mem_001 完整内容]
[#mem_103 完整内容]

{系统指令}
- 如需更多记忆细节，可输出 [RECALL:#mem_xxx]
- 如果索引中没有相关记忆，坦诚告知用户你不记得

{当前事件}
[用户输入 / 触发事件]
```

**Token预算分配** (所有数值均可配置):

```
[Token Budget - 动态调整 + 用户模式选择]
|
|-- 用户可选模式 (User Selectable Modes):
|    |
|    |-- 轻量模式 (Lite Mode): 16k总预算
|    |    |-- 适用: 新用户、低配设备、快速响应需求
|    |    |-- 特点: 响应更快，API成本更低
|    |    |-- 牺牲: 记忆深度有限
|    |    \-- 配置键: prompt.mode = "lite"
|    |
|    |-- 标准模式 (Standard Mode): 32k总预算 (默认)
|    |    |-- 适用: 大多数用户、日常陪伴
|    |    |-- 特点: 平衡响应速度与记忆深度
|    |    \-- 配置键: prompt.mode = "standard"
|    |
|    \-- 深度模式 (Deep Mode): 64k总预算
|         |-- 适用: 老用户、深度对话、复杂任务
|         |-- 特点: 更多记忆上下文，更深度的理解
|         |-- 代价: 响应稍慢，API成本更高
|         \-- 配置键: prompt.mode = "deep"
|
|-- 动态预算调整 (根据记忆总量自动调整):
|    |-- memory_count < 100 (新用户):
|    |    |-- 减少 memory_index_tokens (无需大量索引)
|    |    \-- 增加 working_memory_tokens (更多对话历史)
|    |-- memory_count 100-1000: 使用标准配置
|    \-- memory_count > 1000 (老用户):
|         |-- 增加 memory_index_tokens
|         \-- 自动建议切换深度模式
|
|-- 轻量模式预算 (16k):
|    |-- Core Identity: 1500 | Working Memory: 4000
|    |-- Environment: 500 | Semantic Summary: 1500
|    |-- Memory Index: 1500 | Memory Full-text: 1500
|    \-- Instructions: 500 | Reserved Output: 5000
|
|-- 标准模式预算 (32k):
|    |-- Core Identity: 2500 | Working Memory: 8000
|    |-- Environment: 1000 | Semantic Summary: 2500
|    |-- Memory Index: 3000 | Memory Full-text: 5000
|    \-- Instructions: 1000 | Reserved Output: 9000
|
|-- 深度模式预算 (64k):
|    |-- Core Identity: 4000 | Working Memory: 16000
|    |-- Environment: 2000 | Semantic Summary: 4000
|    |-- Memory Index: 6000 | Memory Full-text: 10000
|    \-- Instructions: 2000 | Reserved Output: 20000

[扩展模式 - 超长对话/复杂任务]
|-- 可扩展至 prompt.extended_budget (默认128000)
|-- 增加更多记忆全文 (prompt.extended_fulltext_count, 默认20)
|-- 增加会话历史深度 (prompt.extended_history_turns, 默认30)
|-- 增加记忆索引数量 (prompt.extended_index_count, 默认200)
\-- 适用于: 深度情感对话、复杂多步任务、长期记忆追溯
```

**构建流程**:

```
[Prompt Assembly Pipeline]
|
v (事件触发)
|
|-- Step 1: 检查静态上下文缓存
|    |-- 命中 → 直接使用
|    \-- 未命中/过期 → 重新加载
|
|-- Step 2: 检查状态变化
|    |-- if state_hash != cached_state_hash:
|    |    \-- 刷新 Layer 2 Working Memory
|    \-- else: 复用缓存状态
|
|-- Step 3: 刷新环境层 (必执行)
|    |-- 获取当前时间
|    |-- 检查天气缓存 (TTL=cache.weather_ttl_minutes, 默认30)
|    \-- 获取系统状态
|
|-- Step 4: 记忆检索 (智能缓存)
|    |-- cache_key = f"{event.type}_{hash(event.keywords)}"
|    |-- if cache_key in retrieval_cache:
|    |    \-- 复用缓存结果
|    |-- else:
|    |    |-- 执行FTS5/FAISS检索 + 重排序
|    |    \-- 写入缓存 (TTL=cache.retrieval_ttl_minutes, 默认5)
|
|-- Step 5: 组装Prompt
|    |-- 按Layer优先级拼接
|    |-- Token预算检查 (max prompt.total_budget, 默认64000)
|    \-- 必要时压缩低优先级内容
|
v (发送到LLM)
|
|-- Step 6: 后处理
|    |-- 长度检查
|    |-- 敏感词过滤 (PII检测)
|    |-- 情感标签提取 (用于动画)
|    \-- 响应缓存 (可选)
|
\-- 输出: {text, emotion_tag, animation_hint}
```

---

### 0.5a 统一上下文管理器 (Unified Context Manager)

> **核心理念**: 所有交互（对话、游戏、工具、插件）都经过统一入口，确保状态一致性和记忆完整性
> **设计目标**: 避免"游戏中的对话不被记住"、"插件状态与主程序不同步"等问题

```
[Unified Context Manager - 统一入口架构]
|
|-- 设计原则:
|    |-- 单一入口: 所有用户交互必须经过 ContextManager
|    |-- 状态同步: 任何模块的状态变化都实时同步到全局状态
|    |-- 记忆一致: 游戏/插件/工具产生的交互同样写入记忆系统
|    |-- 上下文共享: 所有模块共享同一套用户画像和情绪状态
|    \-- 响应统一: 无论来源，都通过 0.3 混合响应策略生成回复
|
|-- 架构图:
|    |
|    |    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
|    |    │  用户对话   │  │  游戏/插件  │  │  系统事件   │
|    |    └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
|    |           │                │                │
|    |           v                v                v
|    |    ┌─────────────────────────────────────────────┐
|    |    │       Unified Context Manager (UCM)         │
|    |    │  ┌─────────┐ ┌─────────┐ ┌─────────────┐    │
|    |    │  │意图识别 │→│上下文   │→│ 响应策略    │    │
|    |    │  │Intent   │ │Assembly │ │ Tier1/2/3   │    │
|    |    │  └─────────┘ └─────────┘ └─────────────┘    │
|    |    └──────────────────┬──────────────────────────┘
|    |                       │
|    |           ┌───────────┼───────────┐
|    |           v           v           v
|    |    ┌──────────┐ ┌──────────┐ ┌──────────┐
|    |    │ 状态更新 │ │ 记忆写入 │ │ 响应输出 │
|    |    └──────────┘ └──────────┘ └──────────┘
|
|-- 交互类型注册表 (Interaction Type Registry):
|    |
|    |-- CONVERSATION: 用户主动对话
|    |    |-- 来源: 聊天输入框
|    |    |-- 响应策略: Tier 3 (LLM生成)
|    |    |-- 记忆写入: 完整对话记录
|    |    \-- 状态影响: 可能改变心情/好感度
|    |
|    |-- GAME_INTERACTION: 游戏内交互
|    |    |-- 来源: 猜拳、骰子、其他小游戏
|    |    |-- 响应策略: Tier 2/3 (可配置，默认Tier3 AI生成)
|    |    |    |-- Tier 2: 规则生成 (快速响应，适合高频游戏)
|    |    |    \-- Tier 3: AI生成 (个性化反应，适合重要时刻)
|    |    |-- 策略选择: 由插件配置或根据连胜/连败/特殊情况动态切换
|    |    |-- 记忆写入: 游戏结果摘要 (重要度较低)
|    |    \-- 状态影响: 金币、好感度变化
|    |
|    |-- TOOL_EXECUTION: 工具执行
|    |    |-- 来源: 文件整理、启动器、提醒等
|    |    |-- 响应策略: Tier 2/3 (根据复杂度)
|    |    |-- 记忆写入: 执行结果摘要
|    |    \-- 状态影响: 可能触发成就/奖励
|    |
|    |-- PLUGIN_ACTION: 插件行为
|    |    |-- 来源: 第三方插件
|    |    |-- 响应策略: 由插件指定，默认Tier 2
|    |    |-- 记忆写入: 通过插件API决定
|    |    \-- 状态影响: 插件声明的影响
|    |
|    |-- SYSTEM_EVENT: 系统事件
|    |    |-- 来源: 整点报时、状态警告、随机事件
|    |    |-- 响应策略: Tier 2/3 (根据事件类型)
|    |    |-- 记忆写入: 重要事件记录
|    |    \-- 状态影响: 根据事件定义
|    |
|    \-- PASSIVE_TRIGGER: 被动触发
|         |-- 来源: 点击、拖拽、抚摸
|         |-- 响应策略: Tier 1 (模板响应)
|         |-- 记忆写入: 不写入 (高频低重要度)
|         \-- 状态影响: 轻微好感度变化
|
|-- 上下文组装流程 (Context Assembly):
|    |
|    v (交互事件到达)
|    |
|    |-- Step 1: 交互类型识别
|    |    |-- 根据事件来源判断类型
|    |    |-- 查找对应的处理策略
|    |    \-- 输出: InteractionType + Metadata
|    |
|    |-- Step 2: 意图识别 (仅CONVERSATION类型)
|    |    |-- 规则匹配: 关键词/正则检测
|    |    |    |-- "玩游戏/猜拳/骰子" → 游戏意图
|    |    |    |-- "提醒我/记住/设置" → 工具意图
|    |    |    |-- "打开/启动/运行" → 启动器意图
|    |    |    \-- 其他 → 自由对话意图
|    |    |-- 输出: Intent + Confidence
|    |    \-- 低置信度时: 直接作为自由对话处理
|    |
|    |-- Step 3: 上下文加载 (复用0.5节流程)
|    |    |-- 静态上下文 (缓存)
|    |    |-- 动态上下文 (实时)
|    |    |-- 记忆检索 (按需)
|    |    \-- 特殊上下文 (游戏/插件提供的额外信息)
|    |
|    |-- Step 4: 响应生成
|    |    |-- 根据InteractionType选择Tier
|    |    |-- 构建完整Prompt
|    |    |-- 调用响应策略
|    |    \-- 输出: Response + Emotion + Actions
|    |
|    \-- Step 5: 后处理与状态更新
|         |-- 记忆写入 (根据类型决定是否写入)
|         |-- 状态更新 (好感度、金币、能量等)
|         |-- 动画触发
|         \-- 事件广播 (通知其他模块)
```

**记忆写入策略**:

```
[Memory Write Policy]
|
|-- 写入级别定义:
|    |-- FULL: 完整记录 (对话全文 + 元数据)
|    |-- SUMMARY: 摘要记录 (仅关键信息)
|    |-- RESULT_ONLY: 仅结果 (如游戏输赢)
|    \-- NONE: 不记录 (高频低价值交互)
|
|-- 各类型默认策略:
|    |-- CONVERSATION → FULL (重要度由内容决定)
|    |-- GAME_INTERACTION → RESULT_ONLY (重要度0.3)
|    |-- TOOL_EXECUTION → SUMMARY (重要度0.5)
|    |-- PLUGIN_ACTION → 插件指定，默认SUMMARY
|    |-- SYSTEM_EVENT → SUMMARY (重要度由事件类型决定)
|    \-- PASSIVE_TRIGGER → NONE
|
\-- 记忆聚合:
     |-- 连续游戏: 聚合为"今天和主人玩了N局猜拳，赢了M局"
     |-- 重复工具: 聚合为"今天帮主人整理了N次文件"
     \-- 避免: 大量低价值记忆稀释重要记忆
```

**配置文件** (`./config/context_manager_settings.json`):

```json
{
  "unified_entry": {
    "enable": true,
    "log_all_interactions": false,
    "interaction_timeout_ms": 30000
  },
  
  "intent_recognition": {
    "enable": true,
    "confidence_threshold": 0.6,
    "keywords": {
      "game": ["玩游戏", "猜拳", "骰子", "来一局", "玩一下"],
      "tool": ["提醒我", "记住", "设置", "帮我记", "别让我忘"],
      "launcher": ["打开", "启动", "运行", "帮我开"],
      "query": ["查一下", "搜索", "天气", "几点了"]
    },
    "fallback_to_conversation": true
  },
  
  "memory_write_policy": {
    "CONVERSATION": {"level": "FULL", "default_importance": 0.6},
    "GAME_INTERACTION": {"level": "RESULT_ONLY", "default_importance": 0.3},
    "TOOL_EXECUTION": {"level": "SUMMARY", "default_importance": 0.5},
    "PLUGIN_ACTION": {"level": "SUMMARY", "default_importance": 0.4},
    "SYSTEM_EVENT": {"level": "SUMMARY", "default_importance": 0.5},
    "PASSIVE_TRIGGER": {"level": "NONE", "default_importance": 0}
  },
  
  "memory_aggregation": {
    "enable": true,
    "aggregate_window_hours": 24,
    "min_count_to_aggregate": 3,
    "aggregation_templates": {
      "game": "今天和主人玩了{count}局{game_name}，赢了{win_count}局",
      "tool": "今天帮主人{action}了{count}次"
    }
  },
  
  "state_sync": {
    "broadcast_state_changes": true,
    "sync_interval_ms": 100,
    "conflict_resolution": "latest_wins"
  }
}
```

---

### 0.5b 用户主动对话场景 (User-Initiated Conversation)

> **核心场景**: 这是桌宠最重要的使用场景 - 用户主动发起聊天
> **设计目标**: 提供完整的提示词管理机制，支持多轮对话和意图理解

```
[User-Initiated Conversation Flow]
|
|-- 触发方式:
|    |-- 点击聊天气泡/输入框
|    |-- 快捷键呼出 (可配置)
|    |-- 语音唤醒 (如已启用)
|    \-- 直接输入文字
|
v (用户输入到达)
|
|-- Step 1: 预处理
|    |-- 输入清洗 (去除首尾空白)
|    |-- 长度检查 (超长输入截断警告)
|    |-- 敏感词初筛 (快速规则匹配)
|    \-- 输出: cleaned_input
|
|-- Step 2: 意图识别 (Intent Recognition)
|    |-- 优先级1: 指令检测
|    |    |-- 以"/"开头 → 隐藏指令 (如/dance, /debug)
|    |    \-- 直接执行，不走对话流程
|    |-- 优先级2: 工具/游戏意图
|    |    |-- 关键词匹配 → 路由到对应模块
|    |    |-- 但仍生成AI响应作为过渡
|    |-- 优先级3: 自由对话
|    |    \-- 默认路径，完整AI生成
|    \-- 输出: {intent, confidence, route}
|
|-- Step 3: 对话上下文构建
|    |
|    |-- 3.1 会话历史管理
|    |    |-- 获取当前会话最近N轮对话 (N=conversation_history_turns)
|    |    |-- 格式: [{role: "user"/"assistant", content: "...", timestamp}]
|    |    |-- 压缩策略: 超过Token限制时，优先压缩早期轮次
|    |    \-- 会话边界: 超过session_timeout_minutes视为新会话
|    |
|    |-- 3.2 相关记忆检索
|    |    |-- 根据用户输入生成检索query
|    |    |-- 执行向量+FTS5混合检索
|    |    |-- 应用阈值门控 (见0.4节)
|    |    \-- 输出: relevant_memories[]
|    |
|    |-- 3.3 用户情绪推断
|    |    |-- 规则检测: 标点符号、大小写、emoji
|    |    |-- 关键词检测: 负面词汇、求助信号
|    |    |-- 输出: inferred_user_mood (用于调整回复语气)
|    |    \-- 注入: 作为上下文提示给LLM
|    |
|    \-- 3.4 组装完整上下文
|         |-- 复用0.5节的Tier分层结构
|         \-- 添加: 当前用户输入 + 推断情绪
|
|-- Step 4: Prompt构建 (对话专用模板)
|    |-- 见下方完整示例
|
|-- Step 5: LLM调用与后处理
|    |-- 调用API (Tier 3策略)
|    |-- 解析情感标签 [EMOTION:tag:intensity]
|    |-- 长度检查与截断处理
|    |-- 更新会话历史
|    \-- 触发动画/音效
|
\-- Step 6: 记忆写入
     |-- 用户输入 + AI回复 → 写入Working Memory
     |-- 重要对话 → 异步写入Episodic Memory
     \-- 提取偏好 → 更新Semantic Memory
```

**对话专用Prompt模板**:

```
[Conversation Prompt Template]

{Layer 1: Identity Layer} ────────────────────────────
[系统角色]
{system_prompt内容}

[用户档案]
称呼: {master_profile.nickname}
关系: {master_profile.relationship}
生日: {master_profile.birthday}
对我的称呼: {master_profile.call_me}

{Layer 2: Working Memory} ────────────────────────────
[当前状态]
好感度: {affinity} ({affinity_level_name})
心情: {mood} | 能量: {energy}% | 饥饿度: {hunger}%

[环境信息]
当前时间: {current_time} {day_of_week}
天气: {weather_description}
系统状态: CPU {cpu}%, 内存 {memory}%
用户活动: {user_activity_hint}

[会话历史]
{conversation_history - 最近N轮，格式如下}
[用户] {user_message_1}
[你] {assistant_response_1}
[用户] {user_message_2}
[你] {assistant_response_2}
...

{Layer 3: Long-term Memory} ────────────────────────────
[相关记忆] (共检索到{memory_count}条，展示最相关的{display_count}条)
{如果 no_relevant_memory == true:}
[系统提示] 未找到与当前话题相关的记忆，如果用户询问过去的事，请坦诚表示不记得，不要编造。

{否则:}
1. [{memory_1.time_ago}] {memory_1.summary} (重要度{memory_1.importance})
2. [{memory_2.time_ago}] {memory_2.summary} (重要度{memory_2.importance})
...

[用户画像]
- 偏好: {preferences_summary}
- 习惯: {habits_summary}
- 近期关注: {recent_topics}

{推断信息} ────────────────────────────
[用户情绪推断]
根据输入分析，用户当前可能: {inferred_user_mood}
{如果检测到负面情绪:}
{prompt_templates.mood_hints.negative_mood}

{回复指令} ────────────────────────────
{prompt_templates.response_instructions.conversation.instruction}

{prompt_templates.response_instructions.conversation.requirements}

{输出格式要求} ────────────────────────────
{prompt_templates.output_format}

[当前用户输入]
{user_input}
```

**多轮对话管理**:

```
[Multi-Turn Conversation Management]
|
|-- 会话定义:
|    |-- 新会话触发条件:
|    |    |-- 距上次对话超过 session_timeout_minutes (默认120分钟)
|    |    |-- 用户手动"清空对话"
|    |    \-- 程序重启
|    |-- 会话内: 保持完整对话历史
|    \-- 跨会话: 仅保留记忆摘要
|
|-- 对话历史压缩策略:
|    |-- Token超限时启动压缩
|    |-- 压缩优先级 (从低到高):
|    |    |-- 1. 早期轮次的完整内容 → 摘要
|    |    |-- 2. 中间轮次保留关键句
|    |    |-- 3. 最近3轮始终保留完整
|    |    \-- 4. 当前轮始终保留完整
|    |-- 压缩示例:
|    |    |-- 原始: "[用户] 今天工作好累啊 [你] 辛苦了，要不要休息一下？"
|    |    \-- 压缩后: "[早期对话摘要: 用户表达工作疲惫，你表示关心]"
|    \-- 配置: history_compression_threshold_tokens
|
|-- 话题追踪:
|    |-- 当前话题: 通过关键词提取
|    |-- 话题切换检测: 余弦相似度 < 0.3 视为切换
|    |-- 话题切换时: 可触发"换个话题"类的过渡语
|    \-- 用途: 帮助AI理解对话流向
```

**配置文件** (`./config/conversation_settings.json`):

```json
{
  "input_processing": {
    "max_input_length": 500,
    "truncate_warning": "你说的太多了，我记不住啦...",
    "enable_sensitive_filter": true
  },
  
  "intent_recognition": {
    "command_prefix": "/",
    "enable_keyword_routing": true,
    "low_confidence_threshold": 0.4
  },
  
  "session_management": {
    "session_timeout_minutes": 120,
    "max_history_turns": 20,
    "history_compression_threshold_tokens": 4000,
    "always_keep_recent_turns": 3
  },
  
  "user_mood_inference": {
    "enable": true,
    "negative_keywords": ["累", "烦", "难过", "生气", "无聊", "孤独", "压力"],
    "positive_keywords": ["开心", "高兴", "哈哈", "太好了", "喜欢"],
    "urgency_indicators": ["!", "！", "急", "快", "马上"],
    "inject_mood_hint": true
  },
  
  "response_generation": {
    "max_response_length": 150,
    "temperature": 0.8,
    "enable_emotion_tag": true,
    "emotion_tag_format": "[EMOTION:{tag}:{intensity}]"
  },
  
  "memory_integration": {
    "enable_memory_retrieval": true,
    "max_memories_in_prompt": 5,
    "memory_time_format": "relative",
    "no_memory_behavior": "honest_admission"
  },
  
  "topic_tracking": {
    "enable": true,
    "switch_threshold": 0.3,
    "enable_transition_phrase": false
  }
}
```

---

### 0.5c 统一Prompt模板系统 (Unified Prompt Template System)

> **核心理念**: 所有场景的Prompt构建遵循统一的模板结构，用户可自定义回复指令和输出格式
> **设计目标**: 让用户能够根据自己桌宠的性格特点自定义响应规则

```
[Unified Prompt Template System]
|
|-- 设计原则:
|    |-- 结构统一: 所有场景都使用Layer 1-3分层结构 (Identity/Working/Long-term)
|    |-- 指令可配: 回复指令、输出格式由用户配置
|    |-- 场景适配: 每个场景有专属的上下文注入规则
|    |-- 继承机制: 场景模板可继承基础模板，仅覆盖差异部分
|    \-- 热重载: 修改配置后无需重启即可生效
|
|-- 模板层次:
|    |-- Base Template (基础模板): 所有场景共享的Layer 1-3结构
|    |-- Scene Template (场景模板): 特定场景的上下文扩展
|    |-- User Instructions (用户指令): 用户自定义的回复要求
|    \-- Output Format (输出格式): 情感标签等输出规范
|
|-- 场景模板注册表:
|    |-- CONVERSATION: 用户主动对话
|    |-- HOURLY_CHIME: 整点报时
|    |-- FOCUS_WARNING: 专注模式警告
|    |-- FOCUS_COMPLETE: 专注完成夸奖
|    |-- SYSTEM_WARNING: 系统状态警告
|    |-- FEED_RESPONSE: 喂食响应
|    |-- GAME_RESULT: 游戏结果反馈
|    |-- TOOL_COMPLETE: 工具执行完成
|    |-- IDLE_CHAT: 闲聊触发
|    |-- WAKE_UP: 睡眠唤醒
|    |-- CLIPBOARD_REACT: 剪贴板反应
|    |-- CLIPBOARD_EAT: 剪贴板"吃掉"反馈
|    |-- NETWORK_STATUS: 网络状态变化
|    |-- GAMING_MODE_EXIT: 游戏模式结束
|    |-- RANDOM_EVENT: 随机事件
|    |-- LAUNCHER: 程序启动反馈
|    |-- BOOKMARK: 网站导航语
|    \-- NOTE_RECALL: 便签回忆提醒
```

**统一Prompt构建流程**:

```
[Unified Prompt Assembly]
|
v (场景触发)
|
|-- Step 1: 加载基础模板 (Base Template)
|    |-- Layer 1: Identity Layer (从system_prompt.txt + master_profile.json)
|    |-- Layer 2: Working Memory (当前状态 + 会话历史 + 环境感知)
|    \-- Layer 3: Long-term Memory (按需检索 Facts + Episodes)
|
|-- Step 2: 注入场景上下文 (Scene Context)
|    |-- 从 prompt_templates.scene_contexts[scene_type] 加载
|    |-- 注入场景特有变量 (如游戏结果、文件整理数量等)
|    \-- 应用场景特定的记忆检索策略
|
|-- Step 3: 加载用户指令 (User Instructions)
|    |-- 基础指令: prompt_templates.base_instructions
|    |-- 场景指令: prompt_templates.response_instructions[scene_type]
|    \-- 合并策略: 场景指令覆盖或追加基础指令
|
|-- Step 4: 加载输出格式 (Output Format)
|    |-- 从 prompt_templates.output_format 加载
|    |-- 包括: 情感标签格式、长度限制等
|    \-- 用户可完全自定义
|
\-- Step 5: 组装最终Prompt
     |-- 按Tier顺序拼接
     |-- 插入场景上下文
     |-- 追加用户指令
     \-- 追加输出格式要求
```

**配置文件** (`./config/prompt_templates.json`) ⭐ 用户核心自定义配置:

```json
{
  "_description": "统一Prompt模板配置 - 用户可自定义回复指令和输出格式",
  "_note": "修改此文件后自动热重载，无需重启程序",
  
  "base_instructions": {
    "_comment": "所有场景共享的基础指令，用户可根据桌宠性格自定义",
    "role_consistency": "保持角色性格一致",
    "language_style": "使用口语化、亲切的表达方式",
    "response_length": "回复简洁自然，不超过{max_response_length}字",
    "memory_usage": "如果涉及记忆中的内容，自然地引用",
    "honesty_principle": "如果用户提到你不记得的事，坦诚说不记得，不要编造"
  },
  
  "response_instructions": {
    "_comment": "各场景的回复指令，用户可完全自定义",
    
    "conversation": {
      "instruction": "请根据以上信息，以角色身份回复用户的消息。",
      "requirements": [
        "{base_instructions.role_consistency}",
        "{base_instructions.response_length}",
        "{base_instructions.memory_usage}",
        "{base_instructions.honesty_principle}"
      ]
    },
    
    "hourly_chime": {
      "instruction": "现在是{hour}点整，用简短俏皮的话问候主人。",
      "requirements": [
        "结合当前时间段的特点",
        "如果是深夜，表达对主人健康的关心",
        "回复不超过30字"
      ]
    },
    
    "focus_warning": {
      "instruction": "主人在专注时打开了{distraction_app}，用{tone}的语气提醒。",
      "requirements": [
        "根据警告次数调整语气严厉程度",
        "可以针对具体应用类型调侃",
        "不要太长，简短有力"
      ],
      "tone_mapping": {
        "first_warning": "轻柔提醒",
        "second_warning": "略带担忧",
        "third_warning": "假装生气"
      }
    },
    
    "focus_complete": {
      "instruction": "主人完成了{duration}分钟的专注，真诚地夸奖他。",
      "requirements": [
        "根据专注时长调整夸奖程度",
        "如果中途没有警告，额外称赞",
        "可以提议休息或奖励"
      ]
    },
    
    "system_warning": {
      "instruction": "电脑{warning_type}，用关切/调侃的语气提醒主人。",
      "requirements": [
        "结合具体数值让提醒更生动",
        "可以拟人化表达(如'脑容量不够了')",
        "简短即可，不要啰嗦"
      ]
    },
    
    "feed_response": {
      "instruction": "主人喂了你{food_name}，表达你的感受和感谢。",
      "requirements": [
        "根据食物属性(口感/温度/味道)生成反应",
        "可以结合当前心情和饥饿度",
        "表达感谢但不要太夸张"
      ]
    },
    
    "game_result": {
      "instruction": "游戏结果是{result}，表达你的反应。",
      "requirements": [
        "赢了可以得意，输了可以不服气",
        "平局表示惊讶",
        "可以提议再来一局"
      ]
    },
    
    "tool_complete": {
      "instruction": "你帮主人完成了{tool_name}，汇报结果。",
      "requirements": [
        "简洁汇报执行结果",
        "可以加入小感想",
        "如果工作量大，可以撒娇说累"
      ]
    },
    
    "idle_chat": {
      "instruction": "主人已经{idle_minutes}分钟没有互动了，主动说点什么。",
      "requirements": [
        "可以是关心、闲聊、小吐槽",
        "不要太打扰，语气轻松",
        "可以结合当前时间或天气"
      ]
    },
    
    "wake_up": {
      "instruction": "你刚从睡眠中{wake_reason}，表达反应。",
      "requirements": [
        "被用户叫醒和自然醒的反应不同",
        "可以表现睡眼惺忪的状态",
        "如果是深夜，可以关心用户为什么还没睡"
      ]
    },
    
    "clipboard_react": {
      "instruction": "用户复制了{content_type}类型的内容，用俏皮的语气评论。",
      "requirements": [
        "根据内容类型(代码/链接/文本)调整反应",
        "可以调侃或好奇",
        "简短即可"
      ]
    },
    
    "clipboard_eat": {
      "instruction": "你'吃掉'了剪贴板里的内容，表达反应。",
      "requirements": [
        "用拟人化'品尝'的方式描述",
        "根据内容类型给出'味道'评价",
        "简短可爱即可"
      ]
    },
    
    "network_status": {
      "instruction": "网络状态变为{status}，表达你的反应。",
      "requirements": [
        "高延迟可以吐槽",
        "断网可以拟人化(如'追信号')",
        "恢复时可以庆祝"
      ]
    },
    
    "gaming_mode_exit": {
      "instruction": "主人刚结束{game_duration}分钟的游戏，问候他。",
      "requirements": [
        "根据游戏时长调整关心程度",
        "长时间游戏建议休息",
        "深夜游戏表达担心"
      ]
    },
    
    "random_event": {
      "instruction": "生成一个有趣的小事件，带两个选项。",
      "requirements": [
        "事件要有趣、符合角色性格",
        "两个选项要有不同的结果",
        "避免重复最近生成过的事件"
      ]
    },
    
    "launcher": {
      "instruction": "帮主人启动{app_name}程序，生成启动反馈。",
      "requirements": [
        "简短的启动提示",
        "可以根据程序类型调整语气",
        "启动失败时给出安慰和建议"
      ]
    },
    
    "bookmark": {
      "instruction": "带主人去{site_name}网站，生成导航语。",
      "requirements": [
        "简短的导航提示",
        "可以根据网站类型加入小提醒",
        "语气轻松活泼"
      ]
    },
    
    "note_recall": {
      "instruction": "随机翻到一条{note_age_days}天前的便签，提醒主人。",
      "requirements": [
        "根据笔记新旧程度调整语气",
        "可以尝试关联当前用户活动",
        "语气自然，像不经意间想起"
      ]
    }
  },
  
  "mood_hints": {
    "_comment": "用户情绪相关的提示词，用户可自定义如何回应不同情绪",
    "negative_mood": "请适当表达关心，但不要过度追问。",
    "positive_mood": "可以一起分享快乐的心情。",
    "urgent_mood": "注意用户可能比较急，回复要简洁有效。",
    "tired_mood": "用户可能很累，说话温柔一些，建议休息。"
  },
  
  "output_format": {
    "_comment": "输出格式要求，用户可根据需要调整",
    "emotion_tag": {
      "enable": true,
      "format": "[EMOTION:{emotion}:{intensity}]",
      "position": "end",
      "instruction": "在回复末尾添加情感标签"
    },
    "max_length_override": {
      "_comment": "各场景可覆盖默认长度限制",
      "conversation": 150,
      "hourly_chime": 30,
      "focus_warning": 50,
      "focus_complete": 80,
      "system_warning": 50,
      "feed_response": 60,
      "game_result": 50,
      "tool_complete": 80,
      "idle_chat": 50,
      "wake_up": 50,
      "clipboard_react": 40,
      "clipboard_eat": 30,
      "network_status": 50,
      "gaming_mode_exit": 60,
      "random_event": 200,
      "launcher": 40,
      "bookmark": 30,
      "note_recall": 60
    }
  },
  
  "scene_contexts": {
    "_comment": "各场景的额外上下文注入规则，高级用户可调整",
    
    "focus_warning": {
      "inject_fields": ["distraction_app", "app_category", "focus_elapsed_minutes", "warning_count"],
      "memory_retrieval": false,
      "forced_tier": 2,
      "_tier_note": "强制使用Tier2规则生成，跳过Tier3 LLM调用以保证响应速度"
    },
    
    "game_result": {
      "inject_fields": ["game_name", "player_choice", "pet_choice", "result", "streak_info"],
      "memory_retrieval": false,
      "forced_tier": 2,
      "_tier_note": "默认Tier2，可在minigame_settings.json中按场景覆盖为Tier3"
    },
    
    "hourly_chime": {
      "inject_fields": ["hour", "time_period", "weather", "user_activity"],
      "memory_retrieval": "lightweight",
      "memory_query": "recent_user_state",
      "forced_tier": null,
      "_tier_note": "默认按场景分类规则(MEDIUM→Tier2/3)，可在此处强制指定Tier"
    },
    
    "conversation": {
      "inject_fields": ["user_input", "inferred_mood"],
      "memory_retrieval": "full",
      "memory_query": "from_user_input"
    },
    
    "system_warning": {
      "inject_fields": ["warning_type", "usage_value", "threshold"],
      "memory_retrieval": false
    },
    
    "feed_response": {
      "inject_fields": ["food_name", "food_attributes", "current_hunger", "current_mood"],
      "memory_retrieval": false
    }
  },
  
  "custom_rules": {
    "_comment": "用户完全自定义的规则，可以添加任意键值对供Prompt引用",
    "forbidden_topics": [],
    "preferred_expressions": [],
    "special_reactions": {},
    "custom_instructions": ""
  }
}
```

**场景模板示例 - 整点报时**:

```
[Hourly Chime Prompt]

{Layer 1: Identity Layer} ────────────────────────────
{从system_prompt.txt + master_profile.json加载}

{Layer 2: Working Memory} ────────────────────────────
[当前状态]
好感度: {affinity} | 心情: {mood} | 能量: {energy}%

[环境]
时间: {hour}:00 {day_of_week} | 时段: {time_period}
天气: {weather} | 用户活动: {user_activity}

{Layer 3: Long-term Memory} ────────────────────────────
{如果 scene_contexts.hourly_chime.memory_retrieval == "lightweight":}
[近期状态] {检索最近用户状态相关记忆，如"用户最近工作压力大"}

{场景上下文} ────────────────────────────
[触发事件] 整点报时

{回复指令} ────────────────────────────
{prompt_templates.response_instructions.hourly_chime.instruction}

{prompt_templates.response_instructions.hourly_chime.requirements}

{输出格式} ────────────────────────────
{prompt_templates.output_format}
```

**热重载机制**:

```
[Hot Reload System]
|
|-- 监控文件: ./config/prompt_templates.json
|-- 检测方式: 文件修改时间戳变化
|-- 重载触发:
|    |-- 自动: 每次生成Prompt前检查
|    |-- 手动: 设置界面"重载配置"按钮
|-- 重载流程:
|    |-- 读取新配置
|    |-- 验证JSON格式
|    |-- 验证必需字段存在
|    |-- 替换内存中的模板
|    \-- 记录重载日志
\-- 错误处理:
     |-- 格式错误: 保持旧配置，Toast提示用户
     \-- 字段缺失: 使用默认值填充
```

---

### 0.6 响应降级链 (Response Fallback Chain)

> **术语说明**: Tier1/2/3 指响应生成策略（见0.3节），Fallback1-5 指故障降级链（本节）

```
[Response Fallback Chain]
|
|-- Fallback 1: 智能响应 (主要方式 - 按场景分类)
|    |-- 触发: 所有用户交互、事件响应
|    |-- 流程: 场景分类 → Tier1模板/Tier2规则/Tier3 LLM
|    |-- 超时阈值: Tier3调用时3秒 (原5秒，优化体验)
|    |-- 优点: 高频场景即时响应，复杂场景个性化生成
|    \-- 延迟: Tier1<50ms / Tier2<100ms / Tier3 1-2秒
|
v (API异常? 包括超时/报错/截断)
|
|-- Fallback 2: Response Cache
|    |-- 触发条件:
|    |    |-- a. API响应超时 (>timeout_seconds)
|    |    |-- b. API返回错误 (HTTP错误/解析失败)
|    |    \-- c. API响应截断 (内容不完整)
|    |-- 流程:
|    |    |-- 计算当前场景特征向量
|    |    |-- 检索相似历史响应 (similarity > 0.8)
|    |    |-- 微调复用 (替换时间/名称等变量)
|    |    \-- 返回调整后的响应
|    |-- 缓存内容: 最近100条高质量AI响应
|    |-- 延迟: <100ms
|    |-- 优点: 保持个性化风格
|    \-- Hit Rate预期: 20-30%
|
v (Cache未命中?)
|
|-- Fallback 3: Local LLM (可选插件)
|    |-- 触发: 用户安装了本地模型插件
|    |-- 流程: 调用本地量化模型生成
|    |-- 推荐模型: Qwen2-1.5B / Llama-3.2-1B (量化版)
|    |-- 延迟: 300-800ms
|    |-- 优点: 完全离线、仍保持一定个性化
|    |-- 缺点: 需额外下载 (~1-2GB)
|    \-- 安装方式: 插件市场下载
|
v (无本地模型 或 生成失败?)
|
|-- Fallback 4: 模板规则生成 (降级)
|    |-- 触发: 以上方式均不可用
|    |-- 流程: 根据事件类型 + 状态变量 → 模板填充
|    |-- 示例: "[mood]的[主人]，现在是[time]啦！"
|    |-- 延迟: <50ms
|    \-- 缺点: 较机械，缺乏深度上下文
|
v (模板生成失败?)
|
\-- Fallback 5: 预设文本兜底 (紧急)
     |-- 触发条件 (任一):
     |    |-- a. API响应过慢/无响应/报错
     |    |-- b. API响应截断 (内容不完整)
     |    |-- c. 网络断开 (完全离线)
     |    \-- d. 所有上级方案均失败
     |-- 文件: ./data/emergency_fallbacks.json
     |-- 内容: 极简单的兜底文本
     |-- 示例: "喵~" / "嗯" / "..."
     \-- 优先尝试: 根据事件类型选择匹配的fallback
```

**Response Cache 机制**:

```
[Response Cache System]
|
|-- 缓存结构:
|    |-- cache_key: 场景特征哈希
|    |-- response: 原始AI响应
|    |-- variables: 可替换变量列表
|    |-- quality_score: 响应质量评分 (0-1)
|    |-- created_at: 创建时间
|    \-- hit_count: 命中次数
|
|-- 写入条件:
|    |-- AI响应成功返回
|    |-- 响应长度在合理范围 (10-200字符)
|    |-- 不包含敏感/错误内容
|    \-- 场景具有复用价值 (非一次性事件)
|
|-- 检索流程:
|    |-- 提取当前场景特征 (event_type, time_period, mood, etc.)
|    |-- 计算与缓存条目的相似度
|    |-- 选择最佳匹配 (similarity > 0.8)
|    \-- 变量替换 (时间、名称、数值)
|
\-- 清理策略:
     |-- LRU淘汰 (超过100条)
     |-- 过期淘汰 (超过7天未命中)
     \-- 低质量淘汰 (quality_score < 0.5)
```

**配置文件** (`./config/generation_settings.json`):

```json
{
  "default_strategy": "hybrid",
  
  "scene_classification": {
    "enable": true,
    "rules_path": "./config/scene_rules.json",
    "default_tier": "complex"
  },
  
  "tier1_template": {
    "enable": true,
    "templates_path": "./config/simple_templates.json",
    "variant_pool_size": 5,
    "max_response_length": 30
  },
  
  "tier2_rule_based": {
    "enable": true,
    "rules_path": "./config/generation_rules.json",
    "variable_sources": ["state", "time", "weather", "mood"]
  },
  
  "tier3_ai_generation": {
    "timeout_seconds": 3,
    "retry_attempts": 1,
    "model": "gpt-4o-mini",
    "temperature": 0.8,
    "max_tokens": 150
  },
  
  "response_cache": {
    "enable": true,
    "max_entries": 100,
    "similarity_threshold": 0.8,
    "ttl_days": 7,
    "quality_threshold": 0.5,
    "cacheable_events": [
      "hourly_chime", "idle_chat", "system_warning",
      "weather_comment", "greeting", "goodbye"
    ]
  },
  
  "local_llm": {
    "enable": false,
    "plugin_id": "local-llm-fallback",
    "model_path": "./plugins/local-llm/model/",
    "max_tokens": 100,
    "temperature": 0.7
  },
  
  "fallback_messages": {
    "enable": true,
    "messages_path": "./config/fallback_messages.json"
  }
}
```

---

### 0.6a 状态系统与内在驱动 (State System & Inner Drive)

> **设计哲学**: 轻度养成 × 自适应主动性 — 有生命感，但不是负担
> **核心理念**: 用"情感共鸣"替代"惩罚机制"，桌宠不会因为被忽略而"死亡"

```
[State System - 轻度养成模式]
|
|-- 核心状态 (Core States):
|    |
|    |-- 心情 (Mood): 影响表情、语气、动画
|    |    |-- 主状态: Happy / Normal / Tired / Sad / Anxious
|    |    |-- 子状态: Excited/Content, Relaxed/Focused, Sleepy/Exhausted, Disappointed/Lonely, Worried/Nervous
|    |    |-- 影响因素: 互动频率、用户情绪、时间段、随机事件
|    |    |-- 表现: 通过表情/颜色/动画展示，不强迫用户
|    |    \-- 衰减: 长时间无互动 → 逐渐趋向 Normal
|    |
|    |-- 能量 (Energy): 0-100%
|    |    |-- 消耗: 长时间运行、频繁互动
|    |    |-- 恢复: 睡眠模式、用户关闭应用
|    |    |-- 低能量表现: 打哈欠动画、说话变慢
|    |    \-- 设计原则: 能量低时桌宠会"困"，但不强制用户做什么
|    |
|    |-- 饥饿度 (Hunger): 0-100% (0=饱，100=很饿)
|    |    |-- 增长: 时间流逝 (+2/小时)
|    |    |-- 降低: 用户喂食
|    |    |-- 饥饿表现: 50%开始偶尔提及，70%明显表现
|    |    \-- ⭐ 特殊机制: 见下方"自主觅食"
|    |
|    \-- 好感度 (Affinity): 0-999
|         |-- 等级:
|         |    |-- Lv.1 (0-24): 陌生
|         |    |-- Lv.2 (25-49): 熟悉  
|         |    |-- Lv.3 (50-74): 亲密
|         |    |-- Lv.4 (75-99): 挚爱
|         |    \-- Lv.5 (100+): 羁绊
|         |-- 增加: 喂食、聊天、完成任务、专注时钟
|         |-- 减少: 长期不互动、饥饿过度(见下方机制)
|         \-- 影响: 解锁表情、影响主动互动频率
|
|-- ⭐ 自主觅食机制 (Auto-Feed):
|    |-- 触发条件: 饥饿度 ≥ 70% AND 仓库有食物
|    |-- 行为:
|    |    |-- 桌宠自己去仓库"拿"一个食物吃
|    |    |-- 播放特殊动画 (翻仓库 + 吃东西)
|    |    |-- 生成对话: "主人太忙了...我自己找点吃的..."
|    |    \-- 好感度 -3 (轻微下降，表示"被忽略的委屈")
|    |-- 仓库为空时:
|    |    |-- 不会饿死！只是一直抱怨
|    |    |-- 心情变为 Sad，偶尔说"好饿..."
|    |    |-- 好感度每小时 -1 (但有下限，不会降到0)
|    |    \-- 设计理念: 委屈但不惩罚
|    \-- 用户喂食后: 立即恢复心情，表达感谢
|
|-- 状态不会导致"死亡":
|    |-- 没有永久负面后果
|    |-- 最差情况: 持续Sad + 好感度降低
|    |-- 恢复: 任何正面互动都能改善状态
|    \-- 核心原则: 情感共鸣，不是压力源
```

**内在驱动系统 (Inner Drive System)**:

> **设计目标**: 让桌宠有"自己的生活"，不只是被动响应
> **简化实现**: 只实现2个核心驱动，避免过度复杂

```
[Inner Drive System - 简化版]
|
|-- 驱动1: 无聊感 (Boredom)
|    |-- 触发条件: 用户空闲时间 > idle_threshold (可配置)
|    |-- 行为:
|    |    |-- 自己"找事做" (小动画：玩毛线、追尾巴、看窗外)
|    |    |-- 偶尔主动说话 (不打扰，气泡自动消失)
|    |    \-- 探索桌面 (移动到屏幕边缘看看)
|    |-- 频率控制: 每次行为后冷却 5-15 分钟
|    \-- 用户设置: 可关闭或调整阈值
|
|-- 驱动2: 依恋感 (Attachment)
|    |-- 影响因素: 好感度等级 + 累计陪伴时长
|    |-- 效果:
|    |    |-- 好感度越高 → 主动互动频率越高
|    |    |-- 好感度低时 → 更安静，偶尔观望
|    |    |-- 好感度高时 → 更黏人，主动分享
|    |-- 具体行为:
|    |    |-- Lv.1-2: 几乎不主动，仅响应
|    |    |-- Lv.3: 偶尔主动打招呼
|    |    |-- Lv.4: 会关心用户状态
|    |    \-- Lv.5: 主动分享"发现"，记住用户提到的事
|    \-- 设计理念: 关系越深，互动越自然
```

**自适应主动性 (Adaptive Proactivity)**:

```
[Adaptive Proactivity System]
|
|-- 自动检测用户状态:
|    |-- 全屏应用检测 (Rust模块): 游戏/视频 → 静音模式
|    |-- 会议应用检测: Teams/Zoom/腾讯会议 → 完全静默
|    |-- 深夜模式: 23:00-07:00 → 降低主动频率
|    |-- 用户活跃度: 频繁操作 → 可能在工作，减少打扰
|    \-- 长时间空闲: 可能离开了 → 进入待机
|
|-- 手动免打扰模式:
|    |-- 入口: 右键菜单 / 快捷键 / 设置
|    |-- 效果:
|    |    |-- 完全停止主动行为
|    |    |-- 仅响应用户直接交互
|    |    |-- 状态栏显示"免打扰"图标
|    |-- 定时解除: 可设置1h/2h/4h/手动
|    \-- 紧急打断: 系统警告(CPU过热等)仍会提示
|
|-- 主动行为频率控制 (用户可自定义):
|    |-- 预设模式:
|    |    |-- 安静模式: 每小时最多1次主动行为
|    |    |-- 适中模式: 每小时最多3次 (默认)
|    |    |-- 活泼模式: 每小时最多6次
|    |-- 自定义: 滑动条调节 0-10 次/小时
|    |-- 分时段设置: 工作时间/休息时间不同频率
|    \-- 配置路径: ./config/proactivity_settings.json
```

**配置文件** (`./config/state_settings.json`):

```json
{
  "mood": {
    "default": "Calm",
    "decay_to_bored_hours": 4,
    "interaction_boost": 0.2,
    "negative_event_penalty": 0.3
  },
  
  "energy": {
    "max": 100,
    "decay_per_hour": 2,
    "sleep_recovery_per_hour": 20,
    "low_threshold": 30,
    "critical_threshold": 10
  },
  
  "hunger": {
    "max": 100,
    "increase_per_hour": 2,
    "mention_threshold": 40,
    "obvious_threshold": 60,
    "auto_feed_threshold": 70,
    "auto_feed_affinity_penalty": 3,
    "starving_affinity_decay_per_hour": 1,
    "affinity_decay_min_floor": 10
  },
  
  "affinity": {
    "level_thresholds": [0, 25, 50, 75, 100],
    "level_names": ["陌生", "熟悉", "亲密", "挚爱", "羁绊"],
    "max": 999,
    "decay_per_day_inactive": 0
  },
  
  "inner_drive": {
    "boredom": {
      "enable": true,
      "idle_threshold_minutes": 20,
      "action_cooldown_minutes": 10,
      "actions": ["play_yarn", "chase_tail", "look_outside", "stretch", "nap"]
    },
    "attachment": {
      "enable": true,
      "proactivity_by_level": {
        "1": 0.2, "2": 0.4, "3": 0.6, "4": 0.8, "5": 1.0
      }
    }
  },
  
  "auto_detection": {
    "fullscreen_quiet_mode": true,
    "meeting_apps": ["Teams.exe", "Zoom.exe", "WeChat.exe", "TencentMeeting.exe"],
    "night_mode": {
      "enable": true,
      "start_hour": 23,
      "end_hour": 7,
      "frequency_multiplier": 0.3
    }
  },
  
  "do_not_disturb": {
    "enable_manual_toggle": true,
    "hotkey": "Ctrl+Shift+D",
    "auto_disable_options": ["1h", "2h", "4h", "manual"],
    "allow_emergency_interrupt": true
  },
  
  "proactivity": {
    "mode": "moderate",
    "mode_limits": {
      "quiet": 1,
      "moderate": 3,
      "active": 6
    },
    "custom_per_hour": null,
    "work_hours": {
      "enable": false,
      "start": "09:00",
      "end": "18:00",
      "frequency_multiplier": 0.5
    }
  }
}
```

---

### 0.7 Agent自主循环架构 (Agent Autonomous Loop)

> **核心理念**: 统一管理所有主动行为，区分Workflow与Agent模式，避免工具滥用导致上下文注意力稀释
> **设计原则**: 单步可完成的操作用Workflow，多步推理才用Agent模式

```
[Agent Autonomous Loop - 统一架构]
|
|-- 设计原则:
|    |-- Workflow优先: 单步操作直接执行，不走Agent循环
|    |-- Agent谨慎: 仅复杂多步任务才启用完整Agent循环
|    |-- 资源控制: 限制主动行为频率，避免打扰用户
|    |-- 优先级管理: 多个触发同时满足时按优先级排队
|    |-- 上下文节约: 工具调用要精准，避免注意力稀释
|    \-- 执行追踪: 每个阶段记录到可观测性系统
|
|-- 循环结构 (每分钟执行一次):
|    |
|    |-- Phase 1: Perception (感知)
|    |    |-- 时间感知: 当前时间、距上次交互时长
|    |    |-- 环境感知: 系统状态、天气、用户活动
|    |    |-- 状态感知: 能量、心情、饥饿度
|    |    |-- 记忆感知: 是否有待处理的重要记忆
|    |    |-- ⭐ 追踪记录: span_id, operation="perception", context
|    |    \-- 输出: PerceptionContext对象
|    |
|    |-- Phase 2: Event Evaluation (事件评估)
|    |    |-- 遍历所有注册的主动行为触发器
|    |    |-- 评估每个触发器的条件是否满足
|    |    |-- 生成候选事件列表 (满足条件的)
|    |    |-- ⭐ 追踪记录: span_id, operation="event_evaluation", candidates_count
|    |    \-- 输出: List<CandidateEvent>
|    |
|    |-- Phase 3: Priority Resolution (优先级决策)
|    |    |-- 按优先级排序候选事件
|    |    |-- 检查冷却时间 (避免重复触发)
|    |    |-- 检查全局频率限制
|    |    |-- 选择最高优先级的事件执行 (或不执行)
|    |    |-- ⭐ 追踪记录: span_id, operation="priority_resolution", selected_event
|    |    \-- 输出: SelectedEvent 或 None
|    |
|    |-- Phase 4: Execution Strategy (执行策略选择)
|    |    |-- 判断事件复杂度:
|    |    |    |-- SIMPLE: 单步操作 → Workflow模式
|    |    |    |-- MEDIUM: 条件分支 → Workflow + 规则
|    |    |    \-- COMPLEX: 多步推理 → Agent模式
|    |    |-- Workflow模式: 直接执行预定义流程
|    |    |-- Agent模式: 启动完整推理循环
|    |    |-- ⭐ 追踪记录: span_id, operation="execution", mode, duration_ms, status
|    |    \-- 输出: ExecutionResult
|    |
|    \-- Phase 5: Memory Update (记忆更新)
|         |-- 记录执行的事件到短期记忆
|         |-- 更新行为统计 (用于自适应)
|         |-- 必要时生成反思记忆
|         |-- 重置循环状态
|         |-- ⭐ 追踪记录: span_id, operation="memory_update", changes
|         \-- 提交trace到可观测性系统
|
|-- 执行追踪集成 (Execution Tracing Integration):
|    |-- 每次Agent循环创建新的trace_id
|    |-- 每个Phase创建子span
|    |-- 记录关键决策点和结果
|    |-- 失败时记录错误上下文
|    |-- 延迟超阈值时标记警告
|    \-- 写入trace_logs目录
```

**轻量行为计划 (Lightweight Behavior Planning)**

> **设计理念**: 让桌宠的行为更有连贯性，不只是被动响应事件，而是有"短期意图"
> **核心原则**: 轻量化实现，每小时生成一次行为意图，不是复杂的长期目标系统

```
[Lightweight Behavior Planning]
|
|-- 设计目标:
|    |-- 让行为更连贯: 例如"连续几天提醒用户早睡"
|    |-- 增加主动性: 例如"今晚想和主人聊聊最近的心情"
|    |-- 避免过度复杂: 不是真正的长期目标系统，只是短期意图
|    \-- 零额外API调用: 计划生成复用反思时间，或使用规则
|
|-- 计划生成时机:
|    |-- 触发: 每小时整点 (与整点报时合并处理)
|    |-- 或者: 每日反思时生成第二天的行为意图
|    |-- 方式: 规则推断 (优先) 或 LLM生成 (复杂场景)
|    \-- 存储: 内存 + 持久化到 behavior_plan.json
|
|-- 计划结构:
|    {
|      "generated_at": "2025-12-29T10:00:00",
|      "valid_until": "2025-12-29T11:00:00",
|      "intentions": [
|        {
|          "type": "proactive_care",
|          "target": "remind_rest",
|          "trigger_condition": "hour >= 22 AND user_active",
|          "reason": "用户连续3天熬夜，需要关心",
|          "priority": "MEDIUM"
|        },
|        {
|          "type": "topic_interest",
|          "target": "ask_about_weekend",
|          "trigger_condition": "is_friday AND idle_time > 10min",
|          "reason": "用户之前提到周末想出去玩",
|          "priority": "LOW"
|        }
|      ],
|      "avoid_actions": [
|        {
|          "type": "topic_avoid",
|          "target": "work_pressure",
|          "reason": "用户最近对工作话题反应消极"
|        }
|      ]
|    }
|
|-- 意图类型:
|    |
|    |-- proactive_care: 主动关心
|    |    |-- remind_rest: 提醒休息
|    |    |-- check_mood: 询问心情
|    |    \-- celebrate_event: 庆祝事件 (如生日倒计时)
|    |
|    |-- topic_interest: 话题意图
|    |    |-- continue_topic: 继续昨天的话题
|    |    |-- ask_about_X: 主动询问某事
|    |    \-- share_discovery: 分享发现 (如天气变化)
|    |
|    \-- behavior_adjust: 行为调整
|         |-- reduce_frequency: 减少主动打扰
|         |-- increase_warmth: 增加关心语气
|         \-- avoid_topic: 避免某话题
|
|-- 计划执行:
|    |
|    |-- 融入现有循环:
|    |    |-- 在 Phase 2 Event Evaluation 时检查当前计划
|    |    |-- 如果意图的 trigger_condition 满足 → 生成额外事件
|    |    \-- 与其他事件一起进入 Phase 3 优先级排序
|    |
|    |-- 计划影响Prompt:
|    |    |-- 当前意图注入到系统提示
|    |    |-- 示例: "[当前意图] 今晚想关心主人的休息情况"
|    |    \-- 影响LLM生成的内容倾向
|    |
|    \-- 计划过期处理:
|         |-- 超过 valid_until → 自动清除
|         |-- 意图被执行 → 标记为 completed
|         |-- 新计划生成 → 覆盖旧计划
|         \-- ⭐ 意图完成后不立即生成新计划，等待下一整点统一生成，避免频繁计划更新
|
|-- 规则推断示例 (无需LLM):
|    |
|    |-- IF 用户连续3天22点后活跃:
|    |    \-- 生成意图: remind_rest, trigger: hour >= 22
|    |
|    |-- IF 用户生日在3天内:
|    |    \-- 生成意图: celebrate_event, trigger: daily_greeting
|    |
|    |-- IF 用户本周互动减少50%:
|    |    \-- 生成意图: reduce_frequency + check_mood
|    |
|    \-- IF 用户昨天提到某个话题且情绪积极:
|         \-- 生成意图: continue_topic, trigger: idle_chat
```

**配置** (`./config/behavior_plan_settings.json`):

```json
{
  "enable_behavior_planning": true,
  "plan_generation": {
    "interval_hours": 1,
    "prefer_rule_based": true,
    "llm_generation_threshold": "complex_only",
    "max_intentions_per_plan": 3
  },
  "intention_rules": {
    "consecutive_late_nights": {
      "condition": "late_night_count >= 3",
      "generates": {"type": "proactive_care", "target": "remind_rest"}
    },
    "upcoming_birthday": {
      "condition": "days_to_birthday <= 3",
      "generates": {"type": "proactive_care", "target": "celebrate_event"}
    },
    "reduced_interaction": {
      "condition": "interaction_drop_percent >= 50",
      "generates": [
        {"type": "behavior_adjust", "target": "reduce_frequency"},
        {"type": "proactive_care", "target": "check_mood"}
      ]
    }
  },
  "plan_injection": {
    "inject_to_prompt": true,
    "prompt_template": "[当前意图] {intention_description}"
  }
}
```

**Workflow vs Agent 决策矩阵**:

```
[Execution Mode Decision]
|
|-- Workflow模式 (直接执行，不调用LLM):
|    |-- 整点报时 (时间触发 → 规则生成 → 显示)
|    |-- 系统警告 (阈值触发 → 模板响应 → 显示)
|    |-- 状态变化 (能量低 → 预定义行为)
|    |-- 定时提醒 (闹钟到 → 弹出通知)
|    |-- 简单反馈 (点击 → 播放动画)
|    \-- 特点: 输入→处理→输出，单步完成
|
|-- Agent模式 (需要推理，调用LLM):
|    |-- 自由对话 (需理解上下文 + 记忆检索)
|    |-- 情感关怀 (需分析用户状态 + 生成个性化内容)
|    |-- 复杂事件 (需多步决策：评估→计划→执行)
|    |-- 工具调用 (需理解意图 → 选择工具 → 解析结果)
|    \-- 特点: 需要多轮思考或外部信息
|
|-- 判断标准:
|    |-- 是否需要理解自然语言? → Agent
|    |-- 是否需要检索记忆? → Agent (除非缓存命中)
|    |-- 是否有明确的触发条件和固定响应? → Workflow
|    |-- 是否需要调用外部工具? → 视工具复杂度而定
|    \-- 是否需要多步推理? → Agent
```

**主动行为注册表** (Proactive Behavior Registry):

```
[Registered Proactive Behaviors]
|
|-- 时间驱动 (Time-Based):
|    |-- hourly_chime: 整点报时
|    |    |-- trigger: minute == 0 AND second == 0
|    |    |-- cooldown: 3600s
|    |    |-- priority: MEDIUM
|    |    |-- mode: WORKFLOW (Tier2规则生成)
|    |    \-- config_key: chime_settings
|    |
|    |-- daily_reflection: 每日反思
|    |    |-- trigger: hour == reflection_hour AND is_idle
|    |    |-- cooldown: 86400s
|    |    |-- priority: LOW
|    |    |-- mode: AGENT (需要LLM生成摘要)
|    |    \-- config_key: reflection_settings
|    |
|    \-- scheduled_reminder: 日程提醒
|         |-- trigger: current_time >= reminder_time
|         |-- cooldown: 0 (每个提醒独立)
|         |-- priority: HIGH
|         |-- mode: WORKFLOW
|         \-- config_key: schedule_settings
|
|-- 状态驱动 (State-Based):
|    |-- low_energy_warning: 能量过低
|    |    |-- trigger: energy < energy_warning_threshold
|    |    |-- cooldown: 1800s
|    |    |-- priority: MEDIUM
|    |    |-- mode: WORKFLOW (Tier2规则生成)
|    |    \-- config_key: state_warning_settings
|    |
|    |-- system_warning: 系统资源警告
|    |    |-- trigger: cpu > cpu_threshold OR memory > memory_threshold
|    |    |-- cooldown: 300s
|    |    |-- priority: HIGH
|    |    |-- mode: WORKFLOW (Tier2规则生成)
|    |    \-- config_key: system_monitor_settings
|    |
|    \-- mood_transition: 情绪状态转换
|         |-- trigger: mood_state_changed
|         |-- cooldown: 60s
|         |-- priority: LOW
|         |-- mode: WORKFLOW (播放动画)
|         \-- config_key: emotion_settings
|
|-- 空闲驱动 (Idle-Based):
|    |-- idle_chat: 闲聊触发
|    |    |-- trigger: idle_time > idle_chat_threshold
|    |    |-- cooldown: idle_chat_cooldown
|    |    |-- priority: LOW
|    |    |-- mode: AGENT (需要上下文生成)
|    |    \-- config_key: idle_chat_settings
|    |
|    |-- sleep_trigger: 进入睡眠
|    |    |-- trigger: idle_time > sleep_threshold AND random < probability
|    |    |-- cooldown: 3600s
|    |    |-- priority: LOW
|    |    |-- mode: WORKFLOW
|    |    \-- config_key: sleep_settings
|    |
|    \-- memory_consolidation: 记忆整合
|         |-- trigger: is_idle AND pending_memories > threshold
|         |-- cooldown: 3600s
|         |-- priority: BACKGROUND
|         |-- mode: WORKFLOW (批量处理)
|         \-- config_key: memory_settings
|
|-- 记忆驱动 (Memory-Based):
|    |-- important_date_reminder: 重要日期提醒
|    |    |-- trigger: today matches remembered_date
|    |    |-- cooldown: 86400s
|    |    |-- priority: HIGH
|    |    |-- mode: AGENT (需要个性化生成)
|    |    \-- config_key: memory_reminder_settings
|    |
|    \-- behavior_insight: 行为洞察分享
|         |-- trigger: new_behavior_pattern_detected
|         |-- cooldown: 86400s
|         |-- priority: LOW
|         |-- mode: AGENT
|         \-- config_key: reflection_settings
|
\-- 随机事件 (Random):
     \-- random_event: 随机小剧场
          |-- trigger: random < event_probability AND time_since_last > min_interval
          |-- cooldown: random_event_cooldown
          |-- priority: LOW
          |-- mode: AGENT (需要创意生成)
          \-- config_key: random_event_settings
```

**优先级与频率控制**:

```
[Priority & Rate Control]
|
|-- 优先级定义 (Priority Levels):
|    |-- CRITICAL: 立即执行，中断其他 (系统崩溃警告)
|    |-- HIGH: 优先执行 (日程提醒、重要日期)
|    |-- MEDIUM: 正常队列 (整点报时、系统警告)
|    |-- LOW: 空闲时执行 (闲聊、随机事件)
|    \-- BACKGROUND: 后台静默 (记忆整合、统计更新)
|
|-- 全局频率限制 (用户可自定义):
|    |-- 预设模式: quiet(1次/h) / moderate(3次/h) / active(6次/h)
|    |-- 自定义: 用户可通过设置界面调节 0-10 次/小时
|    |-- 免打扰时段: 可配置 (默认23:00-07:00)
|    |-- 智能检测: 全屏/会议应用时自动降低频率
|    \-- 配置位置: ./config/state_settings.json (proactivity字段)
|
|-- 冷却时间管理 (Cooldown Management):
|    |-- 每个行为独立冷却计时器
|    |-- 冷却时间可配置 (见各行为的cooldown字段)
|    |-- 支持动态调整 (根据用户反馈)
|    \-- 持久化存储 (程序重启后继续)
```

**配置文件** (`./config/agent_loop_settings.json`):

```json
{
  "enable_autonomous_loop": true,
  "loop_interval_seconds": 60,
  
  "execution_mode": {
    "prefer_workflow": true,
    "agent_mode_triggers": [
      "free_conversation",
      "emotion_analysis_needed",
      "memory_retrieval_required",
      "creative_content_generation"
    ]
  },
  
  "priority_levels": {
    "CRITICAL": 100,
    "HIGH": 80,
    "MEDIUM": 50,
    "LOW": 20,
    "BACKGROUND": 0
  },
  
  "rate_limits": {
    "base_max_proactive_per_hour": 6,
    "base_max_interruptions_per_hour": 3,
    "min_interval_between_proactive_seconds": 300,
    "quiet_hours": {
      "enable": true,
      "start": "23:00",
      "end": "07:00",
      "allowed_priorities": ["CRITICAL", "HIGH"]
    }
  },
  
  "intervention_level": {
    "current_level": 1,
    "level_descriptions": {
      "0": "静默观察 - 仅收集数据，不主动打扰",
      "1": "适度关心 - 仅在重要时刻提醒 (默认)",
      "2": "积极伙伴 - 主动提供帮助建议"
    },
    "level_multipliers": {
      "0": {"proactive": 0.3, "interruptions": 0.2},
      "1": {"proactive": 1.0, "interruptions": 1.0},
      "2": {"proactive": 1.8, "interruptions": 1.5}
    }
  },
  
  "adaptive_frequency": {
    "enable": true,
    "feedback_based_adjustment": true,
    "positive_feedback_boost": 1.1,
    "negative_feedback_reduce": 0.8,
    "ignored_event_reduce": 0.95,
    "adjustment_interval_hours": 24,
    "min_multiplier": 0.3,
    "max_multiplier": 2.0,
    "reset_on_user_change_level": true
  },
  
  "user_busy_detection": {
    "enable": true,
    "fullscreen_app_reduces_frequency": true,
    "meeting_app_mutes_proactive": true,
    "frequency_reduction_factor": 0.3
  },
  
  "behavior_defaults": {
    "default_cooldown_seconds": 1800,
    "default_priority": "MEDIUM",
    "default_mode": "WORKFLOW"
  },
  
  "state_thresholds": {
    "energy_warning_threshold": 30,
    "hunger_warning_threshold": 70,
    "idle_chat_threshold_minutes": 20,
    "sleep_threshold_minutes": 30
  }
}
```

**主动行为频率自适应**:

```
[Adaptive Frequency System]
|
|-- 基于介入级别 (Intervention Level Based):
|    |-- Level 0 (静默观察): 频率×0.3，打断×0.2
|    |-- Level 1 (适度关心): 使用基础频率 (默认)
|    |-- Level 2 (积极伙伴): 频率×1.8，打断×1.5
|    \-- 用户可在设置中切换
|
|-- 基于反馈学习 (Feedback Learning):
|    |-- 正面反馈 (用户响应/点赞): 该类行为频率×1.1
|    |-- 负面反馈 (用户点踩/投诉): 该类行为频率×0.8
|    |-- 被忽视 (用户无响应): 该类行为频率×0.95
|    |-- 统计周期: 每24小时评估一次
|    \-- 范围限制: 乘数在 [0.3, 2.0] 之间
|
|-- 有效频率计算:
|    effective_frequency = base_frequency 
|                          × level_multiplier 
|                          × feedback_multiplier
|                          × busy_detection_factor
```

**工具调用注意力管理** ⭐ 重要:

```
[Tool Use Attention Management]
|
|-- 问题: 过多工具调用会稀释LLM上下文注意力
|
|-- 解决策略:
|    |
|    |-- 1. 工具调用预筛选:
|    |    |-- 在调用前判断是否真的需要工具
|    |    |-- 能用缓存/规则解决的不调用工具
|    |    \-- 记录工具调用频率，异常高时告警
|    |
|    |-- 2. 工具结果精简:
|    |    |-- 工具返回结果要做摘要
|    |    |-- 移除冗余信息再注入上下文
|    |    \-- 设置工具结果最大token数
|    |
|    |-- 3. 单次调用限制:
|    |    |-- max_tool_calls_per_turn (默认3)
|    |    |-- 超过限制时强制结束工具调用
|    |    \-- 提示用户需要更明确的指令
|    |
|    |-- 4. 复杂请求拆分确认:
|    |    |-- 检测请求是否包含多个工具调用意图
|    |    |-- 如果超过max_tool_calls_per_turn:
|    |    |    |-- 暂停执行
|    |    |    |-- 向用户确认: "你要我做这几件事: 1.xxx 2.xxx 3.xxx 4.xxx，要一起执行吗？还是先做前三个？"
|    |    |    \-- 用户确认后分批执行
|    |    \-- 配置: enable_split_confirmation = true
|    |
|    \-- 5. 工具调用监控:
|         |-- 记录每次工具调用的必要性
|         |-- 统计工具调用成功率
|         \-- 识别频繁失败的工具调用模式
|
|-- 配置 (tool_settings.json中):
     {
       "attention_management": {
         "enable_prefilter": true,
         "max_tool_result_tokens": 500,
         "max_tool_calls_per_turn": 3,
         "enable_split_confirmation": true,
         "split_confirmation_template": "你要我做这几件事: {task_list}，要一起执行吗？还是先做前{max_count}个？",
         "log_tool_calls": true,
         "warn_on_high_frequency": true,
         "high_frequency_threshold_per_hour": 20
       }
     }
```

---

### 0.8 记忆反思机制 (Memory Reflection)

> **设计理念**: 轻量级反思 - 每日总结 + 本地规则检测行为变化，平衡功能与API成本

```
[Reflection System]
|
|-- 触发条件:
|    |-- 每日定时反思: 用户空闲时 或 凌晨自动执行
|    |-- 行为模式变化: 本地规则检测 (无需API)
|    \-- 用户手动触发: "生成观察日记"功能
|
|-- 反思类型:
|    |
|    |-- Type 1: 每日总结 (Daily Summary)
|    |    |-- 触发: 每日一次 (用户空闲 或 凌晨3点)
|    |    |-- 输入: 当天所有对话摘要 + 事件记录
|    |    |-- 输出:
|    |    |    |-- daily_summary: 简短总结 (50-100字)
|    |    |    |-- mood_trend: 情绪变化趋势
|    |    |    |-- notable_events: 值得记住的事件列表
|    |    |    \-- behavior_insights: 行为洞察
|    |    |-- 存储: Tier 3 Episodic Memory (重要度0.8)
|    |    \-- API成本: 1次/天
|    |
|    |-- Type 2: 行为变化检测 (Behavior Change Detection)
|    |    |-- 触发: 本地规则检测 (无API调用)
|    |    |-- 检测项:
|    |    |    |-- 作息变化: 活跃时段偏移 > 2小时
|    |    |    |-- 互动频率: 日均互动次数变化 > 50%
|    |    |    |-- 情绪模式: 连续3天负面情绪
|    |    |    \-- 偏好变化: 新话题/食物出现频率突增
|    |    |-- 输出: 更新 behavior_patterns 表
|    |    \-- API成本: 0
|    |
|    \-- Type 3: 关系里程碑 (Relationship Milestone)
|         |-- 触发: 好感度等级变化 / 互动天数达到阈值
|         |-- 输出: 生成特殊记忆 (重要度0.95)
|         \-- API成本: 按需 (仅重要时刻)
```

**反思输出示例**:

```
[每日总结 - 2025-12-28]
{
  "daily_summary": "今天主人似乎很忙，只简短聊了几次。晚上23点还在工作，我提醒了他早点休息。",
  "mood_trend": "stable_to_tired",
  "notable_events": [
    "主人连续3天23点后仍在工作",
    "主人提到周末想出去玩"
  ],
  "behavior_insights": {
    "work_pattern": "近期工作压力较大",
    "interaction_style": "简短高效，可能时间紧张"
  },
  "strategy_adjustment": {
    "reduce_idle_chat_frequency": true,
    "increase_rest_reminders": true,
    "weekend_activity_suggestion": "planned"
  }
}
```

**行为策略自适应**:

```
[Strategy Adjustment Rules]
|
|-- 检测到: 用户连续熬夜
|    \-- 调整: 增加深夜关心频率，降低白天闲聊
|
|-- 检测到: 用户互动频率下降
|    \-- 调整: 降低主动打扰频率，保持存在感
|
|-- 检测到: 用户对某话题反应积极
|    \-- 调整: 增加相关话题的出现概率
|
\-- 检测到: 用户对特定表达方式敏感
     \-- 调整: 在Prompt中添加避免提示
```

**配置文件** (`./config/reflection_settings.json`):

```json
{
  "daily_reflection": {
    "enable": true,
    "preferred_time": "03:00",
    "fallback_trigger": "user_idle_30min",
    "min_interactions_required": 3,
    "summary_max_length": 200
  },
  
  "behavior_detection": {
    "enable": true,
    "check_interval_hours": 6,
    "thresholds": {
      "activity_time_shift_hours": 2,
      "interaction_frequency_change_percent": 50,
      "consecutive_negative_mood_days": 3,
      "new_topic_frequency_threshold": 3
    }
  },
  
  "strategy_adjustment": {
    "enable": true,
    "auto_apply": true,
    "notify_user": false,
    "max_adjustments_per_day": 3
  },
  
  "milestones": {
    "interaction_days": [7, 30, 100, 365],
    "affinity_levels": [2, 3, 4, 5]
  }
}
```

---

### 0.9 隐私保护层 (Privacy Layer)

> **必须功能**: 保护用户隐私，符合数据安全最佳实践

```
[Privacy Protection System]
|
|-- 敏感信息过滤 (PII Detection)
|    |-- 检测类型:
|    |    |-- 正则匹配: 手机号、邮箱、身份证号、银行卡号
|    |    |-- NER识别: 地址、真实姓名、公司名称
|    |    \-- 关键词: 密码、验证码、PIN码
|    |-- 处理方式:
|    |    |-- 对话显示: 正常显示 (用户自己的内容)
|    |    |-- 记忆存储: 脱敏后存储 (替换为[已隐藏])
|    |    \-- API发送: 脱敏后发送 (保护隐私)
|    \-- 用户控制: 可关闭自动脱敏
|
|-- 记忆管理接口 (Memory Management)
|    |-- 查看记忆: 用户可浏览所有存储的记忆
|    |-- 删除单条: 删除指定记忆 (同时从向量索引移除)
|    |-- 批量删除: 按时间段/类型批量删除
|    |-- 彻底清空: 删除所有记忆数据
|    \-- 导出数据: 导出为JSON文件
|
|-- 本地加密存储 (Encryption)
|    |-- 数据库: SQLCipher加密 (AES-256)
|    |-- 密钥管理: 
|    |    |-- 默认: 系统生成密钥，存储在用户目录
|    |    \-- 可选: 用户自定义密码
|    \-- 启用条件: 用户在设置中开启
|
\-- 数据导出与迁移 (Data Portability)
     |-- 导出格式: JSON / SQLite备份
     |-- 导出内容: 
     |    |-- 对话记录
     |    |-- 用户偏好
     |    |-- 好感度/状态
     |    \-- 自定义配置
     |-- 导入功能: 从备份恢复
     \-- 云同步: 可选，用户配置云存储
```

**隐私设置界面**:

```
[Privacy Settings Panel]
|
|-- Section 1: 敏感信息保护
|    |-- [Toggle] 自动检测并脱敏敏感信息
|    |-- [Toggle] 发送到API前过滤敏感内容
|    \-- [Button] 自定义敏感词列表
|
|-- Section 2: 记忆管理
|    |-- [Button] 查看所有记忆
|    |-- [Button] 按日期删除记忆
|    |-- [Button] 清空所有记忆
|    \-- [Warning] 删除后不可恢复
|
|-- Section 3: 数据安全
|    |-- [Toggle] 启用数据库加密
|    |-- [Input] 自定义加密密码 (可选)
|    \-- [Status] 当前加密状态
|
\-- Section 4: 数据导出
     |-- [Button] 导出所有数据 (JSON)
     |-- [Button] 导出数据库备份
     |-- [Button] 从备份恢复
     \-- [Info] 上次备份时间
```

**配置文件** (`./config/privacy_settings.json`):

```json
{
  "pii_detection": {
    "enable": true,
    "detect_types": [
      "phone_number",
      "email",
      "id_card",
      "bank_card",
      "address",
      "password_keyword"
    ],
    "action": "mask_in_storage",
    "mask_placeholder": "[已隐藏]",
    "custom_patterns": []
  },
  
  "memory_management": {
    "allow_user_deletion": true,
    "confirm_before_delete": true,
    "show_memory_browser": true,
    "retention_days": 365
  },
  
  "encryption": {
    "enable": false,
    "algorithm": "AES-256-CBC",
    "key_source": "system_generated",
    "key_path": "./data/.keyfile"
  },
  
  "data_export": {
    "enable": true,
    "export_formats": ["json", "sqlite"],
    "include_embeddings": false,
    "auto_backup": {
      "enable": false,
      "interval_days": 7,
      "backup_path": "./backups/"
    }
  },
  
  "api_privacy": {
    "strip_pii_before_send": true,
    "anonymize_user_info": false,
    "log_api_requests": false
  }
}
```

---

### 0.9a 可观测性与监控系统 (Observability)

> **设计理念**: 为开发调试和生产运维提供完善的可观测性支持，追踪执行路径、监控性能指标、记录错误信息
> **重要性**: 这是生产级系统的必备能力，帮助快速定位问题和优化性能

```
[Observability System]
|
|-- 执行追踪 (Execution Tracing):
|    |-- 追踪范围:
|    |    |-- Agent循环每个Phase的执行
|    |    |-- API调用请求/响应
|    |    |-- 工具调用过程
|    |    |-- 状态转换事件
|    |    \-- 记忆检索操作
|    |-- 追踪格式:
|    |    |-- trace_id: UUID (每次用户交互唯一)
|    |    |-- span_id: UUID (每个操作唯一)
|    |    |-- parent_span_id: 父操作ID
|    |    |-- operation: 操作名称
|    |    |-- start_time / end_time
|    |    |-- status: success / error
|    |    \-- metadata: 操作相关数据
|    |-- 存储: ./data/trace_logs/{date}.jsonl
|    \-- 保留: 滚动保留7天
|
|-- 性能指标 (Performance Metrics):
|    |-- 响应延迟:
|    |    |-- api_latency_ms: API调用延迟
|    |    |-- total_response_ms: 总响应时间
|    |    |-- memory_retrieval_ms: 记忆检索延迟
|    |    \-- tool_execution_ms: 工具执行延迟
|    |-- 资源使用:
|    |    |-- memory_usage_mb: 程序内存占用
|    |    |-- db_size_mb: 数据库大小
|    |    \-- cache_hit_rate: 缓存命中率
|    |-- API成本:
|    |    |-- daily_tokens_used: 每日Token消耗
|    |    |-- daily_api_calls: 每日API调用次数
|    |    \-- cost_estimate: 估算费用
|    \-- 统计周期: 每小时聚合 + 每日报告
|
|-- 错误监控 (Error Monitoring):
|    |-- 错误分类:
|    |    |-- api_error: API调用失败
|    |    |-- tool_error: 工具执行失败
|    |    |-- state_error: 状态转换异常
|    |    |-- parse_error: 响应解析失败
|    |    \-- system_error: 系统级错误
|    |-- 错误记录:
|    |    |-- error_type, error_message
|    |    |-- stack_trace (可选)
|    |    |-- context: 错误发生时的上下文
|    |    \-- recovery_action: 采取的恢复措施
|    |-- 告警机制:
|    |    |-- 连续失败阈值: 3次
|    |    |-- 告警方式: 日志标记 + 状态栏提示
|    |    \-- 严重错误: 弹窗通知用户
|    \-- 存储: ./data/error_logs/{date}.jsonl
|
|-- 调试面板 (Debug Panel) - 开发模式:
|    |-- 入口: 隐藏命令 /debug
|    |-- 显示内容:
|    |    |-- 当前状态快照 (mood, energy, hunger, affinity)
|    |    |-- 最近10次API调用摘要
|    |    |-- 最近5次状态转换
|    |    |-- 缓存状态 (命中率、大小)
|    |    \-- 待处理向量化队列长度
|    \-- 操作: 手动触发记忆整合/向量化
|
\-- 日报生成 (Daily Report):
     |-- 触发: 每日凌晨3点 (与反思合并)
     |-- 内容:
     |    |-- 交互统计 (对话次数、游戏次数)
     |    |-- API使用量 (tokens、调用次数)
     |    |-- 错误统计 (按类型分组)
     |    |-- 性能摘要 (平均延迟、P95延迟)
     |    \-- 存储增长 (记忆数、数据库大小)
     \-- 存储: ./data/daily_reports/{date}.json
```

**配置文件** (`./config/observability_settings.json`):

```json
{
  "execution_tracing": {
    "enable": true,
    "trace_log_path": "./data/trace_logs/",
    "log_level": "INFO",
    "log_levels": ["DEBUG", "INFO", "WARN", "ERROR"],
    "trace_api_requests": true,
    "trace_tool_calls": true,
    "trace_state_transitions": true,
    "trace_memory_operations": true,
    "trace_agent_loop": true,
    "retention_days": 7,
    "max_log_size_mb": 100
  },
  
  "performance_metrics": {
    "enable": true,
    "track_response_latency": true,
    "track_memory_usage": true,
    "track_api_costs": true,
    "track_cache_stats": true,
    "aggregation_interval_minutes": 60,
    "metrics_path": "./data/metrics/"
  },
  
  "error_monitoring": {
    "enable": true,
    "capture_stack_trace": true,
    "error_log_path": "./data/error_logs/",
    "alert_on_repeated_failures": true,
    "failure_threshold": 3,
    "failure_window_minutes": 10,
    "alert_methods": ["log", "status_bar"],
    "critical_error_popup": true
  },
  
  "debug_panel": {
    "enable": true,
    "access_command": "/debug",
    "show_state_snapshot": true,
    "show_recent_api_calls": 10,
    "show_recent_transitions": 5,
    "show_cache_stats": true,
    "allow_manual_triggers": true
  },
  
  "daily_report": {
    "enable": true,
    "generation_hour": 3,
    "report_path": "./data/daily_reports/",
    "include_interaction_stats": true,
    "include_api_usage": true,
    "include_error_summary": true,
    "include_performance_summary": true,
    "retention_days": 30
  }
}
```

---

### 0.10 Tool Use能力 (工具调用层)

> **设计理念**: 让桌宠不仅能说话，还能真正执行操作。采用ReAct模式实现工具调用。
> **增强设计**: 完善的错误恢复、指数退避重试、工具结果缓存

```
[Tool Use Architecture]
|
|-- 核心组件:
|    |-- Tool Registry: 工具注册表
|    |-- Tool Executor: 工具执行器
|    |-- ReAct Loop: 推理-行动循环
|    \-- Result Handler: 结果处理器
|
|-- ReAct模式 (Reasoning + Acting):
|    |
|    v (用户输入)
|    |
|    |-- Step 1: LLM判断是否需要工具
|    |    |-- 分析用户意图
|    |    |-- 检查可用工具列表
|    |    |-- 决定: 直接回复 OR 调用工具
|    |    \-- 如需工具 → 输出工具调用JSON
|    |
|    |-- Step 2: 执行工具 (如需要)
|    |    |-- 解析工具调用参数
|    |    |-- 执行工具函数
|    |    |-- 捕获结果或错误
|    |    \-- 返回执行结果
|    |
|    |-- Step 3: 结果反馈给LLM
|    |    |-- 将工具结果注入上下文
|    |    |-- LLM生成最终回复
|    |    \-- 可能触发多轮工具调用
|    |
|    \-- Step 4: 生成用户可见回复
|         |-- 整合工具执行结果
|         |-- 以自然语言呈现
|         \-- 返回给用户
```

**首批工具定义 (v1.0)**:

```
[Tool: system_reminder]
|-- 功能: 设置系统提醒/闹钟
|-- 触发示例: "提醒我明天早上8点开会"
|-- Schema:
|    {
|      "name": "system_reminder",
|      "description": "设置系统提醒，到时间后弹出通知",
|      "parameters": {
|        "title": "提醒标题",
|        "datetime": "ISO格式时间 或 相对时间",
|        "message": "提醒内容 (可选)",
|        "repeat": "once/daily/weekly (可选)"
|      }
|    }
|-- 执行: 调用系统通知API / 写入内部调度器
\-- 反馈: "好的，我会在[时间]提醒你[事项]喵~"

[Tool: weather_query]
|-- 功能: 查询天气信息
|-- 触发示例: "明天天气怎么样"
|-- Schema:
|    {
|      "name": "weather_query",
|      "description": "查询指定城市的天气信息",
|      "parameters": {
|        "city": "城市名 (可选，默认用户配置)",
|        "date": "today/tomorrow/具体日期"
|      }
|    }
|-- 执行: 调用天气API
\-- 反馈: 根据天气数据生成个性化评论

[Tool: app_launcher]
|-- 功能: 启动应用程序
|-- 触发示例: "帮我打开VS Code"
|-- Schema:
|    {
|      "name": "app_launcher",
|      "description": "启动已配置的应用程序",
|      "parameters": {
|        "app_name": "应用名称 (需在launcher.json中配置)"
|      }
|    }
|-- 执行: 调用subprocess启动
\-- 反馈: "正在为你启动[应用]喵~"

[Tool: note_manager]
|-- 功能: 管理便签笔记
|-- 触发示例: "帮我记一下明天要买牛奶"
|-- Schema:
|    {
|      "name": "note_manager",
|      "description": "创建、读取或搜索便签",
|      "parameters": {
|        "action": "create/read/search",
|        "content": "笔记内容 (create时)",
|        "query": "搜索关键词 (search时)"
|      }
|    }
|-- 执行: 操作notes.txt
\-- 反馈: "已经帮你记下来啦~"

[Tool: web_search] (可选，需配置)
|-- 功能: 简单网页搜索
|-- 触发示例: "帮我搜一下Python教程"
|-- Schema:
|    {
|      "name": "web_search",
|      "description": "使用搜索引擎搜索信息",
|      "parameters": {
|        "query": "搜索关键词",
|        "engine": "google/bing/baidu (可选)"
|      }
|    }
|-- 执行: 打开浏览器搜索页 或 调用搜索API
\-- 反馈: "帮你搜索[关键词]中..."
```

**工具调用Prompt模板**:

```
{系统指令}
你可以使用以下工具来帮助用户：

工具列表：
1. system_reminder - 设置提醒
2. weather_query - 查询天气
3. app_launcher - 启动应用
4. note_manager - 管理便签

使用规则：
- 如需调用工具，以JSON格式输出：{"tool": "工具名", "params": {...}}
- 可以连续调用多个工具
- 如果不需要工具，直接回复用户
- 工具执行结果会返回给你，请据此生成最终回复

{用户输入}
提醒我明天下午3点开会

{LLM输出示例}
{"tool": "system_reminder", "params": {"title": "开会提醒", "datetime": "明天 15:00", "message": "记得准时参加会议"}}

{系统返回}
工具执行成功：已设置提醒 - 明天 15:00 "开会提醒"

{LLM最终回复}
好的主人，我已经帮你设置好明天下午3点的开会提醒啦~记得准时参加哦喵！
```

**错误处理与恢复机制**:

```
[Tool Error Handling - Enhanced]
|
|-- 重试策略 (Retry Strategy):
|    |-- 指数退避重试:
|    |    |-- max_attempts: 3
|    |    |-- initial_delay_ms: 500
|    |    |-- backoff_multiplier: 2
|    |    |-- max_delay_ms: 5000
|    |    \-- 重试序列: 500ms → 1000ms → 2000ms
|    |-- 可重试错误类型:
|    |    |-- network_timeout: 网络超时
|    |    |-- rate_limit: API限流
|    |    |-- server_error: 服务端错误 (5xx)
|    |    \-- transient_failure: 临时故障
|    |-- 不可重试错误:
|    |    |-- auth_error: 认证失败
|    |    |-- invalid_params: 参数错误
|    |    \-- permission_denied: 权限不足
|    \-- 重试时: 记录到追踪日志
|
|-- 工具不存在:
|    |-- 返回: "抱歉，我还不会[操作]呢..."
|    \-- 建议: 引导用户手动操作
|
|-- 参数缺失:
|    |-- LLM追问: "你想设置几点的提醒呀？"
|    \-- 获取参数后重试
|
|-- 执行失败:
|    |-- 返回错误信息给LLM
|    |-- LLM生成友好解释
|    |-- 记录错误到监控系统
|    \-- 示例: "启动[应用]失败了，可能是路径不对，你检查一下配置？"
|
|-- 超时处理:
|    |-- 设置工具执行超时 (默认10秒)
|    |-- 超时后: 先尝试重试
|    |-- 重试耗尽: 降级处理
|    \-- 降级响应: "[操作]好像卡住了，要不你手动试试？"
|
|-- 状态回滚 (State Rollback):
|    |-- 原则: 状态变更在工具成功后执行
|    |-- 金币扣除: 确认执行成功后再扣
|    |-- 记忆写入: 确认操作完成后再写
|    \-- 失败时: 不执行任何状态变更
|
\-- 高风险操作确认 (Human-in-the-Loop):
     |-- 识别高风险操作:
     |    |-- file_delete: 文件删除
     |    |-- file_move: 批量文件移动
     |    |-- send_message: 发送消息 (如邮件)
     |    \-- system_change: 系统设置变更
     |-- 确认流程:
     |    |-- 暂停执行
     |    |-- 弹窗显示: "即将执行[操作]，确认继续？"
     |    |-- 用户选择: [确认] / [取消]
     |    \-- 取消时: 返回"好的，已取消操作"
     \-- 配置: high_risk_operations (可自定义)
```

**工具结果缓存**:

```
[Tool Result Cache]
|
|-- 设计目的:
|    |-- 减少重复API调用
|    |-- 提升响应速度
|    \-- 降低成本
|
|-- 可缓存工具:
|    |-- weather_query: 天气查询 (TTL: 30分钟)
|    |-- web_search: 搜索结果 (TTL: 10分钟)
|    \-- 不缓存: 提醒设置、应用启动等状态变更类
|
|-- 缓存策略:
|    |-- 缓存键: hash(tool_name + params)
|    |-- 缓存值: {result, timestamp, hit_count}
|    |-- TTL: 按工具类型配置
|    |-- 最大条目: 100
|    \-- 淘汰策略: LRU
|
\-- 缓存失效:
     |-- TTL过期
     |-- 用户手动刷新 ("重新查询")
     \-- 相关状态变更时
```

**配置文件** (`./config/tool_settings.json`):

```json
{
  "enable_tools": true,
  "react_mode": true,
  "max_tool_calls_per_turn": 3,
  "tool_timeout_seconds": 10,
  
  "retry_strategy": {
    "enable": true,
    "max_attempts": 3,
    "initial_delay_ms": 500,
    "backoff_multiplier": 2,
    "max_delay_ms": 5000,
    "retryable_errors": ["network_timeout", "rate_limit", "server_error", "transient_failure"],
    "non_retryable_errors": ["auth_error", "invalid_params", "permission_denied"]
  },
  
  "tool_cache": {
    "enable": true,
    "max_entries": 100,
    "eviction_policy": "LRU",
    "tool_ttl_minutes": {
      "weather_query": 30,
      "web_search": 10
    },
    "non_cacheable_tools": ["system_reminder", "app_launcher", "note_manager"]
  },
  
  "high_risk_operations": {
    "enable_confirmation": true,
    "operations": {
      "file_delete": {
        "requires_confirmation": true,
        "confirmation_message": "即将删除文件，确认继续？"
      },
      "file_move_batch": {
        "requires_confirmation": true,
        "threshold": 10,
        "confirmation_message": "即将移动{count}个文件，确认继续？"
      },
      "send_message": {
        "requires_confirmation": true,
        "confirmation_message": "即将发送消息，确认继续？"
      }
    },
    "confirmation_timeout_seconds": 30,
    "default_on_timeout": "cancel"
  },
  
  "state_rollback": {
    "enable": true,
    "deferred_state_changes": true,
    "rollback_on_failure": true
  },
  
  "available_tools": {
    "system_reminder": {
      "enabled": true,
      "requires_confirmation": false
    },
    "weather_query": {
      "enabled": true,
      "default_city": "Beijing",
      "api_source": "wttr.in"
    },
    "app_launcher": {
      "enabled": true,
      "allowed_apps": "./config/launcher.json"
    },
    "note_manager": {
      "enabled": true,
      "notes_path": "./data/notes.txt"
    },
    "web_search": {
      "enabled": false,
      "default_engine": "bing",
      "open_in_browser": true
    }
  },
  
  "error_messages": {
    "tool_not_found": "抱歉，我还不会这个操作呢...",
    "execution_failed": "操作失败了，{error}",
    "timeout": "操作超时了，要不你手动试试？",
    "retrying": "遇到点问题，正在重试...",
    "cancelled": "好的，已取消操作"
  }
}
```

---

### 0.11 用户反馈循环 (Feedback Loop)

> **设计理念**: 收集隐式和显式反馈，用于优化记忆重要度和响应质量

```
[Feedback System]
|
|-- 反馈类型:
|    |
|    |-- 显式反馈 (Explicit Feedback):
|    |    |-- 👍 点赞: 用户主动认可
|    |    |-- 👎 点踩: 用户主动否定
|    |    |-- 触发方式: 对话气泡旁的可选按钮
|    |    \-- 默认: 不显示，可在设置中开启
|    |
|    \-- 隐式反馈 (Implicit Feedback):
|         |-- 继续对话: 用户在30秒内回复 → 正面信号
|         |-- 被忽视: 用户5分钟无响应 → 中性/轻微负面
|         |-- 阅读时长: 气泡显示时间 → 内容吸引度
|         |-- 重复询问: 用户重复类似问题 → 回答不满意
|         \-- 情感词检测: 用户回复中的情感倾向
|
|-- 反馈收集:
|    |
|    |-- 每次对话记录:
|    |    {
|    |      "response_id": "uuid",
|    |      "timestamp": "ISO时间",
|    |      "response_text": "回复内容",
|    |      "explicit_feedback": null/"positive"/"negative",
|    |      "implicit_signals": {
|    |        "continued_conversation": true/false,
|    |        "time_to_next_input_seconds": 15,
|    |        "was_ignored": false,
|    |        "user_sentiment": "positive"/"neutral"/"negative"
|    |      },
|    |      "context_memory_ids": ["mem_001", "mem_042"]
|    |    }
|    |
|    \-- 存储: ./data/feedback_log.json (滚动保留30天)
|
|-- 反馈应用:
|    |
|    |-- 记忆重要度调整:
|    |    |-- 显式👍 → 相关记忆 importance *= 1.2
|    |    |-- 显式👎 → 相关记忆 importance *= 0.7 + 标记review
|    |    |-- 隐式被忽视 → 相关记忆 importance *= 0.95
|    |    \-- 隐式继续对话 → 相关记忆 importance *= 1.05
|    |
|    |-- 行为策略调整:
|    |    |-- 统计负面反馈高的话题 → 减少主动提及
|    |    |-- 统计正面反馈高的互动类型 → 增加频率
|    |    \-- 每周生成反馈摘要报告
|    |
|    \-- 长期优化 (可选):
|         |-- 收集足够数据后可用于Prompt优化
|         |-- 识别用户偏好的回复风格
|         \-- 调整温度/语气参数
```

**反馈界面 (可选开启)**:

```
[Chat Bubble]
|-- 对话内容
|-- 反馈按钮区 (hover时显示):
     |-- [👍] 喜欢这个回复
     |-- [👎] 不喜欢
     \-- 点击后: 按钮消失 + 小提示"已收到反馈~"
```

**配置文件** (`./config/feedback_settings.json`):

```json
{
  "enable_feedback_collection": true,
  
  "explicit_feedback": {
    "enable_buttons": false,
    "button_position": "hover",
    "show_confirmation": true
  },
  
  "implicit_feedback": {
    "enable": true,
    "continued_conversation_threshold_seconds": 30,
    "ignored_threshold_seconds": 300,
    "detect_user_sentiment": true
  },
  
  "importance_adjustment": {
    "positive_explicit_multiplier": 1.2,
    "negative_explicit_multiplier": 0.7,
    "ignored_multiplier": 0.95,
    "continued_multiplier": 1.05
  },
  
  "storage": {
    "log_path": "./data/feedback_log.json",
    "retention_days": 30,
    "max_entries": 10000
  },
  
  "analytics": {
    "generate_weekly_report": true,
    "report_path": "./data/feedback_reports/"
  }
}
```

---

### 0.12 配置文件规范

**配置文件应该包含**:

```json
{
  "parameters": {           // ✅ 参数（阈值、间隔、数量）
    "check_interval": 30,
    "threshold": 85,
    "max_count": 100
  },
  "rules": {                // ✅ 规则（条件、触发器）
    "trigger_condition": "value > threshold",
    "blacklist": ["app1", "app2"]
  },
  "attributes": {           // ✅ 属性标签（用于AI理解）
    "taste": "sweet",
    "tone": "gentle",
    "situation": "focus_mode"
  },
  "context_hints": {        // ✅ 上下文提示（帮助AI生成）
    "mood_influence": true,
    "time_sensitive": true
  }
}
```

**配置文件不应该包含**:

```json
{
  "response_template": "xxx",    // ❌ 固定文本
  "messages": ["xxx", "yyy"],    // ❌ 文本列表
  "greeting": "xxx"              // ❌ 预设对话
}
```

**例外**: `emergency_fallbacks.json` 允许包含预设文本（仅用于完全离线场景）

---

### 0.13 配置文件: context_settings.json

```json
{
  "context_management": {
    "short_term_memory_size": 10,
    "session_timeout_minutes": 120,
    "important_event_threshold": 0.7,
    
    "context_layers": {
      "identity_layer": {
        "source": "./config/system_prompt.txt",
        "reload_on_change": true
      },
      "user_profile": {
        "source": "./data/master_profile.json",
        "inject_every_request": true
      },
      "working_memory": {
        "source": "./data/user_state.json",
        "update_interval_seconds": 5,
        "include_environment": true
      },
      "long_term_memory": {
        "facts_source": "./data/memory.db",
        "episodes_source": "./data/memory.db",
        "retrieval_on_demand": true
      }
    }
  },
  
  "prompt": {
    "mode": "standard",
    "_note": "默认使用standard模式(32k)，对新用户更友好且API成本适中",
    "mode_options": ["lite", "standard", "deep"],
    "mode_budgets": {
      "lite": 16000,
      "standard": 32000,
      "deep": 64000
    },
    "total_budget": 64000,
    "_total_budget_note": "此值为deep模式的细分配置总和，实际预算由mode_budgets[mode]决定；下方细分tokens为deep模式默认值，standard模式使用standard_mode_override覆盖",
    "extended_budget": 128000,
    "core_identity_tokens": 4000,
    "working_memory_tokens": 16000,
    "environment_tokens": 2000,
    "semantic_summary_tokens": 4000,
    "memory_index_tokens": 6000,
    "memory_fulltext_tokens": 10000,
    "instructions_tokens": 2000,
    "reserved_output_tokens": 20000,
    "standard_mode_override": {
      "_comment": "标准模式(32k)时使用这些值覆盖上述配置",
      "core_identity_tokens": 2500,
      "working_memory_tokens": 8000,
      "environment_tokens": 1000,
      "semantic_summary_tokens": 2500,
      "memory_index_tokens": 3000,
      "memory_fulltext_tokens": 5000,
      "instructions_tokens": 1000,
      "reserved_output_tokens": 9000
    },
    "memory_index_count": 100,
    "memory_fulltext_count": 10,
    "extended_index_count": 200,
    "extended_fulltext_count": 20,
    "extended_history_turns": 30,
    "conversation_history_turns": 10
  },
  
  "cache": {
    "weather_ttl_minutes": 30,
    "retrieval_ttl_minutes": 5,
    "semantic_memory_ttl_minutes": 10,
    "static_context_reload_on_change": true
  },
  
  "ai_generation_rules": {
    "max_response_length": 30,
    "min_response_length": 5,
    "temperature": 0.8,
    "avoid_repetition_window": 5,
    "personality_consistency_check": true,
    "enable_context_compression": true
  },
  
  "fallback_strategy": {
    "enable_rule_generation": true,
    "enable_preset_fallback": true,
    "fallback_text_path": "./data/emergency_fallbacks.json",
    "max_retry_attempts": 2,
    "retry_delay_ms": 500,
    "api_timeout_seconds": 5
  },
  
  "optimization": {
    "enable_response_cache": true,
    "cache_duration_seconds": 300,
    "batch_generation": false,
    "parallel_requests": false
  }
}
```

---

### 0.13a API消费控制配置 (API Settings)

**配置文件** (`./config/api_settings.json`):

```json
{
  "primary_api": {
    "provider": "anthropic",
    "base_url": "https://api.anthropic.com/v1",
    "api_key_env": "ANTHROPIC_API_KEY",
    "default_model": "claude-sonnet-4-20250514",
    "timeout_seconds": 30
  },
  
  "fallback_api": {
    "enable": false,
    "provider": "openai",
    "base_url": "https://api.openai.com/v1",
    "api_key_env": "OPENAI_API_KEY",
    "default_model": "gpt-4o-mini",
    "trigger_on": ["timeout", "rate_limit", "server_error"]
  },
  
  "rate_limits": {
    "requests_per_minute": 60,
    "requests_per_hour": 1000,
    "tokens_per_day": 500000,
    "enable_queue": true,
    "queue_max_size": 10
  },
  
  "cost_control": {
    "enable_daily_limit": false,
    "daily_token_budget": 500000,
    "warning_threshold_percent": 90,
    "action_on_limit": "fallback_to_cache",
    "reset_time": "00:00",
    "_note": "优惠额度充足，无需严格限制"
  },
  
  "scene_api_switches": {
    "_comment": "控制各场景是否使用API，false则直接跳过Tier3从Tier2开始（不走完整降级链）",
    "_behavior_note": "设为false时：直接使用Tier2规则生成，跳过Tier3 LLM调用、Response Cache、Local LLM等步骤",
    "conversation": true,
    "hourly_chime": true,
    "focus_warning": true,
    "focus_complete": true,
    "system_warning": true,
    "feed_response": true,
    "game_result": true,
    "idle_chat": true,
    "random_event": true,
    "clipboard_react": true,
    "wake_up": true,
    "daily_reflection": true,
    "auto_feed_reaction": true
  },
  
  "embedding_api": {
    "provider": "openai",
    "model": "text-embedding-3-small",
    "batch_size": 32,
    "enable_local_fallback": true,
    "local_model": "sentence-transformers/all-MiniLM-L6-v2"
  },
  
  "monitoring": {
    "log_all_requests": false,
    "log_path": "./data/api_usage.log",
    "generate_daily_report": true,
    "report_path": "./data/api_reports/"
  }
}
```

---

### 0.14 动画系统架构 (Animation System)

> **核心设计**: 动画与AI响应解耦，独立运行，支持表情叠加

```
[Response Pipeline - Animation Decoupling]
|
v (用户输入/事件触发)
|
|-- AI Processing (异步):
|    |-- 构建Prompt
|    |-- 调用LLM生成
|    \-- 返回: {text, emotion_tag, action_hint}
|
|-- 同时进行 (并行):
|    |
|    |-- Text Display Pipeline:
|    |    |-- 接收AI生成文本
|    |    |-- 逐字显示 (打字机效果)
|    |    \-- 完成后触发后续动画
|    |
|    \-- Animation Pipeline:
|         |-- 立即响应: 播放"思考中"动画
|         |-- 收到emotion_tag后: 切换对应表情
|         |-- 文本显示时: 同步口型动画
|         \-- 支持动画叠加 (说话 + 眨眼 + 情绪)
```

**动画层次系统**:

```
[Animation Layer System]
|
|-- Layer 0: Base (基础层)
|    |-- 内容: 角色主体、服装
|    |-- 更新: 换装时变化
|    \-- 优先级: 最低
|
|-- Layer 1: Idle (待机层)
|    |-- 内容: 待机动画循环 (呼吸、微动)
|    |-- 更新: 持续播放
|    \-- 优先级: 低
|
|-- Layer 2: Expression (表情层)
|    |-- 内容: 眼睛、眉毛、嘴巴表情
|    |-- 更新: 根据emotion_tag切换
|    |-- 表情集: smile, sad, angry, shy, surprised, sleepy
|    \-- 优先级: 中
|
|-- Layer 3: Action (动作层)
|    |-- 内容: 肢体动作 (挥手、跳跃、拥抱)
|    |-- 更新: 事件触发时播放
|    |-- 结束后: 返回Idle层
|    \-- 优先级: 高
|
|-- Layer 4: Effect (特效层)
|    |-- 内容: 粒子效果 (星星、爱心、汗滴)
|    |-- 更新: 情绪强烈时叠加
|    \-- 优先级: 最高
|
\-- Layer 5: LipSync (口型层)
     |-- 内容: 嘴型动画 (A, I, U, E, O, 闭嘴)
     |-- 更新: 根据TTS音频振幅或文本音节
     \-- 优先级: 覆盖Layer 2的嘴部
```

**情感标签映射**:

```
[Emotion Tag → Animation Mapping]
|
|-- emotion_tag (AI输出) → animation_set
|    |-- happy → {expression: "smile", effect: "sparkle"}
|    |-- excited → {expression: "excited", effect: "stars", action: "jump"}
|    |-- sad → {expression: "sad", effect: "tear_drop"}
|    |-- angry → {expression: "angry", effect: "anger_mark"}
|    |-- shy → {expression: "blush", effect: "heart"}
|    |-- surprised → {expression: "surprised", action: "jump_back"}
|    |-- tired → {expression: "sleepy", action: "yawn"}
|    |-- thinking → {expression: "thinking", effect: "question_mark"}
|    \-- neutral → {expression: "idle", effect: null}
|
|-- AI输出格式:
|    {
|      "text": "今天天气真好呢~",
|      "emotion_tag": "happy",
|      "emotion_intensity": 0.8,
|      "action_hint": "wave"
|    }
```

**动画状态机**:

```
[Animation State Machine]
|
|-- States:
|    |-- Idle: 待机循环
|    |-- Talking: 说话中 (口型同步)
|    |-- Reacting: 表情反应
|    |-- Acting: 执行动作
|    |-- Transitioning: 状态过渡
|    \-- Sleeping: 睡眠状态
|
|-- Transitions:
|    |-- Idle → Talking: 开始输出文本
|    |-- Talking → Reacting: 文本输出完成
|    |-- Reacting → Acting: 收到action_hint
|    |-- Acting → Idle: 动作完成
|    |-- Any → Sleeping: 进入睡眠模式
|    \-- Sleeping → Idle: 被唤醒
|
|-- 并行处理:
|    |-- Expression可与任何状态叠加
|    |-- Effect可与任何状态叠加
|    \-- LipSync仅在Talking状态激活
```

**配置文件** (`./config/animation_settings.json`):

```json
{
  "layer_system": {
    "enable": true,
    "layers": ["base", "idle", "expression", "action", "effect", "lipsync"],
    "blend_mode": "overlay"
  },
  
  "emotion_mapping": {
    "happy": {
      "expression": "smile",
      "effect": "sparkle",
      "intensity_threshold": 0.5
    },
    "excited": {
      "expression": "excited",
      "effect": "stars",
      "action": "jump",
      "intensity_threshold": 0.7
    },
    "sad": {
      "expression": "sad",
      "effect": "tear_drop",
      "intensity_threshold": 0.5
    },
    "angry": {
      "expression": "angry",
      "effect": "anger_mark",
      "intensity_threshold": 0.6
    },
    "shy": {
      "expression": "blush",
      "effect": "heart",
      "intensity_threshold": 0.4
    },
    "neutral": {
      "expression": "idle",
      "effect": null
    }
  },
  
  "timing": {
    "expression_transition_ms": 200,
    "action_duration_ms": 1000,
    "effect_duration_ms": 2000,
    "idle_blink_interval_ms": 3000,
    "lipsync_sample_rate_ms": 50
  },
  
  "lipsync": {
    "enable": true,
    "mode": "amplitude",
    "modes": ["amplitude", "phoneme", "text_based"],
    "amplitude_threshold": 0.3,
    "mouth_shapes": ["closed", "A", "I", "U", "E", "O"]
  },
  
  "state_machine": {
    "initial_state": "Idle",
    "auto_return_to_idle_ms": 5000,
    "enable_parallel_layers": true
  }
}
```

---

### 0.15 跨模块契约规范 (Cross-Module Contracts)

> **设计目的**: 统一跨模块的数据结构、接口定义和配置格式，避免各模块各自定义导致的不一致
> **核心原则**: 单一数据源 (Single Source of Truth)，所有模块引用同一份定义

```
[Cross-Module Contract System]
|
|-- 契约存放位置: src/rainze/core/contracts/
|    |-- emotion.py      # 情感标签契约
|    |-- scene.py        # 场景分类契约
|    |-- interaction.py  # 交互请求/响应契约
|    |-- observability.py # 可观测性契约
|    \-- rust_bridge.py  # Rust边界接口契约
|
|-- 契约引用规则:
|    |-- 所有模块必须从 core.contracts 导入公共类型
|    |-- 禁止在其他模块重复定义相同结构
|    \-- 契约变更需要同步更新所有引用模块
```

#### 0.15.1 情感标签契约 (Emotion Contract)

**统一格式**: `[EMOTION:tag:intensity]`

```
[Emotion Tag Contract]
|
|-- 正则模式: \[EMOTION:(\w+):([\d.]+)\]
|
|-- 有效标签 (VALID_EMOTION_TAGS):
|    |-- happy      # 开心
|    |-- excited    # 兴奋
|    |-- sad        # 伤心
|    |-- angry      # 生气
|    |-- shy        # 害羞
|    |-- surprised  # 惊讶
|    |-- tired      # 疲惫
|    |-- anxious    # 焦虑
|    \-- neutral    # 中性
|
|-- 强度范围: 0.0 - 1.0
|    |-- 0.0-0.3: 轻微
|    |-- 0.3-0.6: 中等
|    |-- 0.6-0.8: 明显
|    \-- 0.8-1.0: 强烈
|
|-- 数据结构 (EmotionTag):
|    |-- tag: str           # 情感类型
|    |-- intensity: float   # 强度 [0.0, 1.0]
|    |-- to_string() -> str # 序列化为标签格式
|    |-- parse(text) -> Optional[EmotionTag]  # 从文本解析
|    \-- strip_from_text(text) -> str         # 从文本移除标签
|
\-- 使用模块: AI (生成), State (解析), Animation (映射)
```

#### 0.15.2 场景分类与Tier映射契约 (Scene-Tier Contract)

**中央配置表**: 单一来源，禁止各模块分散定义

```
[Scene-Tier Mapping Contract]
|
|-- 场景类型 (SceneType):
|    |-- SIMPLE   # 简单交互 (点击/拖拽)
|    |-- MEDIUM   # 中等复杂度 (整点报时/系统警告)
|    \-- COMPLEX  # 复杂场景 (自由对话)
|
|-- 响应层级 (ResponseTier):
|    |-- TIER1_TEMPLATE = 1  # 模板响应
|    |-- TIER2_RULE = 2      # 规则生成
|    \-- TIER3_LLM = 3       # LLM生成
|
|-- 中央映射表 (SCENE_TIER_TABLE):
|    |-- 场景ID -> SceneTierMapping
|    |-- 包含: default_tier, allow_override, fallback_chain
|    \-- 配置: config/scene_tier_mapping.json
|
|-- 预定义场景映射:
|    |-- click:          SIMPLE  -> Tier1, fallback=[]
|    |-- drag:           SIMPLE  -> Tier1, fallback=[]
|    |-- hourly_chime:   MEDIUM  -> Tier2, fallback=[Tier1]
|    |-- system_warning: MEDIUM  -> Tier2, fallback=[Tier1]
|    |-- game_result:    MEDIUM  -> Tier2, fallback=[Tier1]
|    |-- feed_response:  MEDIUM  -> Tier2, fallback=[Tier1]
|    |-- idle_chat:      COMPLEX -> Tier3, fallback=[Tier2, Tier1]
|    |-- conversation:   COMPLEX -> Tier3, fallback=[Tier2, Tier1]
|    \-- random_event:   COMPLEX -> Tier3, fallback=[Tier2, Tier1]
|
\-- 使用模块: Agent (分类), AI (响应), Features (触发)
```

**配置文件** (`./config/scene_tier_mapping.json`):

```json
{
  "version": "1.0.0",
  "scenes": {
    "click": {
      "scene_type": "SIMPLE",
      "default_tier": 1,
      "allow_override": false,
      "fallback_chain": [],
      "timeout_ms": 50,
      "memory_retrieval": false
    },
    "hourly_chime": {
      "scene_type": "MEDIUM",
      "default_tier": 2,
      "allow_override": true,
      "fallback_chain": [1],
      "timeout_ms": 100,
      "memory_retrieval": "facts_summary"
    },
    "conversation": {
      "scene_type": "COMPLEX",
      "default_tier": 3,
      "allow_override": true,
      "fallback_chain": [2, 1],
      "timeout_ms": 3000,
      "memory_retrieval": "full"
    }
  }
}
```

#### 0.15.3 统一上下文入口契约 (UCM Entry Contract)

**核心规则**: 所有用户交互必须经过 UCM (Unified Context Manager) 单一入口

```
[UCM Entry Contract]
|
|-- 交互来源 (InteractionSource):
|    |-- CHAT_INPUT       # 用户聊天输入
|    |-- PASSIVE_TRIGGER  # 点击/拖拽
|    |-- SYSTEM_EVENT     # 系统事件 (整点/警告)
|    |-- TOOL_RESULT      # 工具执行结果
|    |-- PLUGIN_ACTION    # 插件行为
|    \-- GAME_INTERACTION # 游戏交互
|
|-- 交互请求 (InteractionRequest):
|    |-- request_id: str      # 唯一请求ID
|    |-- source: InteractionSource
|    |-- timestamp: datetime
|    |-- payload: Dict[str, Any]
|    \-- trace_id: Optional[str]  # 可观测性追踪
|
|-- 交互响应 (InteractionResponse):
|    |-- request_id: str
|    |-- success: bool
|    |-- response_text: Optional[str]
|    |-- emotion: Optional[EmotionTag]
|    |-- state_changes: Dict[str, Any]
|    \-- trace_spans: List[str]
|
|-- 入口流程:
|    |-- EventBus收到事件 -> 路由到UCM
|    |-- UCM执行场景分类
|    |-- UCM调度到对应处理器 (AI/Tools/Features)
|    |-- 处理器返回结果
|    |-- UCM更新State + Memory
|    \-- UCM发布响应事件到GUI/Animation
|
\-- 禁止: 其他模块绕过UCM直接处理用户交互
```

#### 0.15.4 Rust/Python边界契约 (Rust Bridge Contract)

**明确划分**: 哪些操作必须走Rust，哪些保留在Python

```
[Rust-Python Boundary Contract]
|
|-- Rust层职责 (必须):
|    |-- FAISS索引操作 (add/search/remove/save/load)
|    |-- 向量重排序 (Reranker)
|    |-- 批量向量化队列管理
|    |-- CPU/内存监控
|    |-- 全屏/会议应用检测
|    \-- 中文分词/实体检测
|
|-- Python层职责 (保留):
|    |-- FTS5全文检索 (SQLite原生)
|    |-- 记忆重要度评估 (业务规则)
|    |-- 遗忘策略执行 (业务规则)
|    |-- LLM API调用
|    \-- GUI渲染/事件处理
|
|-- 接口定义 (Protocol):
|    |-- IRustMemorySearch: search(), rerank()
|    |-- IRustSystemMonitor: get_cpu_usage(), get_memory_usage(), is_fullscreen()
|    |-- IRustTextProcess: tokenize(), detect_entities()
|    \-- IRustVectorQueue: enqueue(), process_batch()
|
|-- 回退策略:
|    |-- Rust模块加载失败 -> Python回退实现
|    |-- 回退实现提供相同接口，性能降级可接受
|    \-- 日志记录回退事件
|
\-- 使用模块: Memory, Agent, Features (系统监控)
```

#### 0.15.5 可观测性契约 (Observability Contract)

**统一追踪**: 所有模块使用相同的Trace/Span格式

```
[Observability Contract]
|
|-- TraceSpan结构:
|    |-- span_id: str        # 操作唯一ID
|    |-- trace_id: str       # 请求链路ID
|    |-- parent_id: Optional[str]
|    |-- operation: str      # 操作名称
|    |-- start_time: datetime
|    |-- end_time: Optional[datetime]
|    |-- tags: Dict[str, Any]
|    \-- logs: List[Dict]
|
|-- 操作命名规范:
|    |-- agent.loop.{phase}  # Agent循环阶段
|    |-- ai.generate         # AI生成
|    |-- memory.search       # 记忆检索
|    |-- memory.vectorize    # 向量化
|    |-- tool.execute.{name} # 工具执行
|    |-- state.transition    # 状态转换
|    \-- feature.{id}.handle # 功能处理
|
|-- 使用方式:
|    with Tracer.span("memory.search", {"query": q}) as span:
|        result = await search(q)
|        span.log("found", {"count": len(result)})
|
\-- 输出: structlog JSON格式 -> ./data/trace_logs/
```

#### 0.15.6 配置分层契约 (Config Hierarchy Contract)

**配置层次**: 核心配置 -> 服务配置 -> 场景配置 -> 功能配置

```
[Config Hierarchy Contract]
|
|-- 目录结构:
|    config/
|    ├── core/                 # 核心配置 (全局共享)
|    │   ├── api.json         # API超时、重试、限流
|    │   ├── generation.json  # 生成参数
|    │   └── observability.json
|    ├── services/            # 服务配置
|    │   ├── memory.json
|    │   ├── state.json
|    │   └── tools.json
|    ├── scenes/              # 场景配置
|    │   └── scene_tier_mapping.json
|    └── features/            # 功能配置 (继承core)
|        ├── hourly_chime.json
|        └── ...
|
|-- 继承规则:
|    |-- 功能配置自动继承core配置
|    |-- 功能配置可覆盖core默认值
|    \-- 合并顺序: core -> feature
|
|-- 共享Schema:
|    |-- timeout: {connect_ms, read_ms}
|    |-- retry: {max_attempts, backoff_ms}
|    |-- ttl: {cache_seconds, persist_days}
|    \-- 所有配置引用共享schema定义
|
\-- 禁止: 各模块自定义重复的timeout/retry/ttl字段
```

---

# 第一部分：基础稳健功能

> 特点：逻辑主要是"判定+触发"，代码纯本地运行，稳定且即写即用

---

## 1. 聊天记录监控与回溯

```
[Right-Click Menu]
|-- Menu Item: "历史记录"
     |
     v (Click)

[History Panel]
|-- 对话列表 (时间戳排序)
|    |-- 每行显示: [时间戳] + [对话内容摘要] + [删除按钮]
|    \-- 支持滚动浏览
\-- 删除按钮
     |
     v (Click 删除)
     |-- 从本地Log文件/内存列表中抹除该条记录
     |-- 刷新列表显示
     \-- 角色"物理失忆" -> 不再提及被删除内容
```

**数据存储**: `./data/chat_history.json`

**配置文件** (`./config/chat_settings.json`):

```json
{
  "max_history_count": 1000,
  "page_size": 20,
  "timestamp_format": "YYYY-MM-DD HH:mm:ss",
  "auto_cleanup_days": 30,
  "show_deleted_placeholder": false
}
```

---

## 2. 动态使用说明书

```
[Menu Bar]
|-- Menu Item: "帮助/说明"
     |
     v (Click)
     |-- 检测 ./readme.md 是否存在
          |-- Exists -> 打开说明窗口
          \-- Not Exists -> Toast "未找到说明文件"

[Help Window]
|-- 渲染方式:
|    |-- Option A: 调用系统默认文本编辑器
|    \-- Option B: 内置Markdown渲染窗口
\-- 内容源: ./readme.md (实时读取)
```

**用户价值**: 无需修改代码即可更新功能介绍和快捷键列表

---

## 3. 核心人设即时修改

```
[Settings Panel]
|-- 多行文本编辑框
|    |-- 显示当前 System Prompt
|    \-- 支持实时编辑
|-- "保存" 按钮
|-- "重置" 按钮
     |
     v (Click 保存)
     |-- 更新内存中的 Prompt 变量
     |-- 重置短期对话上下文
     \-- Toast "设定已生效，无需重启"
```

**数据存储**: `./config/system_prompt.txt`

---

## 4. 个人档案注入 (用户档案)

```
[Menu]
|-- Menu Item: "用户档案"
     |
     v (Click)

[Master Profile Form]
|-- 输入字段:
|    |-- 昵称 (Text Input)
|    |-- 生日 (Date Picker)
|    |-- 对OC的称呼 (Text Input)
|    \-- 关系设定 (Dropdown / Text)
|-- "保存档案" 按钮
     |
     v (Click 保存)
     |-- 保存至 ./data/master_profile.json
     \-- 每次API请求时，强制拼接至Prompt最前端
```

**Prompt注入示例**:

```
[用户信息] 昵称:{nickname}, 生日:{birthday}, 称呼我为:{call_me}, 关系:{relationship}
```

---

## 5. 整点报时与提醒

```
[Background Thread]
|-- 每秒检测系统时间
     |
     v (分钟=0 AND 秒数=0)

[Hourly Chime Event]
|-- 视觉反馈:
|    \-- 角色图片切换 -> "张嘴/喊话" 状态
|-- 音频反馈 (可选):
|    \-- 播放预设报时音效 (./assets/audio/chime.wav)
|-- 文本反馈 (AI生成):
     |-- 通过统一Prompt模板系统构建 (scene_type: HOURLY_CHIME)
     |-- 上下文注入: 当前时间、用户活动状态、心情、轻量记忆检索
     |-- 回复指令: {prompt_templates.response_instructions.hourly_chime}
     |-- AI生成个性化问候:
     |    |-- 示例1: "喵~已经22点啦，主人还不睡吗？"
     |    |-- 示例2: "早上7点啦！新的一天开始了喵~"
     |    \-- 示例3: "下午茶时间！要不要休息一下？"
     \-- 降级: API失败时使用Tier2规则生成
```

**配置文件** (`./config/chime_settings.json`):

```json
{
  "chime_behavior": {
    "enable": true,
    "enable_sound": true,
    "sound_path": "./assets/audio/chime.wav",
    "expression": "shout"
  },
  
  "time_periods": {
    "00-05": {
      "period_name": "deep_night",
      "atmosphere": "quiet_and_dark",
      "energy_level": "very_low",
      "typical_activities": ["sleeping", "late_work"],
      "health_concerns": ["rest", "sleep"],
      "mood_tendency": "tired"
    },
    "06-11": {
      "period_name": "morning",
      "atmosphere": "fresh_and_energetic",
      "energy_level": "high",
      "typical_activities": ["breakfast", "commute", "work_start"],
      "health_concerns": ["breakfast", "hydration"],
      "mood_tendency": "positive"
    },
    "12-17": {
      "period_name": "afternoon",
      "atmosphere": "busy_and_productive",
      "energy_level": "medium",
      "typical_activities": ["work", "meetings"],
      "health_concerns": ["break", "stretch"],
      "mood_tendency": "focused"
    },
    "18-23": {
      "period_name": "evening",
      "atmosphere": "relaxed_and_social",
      "energy_level": "medium",
      "typical_activities": ["dinner", "leisure", "family_time"],
      "health_concerns": ["relax", "wind_down"],
      "mood_tendency": "calm"
    }
  },
  
  "greeting_rules": {
    "enable_ai_generation": true,
    "max_length": 30,
    "check_factors": [
      "current_time_period",
      "user_activity_status",
      "pet_mood",
      "weather_condition",
      "recent_interaction_count",
      "special_events_today"
    ],
    "tone_adjustment": {
      "early_morning": "gentle",
      "busy_hours": "encouraging",
      "late_night": "concerned"
    }
  }
}
```

**AI生成示例**:

```
[早上8点 - 天气晴]
上下文: 周一，用户刚打开电脑，心情Normal
AI生成: "早安！新的一周开始了，今天天气不错哦~"

[深夜2点 - 用户还在活动]
上下文: 检测到用户还在用电脑，concern_level高
AI生成: "都两点了...你还不睡吗？身体要紧啊..."
```

---

## 6. 专注时钟与监督

> **AI驱动**: 摸鱼警告和完成夸奖由 AI 根据上下文生成个性化内容

```
[Focus Timer Panel]
|-- 时长设定 (Slider / Input): 25/45/60 分钟
|-- "开始专注" 按钮
     |
     v (Click 开始)

[Focus Mode - Active]
|-- 记录: 专注开始时间、设定目标时长
|-- 后台监控线程 (每3-5秒):
|    |-- 检测当前活动窗口标题/进程名
|    |-- 匹配黑名单 (Steam, 视频网站等)
|         |-- Match -> 触发警告
|         \-- No Match -> Continue
|-- 警告机制:
|    |-- 通过统一上下文管理器 (InteractionType: SYSTEM_EVENT)
|    |-- 场景模板: FOCUS_WARNING
|    |-- 上下文注入:
|    |    |-- distraction_app: 检测到的应用名
|    |    |-- app_category: game/video/social
|    |    |-- focus_elapsed_minutes: 已专注时长
|    |    \-- warning_count: 本次专注的警告次数
|    |-- 回复指令: {prompt_templates.response_instructions.focus_warning}
|    |-- AI生成警告 (基于应用类型+警告次数):
|    |    |-- 首次: "诶？这会儿不是在专注吗？"
|    |    |-- 重复: "又摸鱼了！这都第{n}次了！"
|    |    \-- 针对性: "Steam？游戏的诱惑可要抵住啊！"
|    \-- 窗口震动效果
     |
     v (倒计时结束)

[Focus Complete]
|-- 通过统一上下文管理器 (InteractionType: SYSTEM_EVENT)
|-- 场景模板: FOCUS_COMPLETE
|-- 上下文注入:
|    |-- duration_minutes: 实际完成时长
|    |-- warning_count: 中途警告次数
|    \-- streak_days: 连续专注天数
|-- 回复指令: {prompt_templates.response_instructions.focus_complete}
|-- AI生成夸奖 (基于时长+表现):
|    |-- 无警告: "太厉害了！{duration}分钟心无旁骛！"
|    |-- 有警告但坚持: "虽然中间有点小波折，但你还是坚持下来了！"
|    \-- 长时间: "整整{duration}分钟！你是专注大师！"
\-- 奖励货币: +{coins} 金币
```

**配置文件** (`./config/focus_settings.json`):

```json
{
  "monitoring": {
    "default_duration_minutes": 25,
    "duration_presets": [25, 45, 60, 90],
    "check_interval_seconds": 3,
    "warning_cooldown_seconds": 30,
    "shake_intensity": 5
  },
  
  "blacklist": {
    "apps": [
      "steam.exe",
      "bilibili",
      "youtube",
      "netflix",
      "douyin",
      "tiktok"
    ],
    "app_categories": {
      "steam.exe": "game",
      "bilibili": "video",
      "youtube": "video",
      "netflix": "streaming"
    }
  },
  
  "warning_context": {
    "severity_levels": {
      "first_warning": {
        "tone": "gentle_reminder",
        "urgency": "low"
      },
      "second_warning": {
        "tone": "concerned",
        "urgency": "medium"
      },
      "third_warning": {
        "tone": "strict",
        "urgency": "high"
      }
    },
    "context_factors": [
      "distraction_app_name",
      "distraction_category",
      "focus_duration_elapsed",
      "previous_warning_count",
      "user_affinity_level",
      "time_since_last_warning"
    ]
  },
  
  "rewards": {
    "coins_per_10min": 10,
    "completion_bonus_multiplier": 1.5,
    "perfect_session_bonus": 20
  }
}
```

**AI生成示例**:

```
[第1次警告 - B站]
上下文: 已专注15分钟，好感度高，语气gentle
AI生成: "诶？想休息一下吗？不过还是先专注完这轮吧~"

[第3次警告 - 游戏]
上下文: 第3次，语气strict，检测到游戏
AI生成: "又开游戏了？！我真的要生气了哦！"

每次都不重复，且有连贯性
```

---

## 7. 喂食与背包系统

```
[Menu]
|-- Menu Item: "背包"
     |
     v (Click)

[Backpack Panel]
|-- 物品网格列表 (Grid View)
|    |-- 每格显示: [物品图标] + [数量]
|    \-- 数据源: ./data/items.json
|-- 物品详情 (Hover/Click):
     |-- 名称 + 描述 + 效果
     \-- "使用" 按钮

[Feed Action]
|-- Click 食物项 ->
     |-- 扣除数量 (-1)
     |-- 角色播放"进食"动画 (调用 ./assets/animations/actions/eat/)
     |-- AI生成口感评价:
     |    |-- 通过统一Prompt模板系统 (scene_type: FEED_RESPONSE)
     |    |-- 上下文注入: 食物名称、属性(taste/texture/temp)、心情、饥饿度
     |    |-- 回复指令: {prompt_templates.response_instructions.feed_response}
     |    |-- AI生成个性化响应:
     |    |    |-- 苹果: "喵~这个苹果好甜啊！谢谢主人！"
     |    |    |-- 蛋糕: "好吃！奶油好浓郁喵~主人最好了！"
     |    |    \-- 拉面: "呼噜呼噜...好烫！但是好吃喵！"
     |    \-- 降级: 使用食物属性模板生成
     \-- 好感度 +{affinity_bonus}

[自定义食物流程]
|-- Step 1: 画食物贴图 -> 保存到 ./assets/items/[你的食物].png
|-- Step 2: 编辑 ./data/items.json，添加新食物条目
|-- Step 3: 重启程序，新食物自动出现在背包
\-- 支持热重载: 修改数量/名称/效果无需重启
```

**数据结构** (`./data/items.json`) - **参数化食物属性**:

```json
{
  "apple": {
    "id": "apple",
    "display_name": "苹果",
    "icon": "./assets/items/apple.png",
    "quantity": 5,
    "category": "fruit",
    
    "attributes": {
      "taste": ["sweet", "slightly_sour"],
      "texture": "crisp",
      "temperature": "cool",
      "size": "medium",
      "color": "red",
      "freshness": "fresh"
    },
    
    "effects": {
      "affinity_bonus": 2,
      "mood_impact": 0.1,
      "energy_restore": 5
    },
    
    "context_tags": ["healthy", "common", "refreshing"],
    "animation_override": null
  },
  
  "custom_cake": {
    "id": "strawberry_cake",
    "display_name": "草莓蛋糕",
    "icon": "./assets/items/cake.png",
    "quantity": 3,
    "category": "dessert",
    
    "attributes": {
      "taste": ["very_sweet", "creamy"],
      "texture": "soft",
      "temperature": "room",
      "size": "large",
      "color": "pink",
      "luxury_level": "high"
    },
    
    "effects": {
      "affinity_bonus": 5,
      "mood_impact": 0.3,
      "energy_restore": 15
    },
    
    "context_tags": ["treat", "special", "indulgent"],
    "animation_override": "actions/eat_cake"
  },
  
  "ramen": {
    "id": "ramen",
    "display_name": "拉面",
    "icon": "./assets/items/ramen.png",
    "quantity": 2,
    "category": "hot_food",
    
    "attributes": {
      "taste": ["savory", "umami"],
      "texture": "chewy",
      "temperature": "hot",
      "size": "large",
      "steam_level": "steaming"
    },
    
    "effects": {
      "affinity_bonus": 3,
      "mood_impact": 0.2,
      "energy_restore": 20,
      "warmth_bonus": true
    },
    
    "context_tags": ["comfort_food", "filling", "warm"],
    "animation_override": null
  }
}
```

**AI生成示例**:

```
[用户喂食苹果]
上下文: 早上8点，心情Happy，好感度75，刚聊了减肥话题
AI生成: "早餐吃苹果好健康！不过...我想吃蛋糕~"

[用户喂食蛋糕]
上下文: 深夜1点，心情Sleepy，好感度30
AI生成: "这么晚还给我吃甜食...不过奶油好浓郁~"
```

**自定义要点**:

- **属性标签**: AI通过这些标签理解食物特性
- **多维度描述**: 味道、口感、温度等多维度
- **上下文标签**: 帮助AI判断合适的使用场景
- **无预设文本**: 所有回应由AI根据属性实时生成

---

## 8. 好感度数值体系

```
[Global State]
|-- Variable: affinity (Integer, 0-999)
|-- 等级阈值:
     |-- Lv.1: 0-24 (陌生)
     |-- Lv.2: 25-49 (熟悉)
     |-- Lv.3: 50-74 (亲密)
     |-- Lv.4: 75-99 (挚爱)
     \-- Lv.5: 100+ (羁绊)

[Affinity Gain Actions]
|-- 抚摸 (鼠标滑过+点击): +1~3
|-- 喂食: +{item.affinity_bonus}
|-- 聊天互动: +1
|-- 完成日程/专注: +5~10
\-- 每日首次互动: +3

[Affinity Loss Actions]
|-- 自主觅食 (饥饿≥90%自己拿吃的): -3
|-- 持续挨饿 (仓库空且饥饿≥90%): -1/小时
\-- 好感度下限: 10 (不会降到0)

[Level Up Event]
|
v (affinity 突破阈值)
|-- 解锁隐藏表情/动画
|-- 更换默认待机图片 (冷漠 -> 微笑)
|-- 增加主动互动频率 (依恋系统)
\-- 状态栏显示好感度进度条

[好感度与主动性关联]
|-- Lv.1-2: 几乎不主动，仅响应用户，心情多为Normal
|-- Lv.3: 偶尔主动打招呼，心情更易变为Happy
|-- Lv.4: 会关心用户状态，记住用户喜好，更容易Anxious(担心用户)
\-- Lv.5: 主动分享发现，追问之前的话题
```

**数据存储**: `./data/user_state.json`

**配置文件** (`./config/affinity_settings.json`):

```json
{
  "level_thresholds": [
    { "level": 1, "min": 0, "name": "陌生", "idle_image": "cold", "proactivity": 0.2 },
    { "level": 2, "min": 25, "name": "熟悉", "idle_image": "neutral", "proactivity": 0.4 },
    { "level": 3, "min": 50, "name": "亲密", "idle_image": "smile", "proactivity": 0.6 },
    { "level": 4, "min": 75, "name": "挚爱", "idle_image": "love", "proactivity": 0.8 },
    { "level": 5, "min": 100, "name": "羁绊", "idle_image": "bond", "proactivity": 1.0 }
  ],
  "gain_values": {
    "pet_touch": { "min": 1, "max": 3 },
    "feed": "item_bonus",
    "chat": 1,
    "focus_complete": 5,
    "schedule_complete": 5,
    "daily_checkin": 3
  },
  "loss_values": {
    "auto_feed": 3,
    "starving_per_hour": 1
  },
  "min_affinity": 10,
  "max_affinity": 999,
  "decay_per_day": 0
}
```

---

## 9. 日程提醒助手

```
[Menu]
|-- Menu Item: "日程管理"
     |
     v (Click)

[Schedule Panel]
|-- 日程列表 (List View)
|-- "添加日程" 按钮
     |
     v (Click)

[Add Schedule Dialog]
|-- 时间选择器 (DateTime Picker)
|-- 事项输入框 (Text Input)
|-- 提前提醒: 0/5/10/30 分钟 (Dropdown)
\-- "确认添加" 按钮

[Background Polling]
|-- 轮询系统时间 (每30秒)
     |
     v (匹配设定时间 OR 提前N分钟)

[Reminder Trigger]
|-- 角色窗口强制置顶
|-- 弹出对话框: "[事项内容]"
|-- 播放提示音
\-- "知道了" 按钮 -> 关闭提醒
```

**配置文件** (`./config/schedule_settings.json`):

```json
{
  "poll_interval_seconds": 30,
  "advance_reminder_options": [0, 5, 10, 15, 30],
  "default_advance_minutes": 5,
  "alert_sound_path": "./assets/audio/alert.wav",
  "enable_sound": true,
  "force_topmost": true,
  "complete_reward_coins": 10
}
```

---

## 10. 随机事件小剧场

```
[Event Timer]
|-- 可调节频率: 30min / 1h / 2h
     |
     v (Timer Trigger)

[Random Event Generation]
|-- AI生成事件 (默认模式):
|    |-- 通过统一上下文管理器 (InteractionType: PROACTIVE)
|    |-- 场景模板: RANDOM_EVENT
|    |-- 上下文注入:
|    |    |-- scene_type: "random_event"
|    |    |-- current_time, emotion_state, affinity_level
|    |    |-- recent_events: 最近24h内事件历史
|    |    \-- output_format: {situation, option_a, option_b}
|    |-- 回复指令: {prompt_templates.response_instructions.random_event}
|    |-- AI返回事件内容:
|    |    |-- 示例1: "路上看到一只流浪猫，要喂它吗？"
|    |    \-- 示例2: "发现一家新开的咖啡店，要进去尝试吗？"
|    \-- 降级: API失败时从 preset_events.json 随机选择
\-- 预设事件库 (fallback_events_path):
     \-- 仅在API完全不可用时使用

[Event Dialog]
|-- 情景描述文本
|-- Option A 按钮 / Option B 按钮
     |
     v (Click 选项)
     |-- 数值计算:
     |    |-- 金币 +/- N
     |    \-- 好感度 +/- N
     \-- 显示结果文本
```

**配置文件** (`./config/random_event_settings.json`):

```json
{
  "enable_random_events": true,
  "trigger_interval_minutes": 60,
  "interval_options": [30, 60, 120],
  "coins_range": { "min": -20, "max": 50 },
  "affinity_range": { "min": -5, "max": 10 },
  "generation_mode": "ai_primary",
  "ai_generation": {
    "enabled": true,
    "style": "creative_varied",
    "consider_context": true,
    "avoid_repeat_within_hours": 24
  },
  "fallback_events": {
    "_comment": "仅在API完全不可用时使用",
    "enabled": true,
    "path": "./data/preset_events.json"
  }
}
```

---

## 11. 闲聊陪伴模式

```
[Idle Timer]
|-- 检测用户操作 (键盘/鼠标)
|-- 无操作计时器: 默认20分钟
     |
     v (超过设定时间无操作)

[Idle Chat Trigger]
|-- 通过统一上下文管理器 (InteractionType: PROACTIVE)
|-- 场景模板: IDLE_CHAT
|-- 上下文注入:
|    |-- scene_type: "idle_chat"
|    |-- idle_duration_minutes
|    |-- last_user_activity
|    \-- current_environment_state
|-- 回复指令: {prompt_templates.response_instructions.idle_chat}
|-- 生成符合人设的唠叨/关心话语
|-- 示例:
|    |-- "你还在忙吗？记得休息哦~"
|    |-- "好安静啊...你在想什么呢？"
|    \-- "要不要喝点水？"
\-- 以气泡形式静默显示 (不弹窗打断)
```

**配置文件** (`./config/idle_chat_settings.json`):

```json
{
  "enable_idle_chat": true,
  "idle_timeout_minutes": 20,
  "chat_cooldown_minutes": 10,
  "generation_mode": "ai_primary",
  "ai_generation": {
    "enabled": true,
    "style": "casual_caring",
    "max_length": 50,
    "include_emoji": true
  },
  "fallback_messages": {
    "_comment": "仅在API完全不可用时使用",
    "enabled": true,
    "messages": [
      "你还在忙吗？",
      "好安静啊...",
      "记得休息哦~"
    ]
  },
  "bubble_display_seconds": 10,
  "bubble_style": "silent"
}
```

---

## 12. 基础物理与交互

```
[Desktop Pet - Idle State]
|-- 显示待机动画/图片

[Drag Interaction]
|-- 鼠标左键按住角色
     |
     v (Dragging)
     |-- 角色跟随鼠标移动
     |-- 可选: 切换"被抓起"表情
     |
     v (Release 松开)
     |-- 判断屏幕坐标:
          |-- 屏幕中间区域:
          |    \-- 模拟重力下落 -> 落至任务栏上方
          |-- 屏幕左边缘:
          |    \-- 吸附边缘 + 切换"攀爬/挂靠"图片 (左)
          \-- 屏幕右边缘:
               \-- 吸附边缘 + 切换"攀爬/挂靠"图片 (右)
```

**配置文件** (`./config/physics_settings.json`):

```json
{
  "display_mode": "floating",
  "display_mode_options": ["floating", "taskbar_walk"],
  "display_mode_descriptions": {
    "floating": "悬浮模式：桌宠作为独立窗口，可拖拽到任意位置",
    "taskbar_walk": "任务栏模式：桌宠在任务栏上方行走活动"
  },
  "taskbar_walk_settings": {
    "walk_speed_px_per_sec": 30,
    "idle_before_walk_seconds": 10,
    "walk_probability": 0.5,
    "walk_direction_change_probability": 0.2,
    "enable_random_stops": true,
    "stop_duration_range": [3, 10]
  },
  "enable_gravity": true,
  "gravity_acceleration": 9.8,
  "fall_animation_ms": 500,
  "edge_snap_distance_px": 50,
  "edge_snap_enabled": true,
  "drag_expression": "grabbed",
  "left_edge_expression": "climb_left",
  "right_edge_expression": "climb_right",
  "bounce_on_land": true,
  "bounce_height_px": 10,
  "allow_mode_switch_hotkey": true,
  "mode_switch_hotkey": "Ctrl+Shift+M"
}
```

---

## 13. 系统状态感知与主动场景识别

> **设计升级**: 从被动响应升级为适度主动介入，默认低介入模式

```
[System Monitor Thread]
|-- 使用 rust sysinfo 库监控系统状态
|-- 监控频率: 每5秒

[CPU Monitor]
|-- 读取 CPU 占用率
     |-- > 85%:
     |    |-- 角色切换 -> "晕倒/流汗" 表情
     |    |-- 通过统一Prompt模板系统 (scene_type: SYSTEM_WARNING)
     |    |-- 上下文注入: warning_type="CPU过热", usage_value={cpu_usage}%
     |    |-- 回复指令: {prompt_templates.response_instructions.system_warning}
     |    |-- AI生成个性化响应:
     |    |    |-- 示例1: "喵！CPU已经{cpu_usage}%了，主人在跑什么程序呀？"
     |    |    \-- 示例2: "好烫啊...电脑要变成烤箱了喵！"
     |    \-- 降级: "电脑好烫..."
     \-- <= 85%:
          \-- 恢复正常待机状态

[Memory Monitor]
|-- 读取内存占用率
     |-- > 90%:
     |    |-- 角色切换 -> "困惑/头疼" 表情
     |    |-- 通过统一Prompt模板系统 (scene_type: SYSTEM_WARNING)
     |    |-- 上下文注入: warning_type="内存不足", usage_value={memory_usage}%
     |    |-- 回复指令: {prompt_templates.response_instructions.system_warning}
     |    |-- AI生成个性化响应:
     |    |    |-- 示例1: "脑容量不够了喵...主人关些程序吧！"
     |    |    \-- 示例2: "头好疼...太多东西在运行了"
     |    \-- 降级: "内存不足..."
     \-- <= 90%:
          \-- 恢复正常待机状态
```

**主动场景识别 (Proactive Scene Detection)**:

```
[Proactive Assistance System]
|
|-- 介入级别 (Intervention Levels):
|    |-- Level 0: 静默观察 (默认)
|    |    \-- 仅收集数据，不主动打扰
|    |-- Level 1: 适度关心 (推荐)
|    |    \-- 仅在重要时刻提醒
|    \-- Level 2: 积极伙伴
|         \-- 主动提供帮助建议 (可关闭)
|
|-- 场景识别规则:
|    |
|    |-- 深夜工作检测 (Level 1+)
|    |    |-- 条件: 时间 > 23:00 AND 用户仍在活动
|    |    |-- 响应: 轻柔提醒休息 (每小时最多1次)
|    |    \-- 示例: "都这么晚了...要注意休息哦"
|    |
|    |-- 长时间专注检测 (Level 1+)
|    |    |-- 条件: 连续活动 > 2小时 无休息
|    |    |-- 响应: 建议休息眼睛/喝水
|    |    \-- 示例: "已经工作很久了，要不要休息一下喵？"
|    |
|    |-- 视频/娱乐模式检测 (Level 0+)
|    |    |-- 条件: 检测到视频播放/全屏应用
|    |    |-- 响应: 自动降低出现频率
|    |    \-- 效果: 减少打扰，静默陪伴
|    |
|    |-- 代码编写检测 (Level 2)
|    |    |-- 条件: 检测到IDE活动 + 编译失败
|    |    |-- 响应: "看起来遇到了问题？要聊聊吗~"
|    |    \-- 用户可关闭
|    |
|    \-- 会议/演示模式 (Level 0+)
|         |-- 条件: 检测到视频会议软件/演示模式
|         |-- 响应: 自动最小化或静音
|         \-- 结束后: 恢复并问候
|
|-- 干预策略:
|    |-- 高优先级 (始终触发):
|    |    |-- 系统崩溃/蓝屏警告
|    |    \-- 电池低电量 (笔记本)
|    |-- 中优先级 (Level 1+):
|    |    |-- 健康提醒 (久坐、深夜)
|    |    \-- 效率建议 (长时间无产出)
|    \-- 低优先级 (Level 2):
|         |-- 技术帮助建议
|         \-- 闲聊陪伴
```

**配置文件** (`./config/system_monitor_settings.json`):

```json
{
  "enable_system_monitor": true,
  "check_interval_seconds": 5,
  "cpu_warning_threshold": 85,
  "memory_warning_threshold": 90,
  "cpu_warning_expression": "sweat",
  "memory_warning_expression": "confused",
  
  "proactive_assistance": {
    "enable": true,
    "intervention_level": 1,
    "level_descriptions": {
      "0": "静默观察 - 仅收集数据，不主动打扰",
      "1": "适度关心 - 仅在重要时刻提醒 (推荐)",
      "2": "积极伙伴 - 主动提供帮助建议"
    }
  },
  
  "scene_detection": {
    "late_night_work": {
      "enable": true,
      "start_hour": 23,
      "end_hour": 6,
      "reminder_interval_minutes": 60,
      "max_reminders_per_night": 3
    },
    "long_focus": {
      "enable": true,
      "threshold_hours": 2,
      "reminder_cooldown_minutes": 30
    },
    "entertainment_mode": {
      "enable": true,
      "reduce_frequency_by": 0.8,
      "detected_apps": ["netflix", "youtube", "bilibili", "vlc", "potplayer"]
    },
    "meeting_mode": {
      "enable": true,
      "auto_minimize": true,
      "detected_apps": ["zoom", "teams", "腾讯会议", "钉钉", "飞书"]
    },
    "coding_mode": {
      "enable": false,
      "detected_apps": ["code", "idea", "pycharm", "webstorm", "visual studio"],
      "offer_help_on_error": false
    }
  },
  
  "ai_generation": {
    "enabled": true,
    "style": "caring_playful",
    "include_metrics": true
  },
  
  "fallback_messages": {
    "_comment": "仅API失败时使用",
    "cpu_warning": "电脑好烫...",
    "memory_warning": "内存不足...",
    "rest_reminder": "要不要休息一下？"
  },
  
  "recovery_delay_seconds": 10
}
```

```

---

## 14. 剪贴板互动

```

[Clipboard Monitor Thread]
|-- 监听剪贴板内容变化
     |
     v (检测到新复制内容)

[Clipboard Notification]
|-- 角色头上冒出小图标: "❓你复制了什么？"
     |
     v (Click 图标)

[Clipboard Interaction Panel]
|-- 显示剪贴板内容 (截断显示前100字符)
|-- AI分析内容:
|    |-- 通过统一上下文管理器 (InteractionType: PROACTIVE)
|    |-- 场景模板: CLIPBOARD_REACT
|    |-- 上下文注入:
|    |    |-- scene_type: "clipboard_react"
|    |    |-- content_type: text/code/link/image
|    |    |-- content_preview: 截断前100字符
|    |    |-- content_length
|    |    \-- detected_keywords
|    |-- 回复指令: {prompt_templates.response_instructions.clipboard_react}
|    |-- AI生成个性化响应:
|    |    |-- 代码片段: "喵！这些代码看起来...主人又在写bug了吗？"
|    |    |-- 长文本: "这么长一段！要写论文吗？"
|    |    |-- 链接: "要去{domain}逛逛吗？"
|    |    \-- 图片: "复制了图片呀，让我看看~"
|    \-- 降级: 使用基础规则匹配生成
|-- "吃掉" 按钮:
     |
     v (Click)
     |-- 清空剪贴板
     |-- AI生成反馈 (回复指令: {prompt_templates.response_instructions.clipboard_eat})
     \-- 好感度 +1

```

**配置文件** (`./config/clipboard_settings.json`):

```json
{
  "enable_clipboard_monitor": true,
  "display_max_chars": 100,
  "eat_affinity_bonus": 1,
  "notification_icon": "❓",
  "ai_analysis": {
    "enabled": true,
    "analyze_on_copy": true,
    "style": "playful_teasing",
    "max_response_length": 50
  },
  "content_detection_rules": {
    "_comment": "用于AI提示词构建，不是预设响应",
    "link": { "pattern": "^https?://", "hint": "URL链接" },
    "code": { "pattern": "function|def |class |import |const ", "hint": "代码片段" },
    "long_text": { "pattern": ".{200,}", "hint": "长文本" },
    "image": { "pattern": "^data:image", "hint": "图片数据" }
  },
  "fallback_response": "你复制了什么呀？"
}
```

---

## 15. 昼夜作息系统

```
[Idle Sleep System]
|-- 检测用户无操作时长
|-- 配置项:
|    |-- idle_before_sleepy: 30 (分钟，开始犯困)
|    |-- sleep_probability: 0.3 (入睡概率，0-1)
|    |-- nap_duration_range: [5, 15] (小睡时长范围，分钟)
|    \-- enable_sleep: true (是否启用睡眠功能)

[Sleepy State]
|-- 触发条件: 无操作时长 > idle_before_sleepy
     |
     v (随机判定: random() < sleep_probability)
     |-- 成功 -> 进入 [Nap Mode]
     \-- 失败 -> 保持待机，下次再判定

[Nap Mode - 小睡中]
|-- 角色切换 -> "打盹/趴睡" 图片
|-- AI生成睡眠表现 (轻量级/可缓存):
|    \-- 示例: "Zzz...", "呼噜~", "喵呜..."
|-- 小睡时长: random(nap_duration_range)
|-- 唤醒方式:
     |-- 用户点击/互动 -> 立即唤醒
     \-- 小睡时间到 -> 自然醒来

[Wake Up Event]
|-- 角色切换 -> "睡眼惺忪" -> "清醒" 动画
|-- 通过统一上下文管理器 (InteractionType: PROACTIVE)
|-- 场景模板: WAKE_UP
|-- 上下文注入:
|    |-- scene_type: "wake_up"
|    |-- wake_reason: "user_interaction" | "natural"
|    |-- nap_duration_minutes: 小睡时长
|    |-- time_of_day: 当前时间段
|    \-- user_activity: 用户正在做什么
|-- 回复指令: {prompt_templates.response_instructions.wake_up}
|-- AI生成起床语 (基于时间+唤醒方式):
     |-- 被用户唤醒: "唔...你叫我吗？"
     |-- 自然醒来: "啊...刚才睡着了吗？"
     |-- 深夜: "你还没睡呀？陪你熬夜吗..."
     \-- Fallback: wake_up.fallback_message
```

**配置文件** (`./config/sleep_settings.json`):

```json
{
  "enable_sleep": true,
  "idle_before_sleepy": 30,
  "sleep_probability": 0.3,
  "nap_duration_range": [5, 15],
  "sleepy_expressions": ["打哈欠", "揉眼睛"],
  "sleep_expressions": ["趴睡", "侧睡"],
  "wake_up": {
    "ai_generation": {
      "enabled": true,
      "style": "sleepy_cute",
      "consider_wake_reason": true
    },
    "time_hints": {
      "_comment": "为AI提供时间段参考，不是预设文本",
      "night": [0, 1, 2, 3, 4, 5],
      "morning": [6, 7, 8, 9],
      "day": [10, 11, 12, 13, 14, 15, 16, 17],
      "evening": [18, 19, 20, 21, 22, 23]
    },
    "fallback_message": "喵...睡醒了~"
  }
}
```

---

## 16. 程序快速启动器

> **AI驱动**: 启动反馈由AI生成，提供个性化响应

```
[Right-Click Menu]
|-- Menu Item: "管家服务"
     |
     v (Hover/Click)

[Launcher Submenu]
|-- 列出已配置的程序列表
|-- 数据源: ./config/launcher.json
     |
     v (Click 程序项)
     |-- 使用 subprocess / os.startfile 启动
     |-- 通过统一上下文管理器 (InteractionType: TOOL_EXECUTION)
     |-- 场景模板: LAUNCHER
     |-- 上下文注入:
     |    |-- scene_type: "launcher"
     |    |-- app_name, app_category
     |    |-- time_of_day, user_activity_state
     |    \-- launch_result: success/failure
     |-- 回复指令: {prompt_templates.response_instructions.launcher}
     |-- AI生成启动反馈:
     |    |-- 示例: "正在帮你打开{app_name}~稍等一下喵！"
     |    |-- 示例: "要用{app_name}工作吗？加油哦！"
     |    \-- 启动失败时: "唔...{app_name}打不开，是不是路径不对？"
     \-- 成功/失败 Toast 提示
```

**配置示例** (`launcher.json`):

```json
{
  "Chrome": {
    "path": "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "category": "browser",
    "icon": "🌐"
  },
  "VS Code": {
    "path": "C:/Users/{user}/AppData/Local/Programs/Microsoft VS Code/Code.exe",
    "category": "development",
    "icon": "💻"
  },
  "Steam": {
    "path": "D:/Steam/steam.exe",
    "category": "game",
    "icon": "🎮"
  }
}
```

---

## 17. 网站快捷访问

> **AI驱动**: 访问网站时提供个性化导航语

```
[Right-Click Menu]
|-- Menu Item: "书签/传送门"
     |
     v (Hover/Click)

[Bookmarks Submenu]
|-- 列出已配置的网站列表
|-- 数据源: ./config/bookmarks.json
     |
     v (Click 网站项)
     |-- 使用 webbrowser 库打开
     |-- 角色配合动作 (挥手/指向)
     |-- 通过统一上下文管理器 (InteractionType: TOOL_EXECUTION)
     |-- 场景模板: BOOKMARK
     |-- 上下文注入:
     |    |-- scene_type: "bookmark"
     |    |-- site_name, site_category, site_url
     |    \-- time_of_day
     |-- 回复指令: {prompt_templates.response_instructions.bookmark}
     |-- AI生成导航语:
     |    |-- B站: "去看视频吗？不要看太久哦~"
     |    |-- GitHub: "要写代码了吗？主人真厉害！"
     |    \-- 默认: "带你去{site_name}~"
```

**配置示例** (`bookmarks.json`):

```json
{
  "B站": {
    "url": "https://www.bilibili.com",
    "category": "video",
    "icon": "📺"
  },
  "GitHub": {
    "url": "https://github.com",
    "category": "development",
    "icon": "🐙"
  },
  "ChatGPT": {
    "url": "https://chat.openai.com",
    "category": "ai",
    "icon": "🤖"
  }
}
```

---

## 18. 猜拳与掷骰子

> 注：小游戏属于插件系统的一部分，详见 [插件系统架构](#插件系统架构)
> **AI驱动**: 游戏结果反馈由AI生成，经过统一上下文管理器处理

### 18.1 猜拳游戏

```
[Game Menu]
|-- Menu Item: "猜拳"
     |
     v (Click)

[Rock-Paper-Scissors Panel]
|-- 玩家选择: [石头] [剪刀] [布]
     |
     v (Click 出拳)
     |-- 程序随机生成角色出拳
     |-- 判断胜负 → 生成游戏上下文
     |-- 通过统一上下文管理器 (InteractionType: GAME_INTERACTION)
     |-- 场景模板: GAME_RESULT
     |-- 上下文注入:
     |    |-- game_name: 猜拳
     |    |-- player_choice, pet_choice, result
     |    |-- streak_info: 连胜/连败信息
     |    \-- 当前心情、好感度
     |-- 回复指令: {prompt_templates.response_instructions.game_result}
     |-- AI生成个性化反应:
          |-- Win (玩家赢) → AI生成沮丧/不服气的反应
          |    |-- 示例: "唔...又输了，再来一局！"
          |    |-- 示例: "运气好而已啦！下次绝对赢你！"
          |    \-- 示例: "好吧好吧，你赢了喵..."
          |-- Lose (玩家输) → AI生成得意/开心的反应
          |    |-- 示例: "耶！我赢啦！主人要请我吃小鱼干~"
          |    |-- 示例: "哈哈哈哈太简单了！"
          |    \-- 示例: "这局是我的！再来？"
          \-- Draw → AI生成惊讶/调侃的反应
               |-- 示例: "诶？心有灵犀吗？"
               |-- 示例: "竟然一样！再来再来！"
               \-- 示例: "平局！这说明我们很有默契喵~"
     |-- 表情/动画: 根据AI返回的emotion_tag自动匹配
     \-- 记忆写入: 聚合为"今天玩了N局猜拳"
```

### 18.2 掷骰子

```
[Game Menu]
|-- Menu Item: "掷骰子"
     |
     v (Click)

[Dice Roll Panel]
|-- "掷骰子" 按钮
     |
     v (Click)
     |-- 玩家骰子: random(1-100)
     |-- 角色骰子: random(1-100)
     |-- 生成游戏上下文 → 统一上下文管理器
     |-- 场景模板: GAME_RESULT
     |-- 上下文注入:
     |    |-- game_name: 掷骰子
     |    |-- player_roll, pet_roll, difference
     |    \-- is_large_margin: abs(difference) > 50
     |-- 回复指令: {prompt_templates.response_instructions.game_result}
     |-- AI生成个性化反应:
          |-- Player > Pet → AI生成认输/调侃反应
          |    |-- 示例: "哇{player_roll}！你运气也太好了吧！"
          |    |-- 示例: "我才{pet_roll}...骰子是不是坏了？"
          |    \-- 大比分差: "差这么多！你是欧皇吗？！"
          |-- Player < Pet → AI生成得意反应
          |    |-- 示例: "看我的{pet_roll}！完美~"
          |    \-- 大比分差: "{pet_roll}对{player_roll}，碾压！"
          \-- Equal → AI生成惊叹反应
               \-- 示例: "都是{player_roll}！这概率也太小了吧！"
     \-- 记忆写入: 聚合记录
```

**配置文件** (`./config/minigame_settings.json`):

```json
{
  "daily_reward_limit": 5,
  "reward_reset_time": "00:00",
  "show_remaining_rewards": true,
  "after_limit_behavior": "play_without_reward",
  
  "response_strategy": {
    "default_tier": 3,
    "_note": "此处default_tier可覆盖prompt_templates.json中scene_contexts.game_result.forced_tier",
    "tier_selection_rules": {
      "use_tier2_when": ["consecutive_games >= 5", "user_in_hurry", "api_latency_high"],
      "use_tier3_when": ["streak >= 3", "first_game_of_day", "special_outcome"]
    },
    "allow_plugin_override": true
  },
  
  "ai_generation": {
    "enabled": true,
    "use_unified_context_manager": true,
    "interaction_type": "GAME_INTERACTION",
    "include_streak_info": true,
    "include_mood_context": true,
    "max_response_length": 50
  },
  
  "fallback_messages": {
    "_comment": "仅在AI生成失败时使用",
    "win": ["你赢了！", "厉害！", "运气真好~"],
    "lose": ["我赢啦！", "哈哈~", "太简单了！"],
    "draw": ["平局！", "再来！", "竟然一样！"]
  },
  
  "rock_paper_scissors": {
    "win_coins": 5,
    "win_affinity": 1,
    "lose_coins": 0,
    "lose_affinity": 0,
    "prompt_context": {
      "game_name": "猜拳",
      "choices": ["石头", "剪刀", "布"],
      "result_types": ["win", "lose", "draw"]
    }
  },
  
  "dice_roll": {
    "dice_min": 1,
    "dice_max": 100,
    "win_coins": 10,
    "win_affinity": 2,
    "large_margin_threshold": 50,
    "prompt_context": {
      "game_name": "掷骰子",
      "include_margin_commentary": true
    },
    "enable_betting": false,
    "roll_animation": "actions/dice_roll"
  },
  
  "memory_aggregation": {
    "enable": true,
    "aggregate_to_daily_summary": true,
    "template": "今天和主人玩了{total_games}局游戏，{game_summary}"
  }
}
```

---

## 19. 本地文件整理

> **AI驱动**: 整理完成后的汇报由AI生成，提供个性化反馈

```
[Menu]
|-- Menu Item: "文件整理"
     |
     v (Click)

[File Organizer Dialog]
|-- 杂乱目录选择: (Folder Picker)
|-- 目标目录选择: (Folder Picker)
|-- "开始整理" 按钮
     |
     v (Click)

[Organizing Process]
|-- 扫描杂乱目录下所有文件
|-- 按后缀名分类移动:
|    |-- 图片 (.jpg, .png, .gif) -> /Images/
|    |-- 文档 (.doc, .pdf, .txt) -> /Documents/
|    |-- 压缩包 (.zip, .rar, .7z) -> /Archives/
|    \-- 其他 -> /Others/
|-- 进度条显示
     |
     v (完成)
     |-- 通过统一上下文管理器 (InteractionType: TOOL_EXECUTION)
     |-- 场景模板: TOOL_COMPLETE
     |-- 上下文注入:
     |    |-- tool_name: 文件整理
     |    |-- result: {total_count}个文件，分类详情
     |    \-- 上下文: 时间、用户状态
     |-- 回复指令: {prompt_templates.response_instructions.tool_complete}
     \-- AI生成个性化汇报:
          |-- 示例: "搞定！{count}个文件都整理好了~桌面清爽多了！"
          |-- 示例: "整理完毕！图片{img_count}张，文档{doc_count}份，主人的文件真多呀~"
          \-- 示例: "呼~终于整理完了！{count}个文件归位，我要休息一下喵..."
```

**配置文件** (`./config/file_organizer_settings.json`):

```json
{
  "enable_feature": true,
  "category_rules": {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"],
    "Documents": [".doc", ".docx", ".pdf", ".txt", ".md", ".xlsx", ".pptx"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv"],
    "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
    "Code": [".py", ".js", ".ts", ".java", ".cpp", ".c", ".h"]
  },
  "default_category": "Others",
  "skip_hidden_files": true,
  "confirm_before_move": true,
  "completion_animation": "actions/proud",
  
  "ai_generation": {
    "enabled": true,
    "use_unified_context_manager": true,
    "interaction_type": "TOOL_EXECUTION",
    "include_category_breakdown": true,
    "max_response_length": 80
  },
  
  "fallback_messages": {
    "_comment": "仅在AI生成失败时使用",
    "completion": "整理完成，共{count}个文件~"
  }
}
```

---

## 20. 商城与经济系统

```
[Economy System]
|-- 货币: 金币 (coins)
|-- 获取途径:
     |-- 专注时长: +{duration/10} 金币
     |-- 完成日程: +10 金币
     \-- 每日签到: +20 金币

[Menu]
|-- Menu Item: "商城"
     |
     v (Click)

[Shop Panel]
|-- 商品分类 Tab:
|    |-- 道具 (增加好感)
|    |-- 衣服 (切换图片组)
|    \-- 家具 (改变背景框)
|-- 商品列表:
     |-- [图标] + [名称] + [价格] + [购买按钮]
     |
     v (Click 购买)
     |-- 检查金币余额:
          |-- 足够 -> 扣除金币 + 添加物品 + Toast "购买成功"
          \-- 不足 -> Toast "金币不足"
```

**数据存储**: `./data/shop.json`, `./data/user_inventory.json`

**配置文件** (`./config/economy_settings.json`):

```json
{
  "currency_name": "金币",
  "currency_icon": "🪙",
  "initial_coins": 100,
  "earning_rules": {
    "focus_per_10min": 10,
    "schedule_complete": 10,
    "daily_checkin": 20,
    "random_event_bonus": 50,
    "minigame_win": 5
  },
  "daily_limits": {
    "focus_max_coins": 100,
    "minigame_reward_times": 5,
    "random_event_max": 3
  },
  "daily_checkin_streak_bonus": {
    "3_days": 10,
    "7_days": 30,
    "30_days": 100
  },
  "enable_coin_decay": false,
  "show_daily_summary": true
}
```

---

## 21. 网络延迟感知

> **AI驱动**: 网络状态变化时由 AI 根据上下文生成个性化吐槽，而非使用预设文本

```
[Network Monitor Thread]
|-- 执行 Ping 测试 (目标: baidu.com)
|-- 检测频率: 每30秒

[Network Status Changed]
|-- 状态变化检测 → 触发统一上下文管理器 (InteractionType: PROACTIVE)
|-- 场景模板: NETWORK_STATUS
|-- 上下文注入:
|    |-- scene_type: "network_status"
|    |-- status: "high_latency" | "disconnected" | "recovered"
|    |-- latency_ms: 具体延迟数值
|    |-- user_activity: 当前用户活动 (是否在看视频/下载等)
|    \-- emotion_state: 当前情绪
|-- 回复指令: {prompt_templates.response_instructions.network_status}

[AI Generation Flow]
|-- Latency > 500ms:
|    |-- 角色头上出现 "📶❌" 图标
|    |-- AI生成吐槽 (基于延迟值+用户活动):
|    |    \-- 示例: "这网速...主人是在用信鸽传输吗？"
|    \-- Fallback: 使用 response_fallback_chain
|-- 完全断网:
|    |-- 角色切换 -> "拿着线缆在修" 图片
|    |-- AI生成响应 (基于断网持续时间+历史频率):
|    |    \-- 示例: "信号又跑丢了！我去追追看~"
|    \-- Fallback: emergency_fallbacks.json
\-- 恢复正常:
     |-- 自动切回待机状态
     \-- AI生成庆祝 (如断网>1分钟)
```

**配置文件** (`./config/network_settings.json`):

```json
{
  "enable_network_monitor": true,
  "ping_target": "baidu.com",
  "ping_interval_seconds": 30,
  "high_latency_threshold_ms": 500,
  "disconnect_timeout_ms": 3000,
  "high_latency_expression": "worried",
  "disconnect_expression": "fixing_cables",
  "ai_generation": {
    "enabled": true,
    "context_hints": {
      "high_latency": "网络延迟，可根据具体ms数值和用户当前活动生成吐槽",
      "disconnect": "网络断开，可表现为修理/追逐信号等拟人化行为",
      "recovered": "网络恢复，根据断网时长决定庆祝程度"
    }
  },
  "_fallback_deprecated": "以下预设仅在emergency_fallbacks.json中使用"
}
```

---

## 22. 游戏模式侦测

> **AI驱动**: 游戏结束后的问候语由 AI 根据游戏时长和类型生成个性化内容

```
[Process Monitor Thread]
|-- 维护游戏进程白名单:
|    |-- "League of Legends.exe"
|    |-- "GenshinImpact.exe"
|    |-- "Valorant.exe"
|    \-- ... (可配置)
|-- 检测频率: 每10秒

[Gaming Mode - Detected]
|-- 记录游戏开始时间和游戏类型
|-- 自动静音角色闲聊功能
|-- 角色自动行为 (可选):
     |-- Option A: 最小化到系统托盘
     |-- Option B: 缩放到屏幕角落 (小尺寸)
     \-- Option C: 切换"加油"表情静默待命

[Gaming Mode - Exit]
|-- 检测到游戏进程关闭
|-- 计算游戏时长
|-- 通过统一上下文管理器 (InteractionType: PROACTIVE)
|-- 场景模板: GAMING_MODE_EXIT
|-- 上下文注入:
|    |-- scene_type: "gaming_mode_exit"
|    |-- game_name: 游戏名称
|    |-- game_duration_minutes: 游戏时长
|    |-- time_of_day: 当前时间段
|    \-- consecutive_sessions: 连续游戏场次
|-- 回复指令: {prompt_templates.response_instructions.gaming_mode_exit}
|-- AI生成问候:
|    |-- 短时间(< 30分钟): "这么快就结束了？打得顺利吗？"
|    |-- 中等时长(30-120分钟): "玩了一个多小时啦，要不要休息一下眼睛？"
|    |-- 长时间(> 120分钟): "主人玩了好久呢，手酸不酸？要喝点水吗？"
|    \-- 深夜游戏: "这么晚了还在打游戏...明天不用早起吗？"
\-- 自动恢复正常状态
```

**配置文件** (`./config/gaming_mode_settings.json`):

```json
{
  "enable_gaming_mode": true,
  "check_interval_seconds": 10,
  "game_whitelist": [
    "League of Legends.exe",
    "GenshinImpact.exe",
    "Valorant.exe",
    "PUBG.exe",
    "csgo.exe",
    "Overwatch.exe"
  ],
  "game_categories": {
    "moba": ["League of Legends.exe", "Dota2.exe"],
    "fps": ["csgo.exe", "Valorant.exe", "Overwatch.exe", "PUBG.exe"],
    "rpg": ["GenshinImpact.exe"]
  },
  "behavior_on_detect": "minimize_corner",
  "behavior_options": ["minimize_tray", "minimize_corner", "cheer_silent"],
  "corner_scale": 0.5,
  "corner_position": "bottom_right",
  "cheer_expression": "cheer",
  "ai_generation": {
    "enabled": true,
    "context_hints": {
      "exit_greeting": "根据游戏时长、游戏类型、当前时间生成个性化问候",
      "duration_thresholds": {
        "short": 30,
        "medium": 120,
        "long": 180
      }
    }
  }
}
```

```

---

## 23. 情绪状态机系统 (Mood State Machine)

> **设计升级**: 从简单数值变为完整状态机，支持状态转换逻辑和交叉影响
> **状态同步**: 添加状态持久化和同步机制，确保UI与内存状态一致

```

[Mood State Machine - Enhanced]
|
|-- 状态节点 (State Nodes):
|    |
|    |-- Happy (开心)
|    |    |-- 子状态: Excited (兴奋) / Content (满足)
|    |    |-- 表现: 微笑、活泼动画、主动发起话题
|    |    \-- 语气: 活泼、多用感叹号和emoji
|    |
|    |-- Normal (普通)
|    |    |-- 子状态: Relaxed (放松) / Focused (专注)
|    |    |-- 表现: 标准待机、正常响应
|    |    \-- 语气: 平和、自然
|    |
|    |-- Tired (疲惫)
|    |    |-- 子状态: Sleepy (困倦) / Exhausted (精疲力竭)
|    |    |-- 表现: 打哈欠、眼睛半闭、动作缓慢
|    |    \-- 语气: 简短、偶尔打哈欠
|    |
|    |-- Sad (难过)
|    |    |-- 子状态: Disappointed (失望) / Lonely (孤独)
|    |    |-- 表现: 低头、失落表情、减少主动互动
|    |    \-- 语气: 低落、短句
|    |
|    \-- Anxious (焦虑)
|         |-- 子状态: Worried (担心) / Nervous (紧张)
|         |-- 表现: 来回走动、小动作多
|         \-- 语气: 关心、询问较多
|
|-- 状态同步机制 (State Synchronization):
|    |
|    |-- 单一数据源 (Single Source of Truth):
|    |    |-- 所有状态存储在 StateStore 中
|    |    |-- UI组件订阅状态变化
|    |    |-- 禁止UI直接修改状态
|    |    \-- 通过Action触发状态变更
|    |
|    |-- 状态持久化与检查点 (State Persistence & Checkpoints):
|    |    |-- 持久化文件: ./data/user_state.json
|    |    |-- 检查点触发条件 (满足任一即保存):
|    |    |    |-- 状态变化时 (mood/energy/hunger/affinity变更)
|    |    |    |-- 每次对话结束后
|    |    |    |-- 工具执行成功后
|    |    |    |-- 定时保存 (间隔30秒)
|    |    |    \-- 程序正常退出时
|    |    |-- 保存内容:
|    |    |    |-- 核心状态: mood, energy, hunger, affinity, coins
|    |    |    |-- 位置信息: position, display_mode
|    |    |    |-- 会话状态: last_interaction_time, session_id
|    |    |    |-- 检查点元数据: checkpoint_id, timestamp, version
|    |    |    \-- 待处理队列: pending_reminders, pending_vectorization_count
|    |    |-- 启动恢复流程:
|    |    |    |-- 检查主状态文件是否存在且有效
|    |    |    |-- 有效 → 加载并恢复状态
|    |    |    |-- 损坏 → 尝试从备份恢复 (./data/user_state.backup.json)
|    |    |    \-- 备份也失败 → 使用默认值 + 日志警告
|    |    |-- 备份策略:
|    |    |    |-- 每次成功保存后，旧文件重命名为 .backup.json
|    |    |    |-- 保留最近1个备份
|    |    |    \-- 崩溃恢复: 程序异常退出后，下次启动检测并提示
|    |    \-- 版本兼容: 状态文件包含schema_version，支持迁移
|    |
|    |-- 内存缓存层 (Memory Cache Layer):
|    |    |-- 目的: 减少磁盘I/O，提升响应速度
|    |    |-- 实现: LRU Cache (最近使用的状态)
|    |    |-- 写策略: Write-Through (写入缓存同时写入持久化)
|    |    |-- 读策略: 优先读缓存，缓存未命中读文件
|    |    \-- 缓存失效: 文件变更时清除缓存
|    |
|    |-- 变更通知 (Change Notification):
|    |    |-- 状态变化触发事件: StateChangedEvent
|    |    |-- 订阅者: UI层、动画层、Agent循环、可观测性系统
|    |    |-- 支持批量更新 (避免频繁触发)
|    |    \-- 变更日志: 记录到追踪系统 (如已启用)
|    |
|    \-- 冲突处理 (Conflict Resolution):
|         |-- 并发写入: 使用时间戳，最新写入优先
|         |-- 范围约束: 自动裁剪超出范围的值
|         \-- 依赖检查: 状态A变化时检查是否需要联动更新状态B
|
|-- 情感强度解析机制 (Emotion Intensity Parsing):
|    |
|    |-- LLM输出格式强制约束:
|    |    |-- 在System Prompt中要求LLM输出结构化情感标签
|    |    |-- 格式: [EMOTION:tag:intensity] 在回复末尾
|    |    |-- 示例: "今天天气真好呢~ [EMOTION:happy:0.7]"
|    |    \-- intensity取值: 0.0-1.0 (浮点数)
|    |
|    |-- 解析流程:
|    |    |-- Step 1: 正则匹配 \[EMOTION:(\w+):([\d.]+)\]
|    |    |-- Step 2: 提取 emotion_tag 和 emotion_intensity
|    |    |-- Step 3: 从显示文本中移除标签
|    |    |-- Step 4: 验证intensity范围 [0, 1]
|    |    \-- Step 5: 传递给动画系统
|    |
|    |-- 降级策略 (解析失败时):
|    |    |-- 使用规则推断: 关键词匹配 → 默认intensity
|    |    |    |-- 检测到"!"/"！" → intensity += 0.2
|    |    |    |-- 检测到emoji → intensity += 0.1
|    |    |    |-- 检测到"..."/"唔" → intensity -= 0.2
|    |    |-- 默认值: emotion_tag = "neutral", intensity = 0.5
|    |    \-- 配置: enable_rule_fallback = true
|    |
|    \-- 用于动画系统:
|         |-- intensity < 0.3 → 轻微表情变化
|         |-- intensity 0.3-0.7 → 标准表情
|         |-- intensity > 0.7 → 夸张表情 + 特效
|
|-- 状态转换规则 (State Transitions): ⭐ 混合驱动架构
|    |
|    |-- ⚠️ 优先级原则: 规则层始终优先于LLM层
|    |    |-- 规则层触发时，LLM层判断被跳过
|    |    |-- LLM层仅处理规则层未覆盖的灰色地带
|    |    \-- 冲突时以规则层结果为准
|    |
|    |-- ⭐ 状态优先级矩阵 (State Priority Matrix):
|    |    |-- 不可覆盖状态 (Uncoverridable):
|    |    |    |-- Tired (energy < 20): 能量极低时强制疲惫，情绪事件无法覆盖
|    |    |    |    \-- ⭐ 注: 数值变化(如喂食恢复能量)可触发状态重新评估，不属于"覆盖"
|    |    |    \-- Sleeping: 睡眠状态仅能被用户交互打断
|    |    |-- 可覆盖状态 (Overridable):
|    |    |    |-- Tired (hour >= 23 AND energy >= 20): 深夜疲惫可被强正面事件覆盖
|    |    |    |-- Sad: 可被连续正面交互恢复
|    |    |    \-- Anxious: 可被用户安抚恢复
|    |    |-- 情绪覆盖条件 (满足任一即可 - OR关系):
|    |    |    |-- 正面事件强度 >= 0.8 (emotion_intensity)
|    |    |    |-- 连续正面交互 >= 3次
|    |    |    \-- 用户主动安抚行为 (抚摸/喂食/关心对话 任一)
|    |    |-- ⭐ 数值恢复与情绪覆盖的区别:
|    |    |    |-- 情绪覆盖: 通过情感事件改变状态 (受优先级矩阵约束)
|    |    |    \-- 数值恢复: 通过喂食/休息等改变energy/hunger值，触发状态重新评估 (不受覆盖限制)
|    |    \-- 优先级数值: Sleeping(100) > Tired_Low_Energy(90) > Anxious(50) > Sad(40) > Tired_Night(30) > Normal(0)
|    |
|    |-- 【规则层 - 硬约束】确定性转换，不依赖LLM:
|    |    |
|    |    |-- Normal → Tired (规则驱动)
|    |    |    |-- 条件: energy < 30 OR hour >= 23
|    |    |    |-- 计算: 确定性判断，立即生效
|    |    |    \-- 效果: 切换疲惫表情，减少主动行为
|    |    |
|    |    |-- Tired → Sleeping (规则驱动)
|    |    |    |-- 条件: energy < 20 AND hour >= 23 AND idle_minutes > 10
|    |    |    |-- 计算: 确定性判断
|    |    |    \-- 效果: 进入睡眠模式
|    |    |
|    |    |-- Any → Tired (规则驱动)
|    |    |    |-- 条件: energy < 20 (任何时间)
|    |    |    \-- 效果: 强制切换到疲惫状态
|    |    |
|    |    \-- 能量/饥饿恢复 (规则驱动)
|    |         |-- 喂食: energy += item.energy_restore, hunger -= item.hunger_restore
|    |         |-- 休息: energy += 5/小时 (待机时)
|    |         \-- 约束: 0 <= energy <= 100, 0 <= hunger <= 100
|    |
|    |-- 【LLM层 - 软决策】情感细微调整，需要上下文理解:
|    |    |
|    |    |-- Happy ↔ Excited (LLM辅助 + intensity判断)
|    |    |    |-- 触发: 好感度提升 + 连续正面互动 (3次以上)
|    |    |    |-- LLM判断: 输出 [EMOTION:happy:X]，当X > 0.8时升级到Excited
|    |    |    \-- 效果: 播放庆祝动画，增加主动事件概率
|    |    |
|    |    |-- Normal → Sad (LLM辅助)
|    |    |    |-- 触发条件: 连续负面事件 (2次) OR 被忽视 (3小时)
|    |    |    |-- LLM判断: 分析用户态度，判断是否真的冷落
|    |    |    \-- 效果: 降低主动行为概率
|    |    |
|    |    |-- Any → Anxious (LLM辅助)
|    |    |    |-- 触发条件: 检测到用户异常行为 (深夜工作、系统卡顿)
|    |    |    |-- LLM判断: 评估是否应该表达担心
|    |    |    \-- 效果: 增加关心提醒频率
|    |    |
|    |    \-- Sad/Anxious → Happy (LLM辅助)
|    |         |-- 触发: 用户抚摸 + 喂食 + 正面对话
|    |         |-- LLM判断: 评估恢复程度，决定情绪回升速度
|    |         \-- 效果: 播放恢复动画，表达感谢
|    |
|    |-- 【平滑过渡机制】避免状态抖动:
|    |    |-- 状态变化需要持续满足条件 >= 30秒
|    |    |-- 快速来回切换保护: 同一状态对60秒内不可重复切换
|    |    \-- 情绪惯性: new_mood = current_mood *0.7 + target_mood* 0.3
|    |
|    \-- Happy → Normal (规则驱动)
|         |-- 触发: 自然衰减 (2小时无强化)
|         \-- 效果: 平滑过渡动画
|
|-- 交叉影响因素 (Cross Factors):
|    |-- 能量值 (Energy): 影响 Tired 状态阈值
|    |-- 饥饿度 (Hunger): 低于30%增加负面情绪概率
|    |-- 好感度 (Affinity): 高好感度增加情绪恢复速度
|    \-- 时间段 (Time): 深夜自动增加疲惫倾向

```

**状态转换事件**:

```

[State Transition Events]
|
|-- 转换发生时:
|    |-- 记录: 状态变化写入Tier 3记忆
|    |-- 通知: 生成TransitionEvent供AI参考
|    |-- 动画: 播放过渡动画 (如有)
|    \-- 行为: 更新行为策略参数
|
|-- TransitionEvent结构:
|    |-- from_state: 原状态
|    |-- to_state: 新状态
|    |-- trigger: 触发原因
|    |-- timestamp: 发生时间
|    \-- context: 相关上下文

```

**配置文件** (`./config/emotion_settings.json`):

```json
{
  "state_machine": {
    "initial_state": "Normal",
    "states": ["Happy", "Normal", "Tired", "Sad", "Anxious"],
    "sub_states": {
      "Happy": ["Excited", "Content"],
      "Normal": ["Relaxed", "Focused"],
      "Tired": ["Sleepy", "Exhausted"],
      "Sad": ["Disappointed", "Lonely"],
      "Anxious": ["Worried", "Nervous"]
    },
    "state_priority": {
      "Sleeping": 100,
      "Tired_LowEnergy": 90,
      "Anxious": 50,
      "Sad": 40,
      "Tired_Night": 30,
      "Normal": 0,
      "Happy": 10,
      "Excited": 20
    },
    "uncoverridable_conditions": {
      "Tired": "energy < 20",
      "Sleeping": "is_sleeping == true"
    },
    "override_requirements": {
      "min_positive_intensity": 0.8,
      "min_consecutive_positive_interactions": 3,
      "comfort_actions": ["pet", "feed", "caring_dialogue"]
    }
  },
  
  "emotion_intensity_parsing": {
    "enable": true,
    "output_format": "[EMOTION:tag:intensity]",
    "regex_pattern": "\\[EMOTION:(\\w+):([\\d.]+)\\]",
    "strip_from_display": true,
    "valid_tags": ["happy", "excited", "sad", "angry", "shy", "surprised", "tired", "anxious", "neutral"],
    "intensity_range": [0.0, 1.0],
    "rule_fallback": {
      "enable": true,
      "exclamation_boost": 0.2,
      "emoji_boost": 0.1,
      "ellipsis_reduce": 0.2,
      "default_tag": "neutral",
      "default_intensity": 0.5
    },
    "intensity_thresholds": {
      "subtle": 0.3,
      "standard": 0.7,
      "exaggerated": 1.0
    },
    "prompt_instruction": "在回复末尾添加情感标签，格式: [EMOTION:情感:强度]，如 [EMOTION:happy:0.7]"
  },
  
  "transitions": {
    "Happy_to_Excited": {
      "conditions": ["affinity_up", "positive_interactions >= 3", "emotion_intensity > 0.8"],
      "probability": 0.7
    },
    "Normal_to_Tired": {
      "conditions": ["energy < 30", "OR", "hour >= 23"],
      "probability": 1.0
    },
    "Any_to_Anxious": {
      "conditions": ["user_late_night_work", "OR", "system_stressed"],
      "probability": 0.5
    }
  },
  
  "cross_factors": {
    "energy_tired_threshold": 30,
    "hunger_negative_threshold": 30,
    "affinity_recovery_bonus": 0.2,
    "night_fatigue_hours": [23, 24, 0, 1, 2, 3, 4, 5]
  },
  
  "decay_settings": {
    "happy_decay_hours": 2,
    "sad_recovery_hours": 4,
    "natural_decay_per_hour": 3
  },
  
  "state_sync": {
    "persistence_file": "./data/user_state.json",
    "backup_file": "./data/user_state.backup.json",
    "auto_save_interval_seconds": 30,
    "save_on_change": true,
    "save_on_conversation_end": true,
    "save_on_tool_success": true,
    "enable_backup": true,
    "backup_on_save": true,
    "schema_version": "1.0",
    "enable_memory_cache": true,
    "cache_size": 100,
    "enable_change_log": true,
    "change_log_to_trace": true,
    "batch_update_delay_ms": 100,
    "crash_recovery": {
      "enable": true,
      "detect_abnormal_exit": true,
      "show_recovery_prompt": true
    },
    "default_state_on_corruption": {
      "mood": "Normal",
      "energy": 80,
      "hunger": 20,
      "affinity": 50,
      "coins": 100
    }
  },
  
  "smooth_transition": {
    "min_condition_duration_seconds": 30,
    "switch_protection_seconds": 60,
    "inertia_factor": 0.7
  },
  
  "mood_expressions": {
    "Happy": ["smile", "excited"],
    "Normal": ["idle", "relaxed"],
    "Tired": ["yawn", "sleepy"],
    "Sad": ["sad", "disappointed"],
    "Anxious": ["worried", "nervous"]
  },
  
  "mood_prompt_modifiers": {
    "Happy": "用活泼开心的语气回复，可以用emoji",
    "Excited": "非常兴奋和热情，表达更夸张",
    "Normal": "",
    "Tired": "用简短的语气回复，偶尔打哈欠",
    "Sad": "用低落、简短的语气回复",
    "Anxious": "表现出担心和关心，多问候用户状况"
  },
  
  "behavior_modifiers": {
    "Happy": {
      "idle_chat_frequency": 1.5,
      "proactive_event_probability": 1.3
    },
    "Tired": {
      "idle_chat_frequency": 0.5,
      "proactive_event_probability": 0.3
    },
    "Sad": {
      "idle_chat_frequency": 0.7,
      "proactive_event_probability": 0.5
    }
  }
}
```

---

## 24. 随手记/便签条

> **AI驱动**: 便签回忆由 AI 结合笔记内容和当前上下文生成个性化提醒

```

[Menu]
|-- Menu Item: "记一笔"
     |
     v (Click)

[Quick Note Panel]
|-- 半透明小输入框
|-- "保存" 按钮
     |
     v (Click 保存)
     |-- 追加内容到 ./data/notes.txt
     |-- Toast "已记录"
     \-- 关闭面板

[Note Recall - Random]
|-- 角色不定时随机读取一条笔记
|-- 通过统一上下文管理器 (InteractionType: PROACTIVE)
|-- 场景模板: NOTE_RECALL
|-- 上下文注入:
|    |-- scene_type: "note_recall"
|    |-- note_content: 笔记内容
|    |-- note_age_days: 笔记距今天数
|    |-- note_keywords: 关键词提取
|    \-- current_context: 当前用户活动
|-- 回复指令: {prompt_templates.response_instructions.note_recall}
|-- AI生成提醒:
|    |-- 近期笔记: "对了，你昨天记了这个：'{content}'，还记得吗？"
|    |-- 久远笔记: "翻到一条老笔记了！是{n}天前记的：'{content}'"
|    |-- 相关性提醒: "你现在在做的事，好像跟之前记的这个有关系..."
|    \-- Fallback: emergency_fallbacks.json

```

**配置文件** (`./config/notes_settings.json`):

```json
{
  "notes_file_path": "./data/notes.txt",
  "max_notes_count": 500,
  "enable_random_recall": true,
  "recall_interval_minutes": 120,
  "recall_probability": 0.3,
  "input_placeholder": "随手记点什么...",
  "window_opacity": 0.9
}
```

---

## 25. 本地天气感知

```
[Weather Service]
|-- 接入免费天气API (如 wttr.in)
|-- 获取频率: 每小时

[Weather State]
|-- 晴天 (Clear):
     \-- 正常待机状态
|-- 雨天 (Rain):
     |-- 角色图片图层叠加 "打伞" PNG
     \-- 可选: 桌面生成雨滴特效
|-- 雪天 (Snow):
     |-- 角色切换 "穿冬装" 图片
     \-- 可选: 桌面生成雪花特效
|-- 极端天气 (Storm/Heat):
     \-- 角色发出相应吐槽
```

**配置文件** (`./config/weather_settings.json`):

```json
{
  "enable_weather": true,
  "api_url": "https://wttr.in/{city}?format=j1",
  "city": "Beijing",
  "update_interval_minutes": 60,
  "enable_effects": true,
  "weather_expressions": {
    "Clear": "idle",
    "Rain": "umbrella",
    "Snow": "winter_coat",
    "Storm": "scared",
    "Cloudy": "idle"
  },
  "weather_comments": {
    "Clear": "今天天气真好~",
    "Rain": "下雨了，记得带伞哦",
    "Snow": "下雪了！好冷啊",
    "Storm": "外面风好大...好可怕",
    "Hot": "好热啊...要融化了"
  },
  "temperature_thresholds": {
    "hot": 35,
    "cold": 5
  }
}
```

---

## 26. 彩蛋与隐藏指令

```
[Easter Eggs]
|-- 连续点击 10 次:
     \-- 触发特殊动画/语音
|-- 拖拽角色到屏幕外再拉回:
     \-- 角色: "你想把我扔掉吗？！"
|-- 特定日期 (生日/节日):
     \-- 自动触发节日特效

[Hidden Commands]
|-- 输入 "/dance":
     \-- 角色播放跳舞动画
|-- 输入 "/secret":
     \-- 解锁隐藏对话

[Interaction Features]
|-- 显示模式切换: 悬浮模式 ↔ 任务栏行走模式 (快捷键/菜单切换)
|-- 悬浮吸附: 拖拽到屏幕边缘时自动吸附
|-- 换装系统: 商城购买后可切换服装
|-- 抚摸反馈: 鼠标滑过 -> 角色害羞表情
\-- 成长系统: 根据互动天数变化形态
```

**配置文件** (`./config/easter_eggs_settings.json`):

```json
{
  "click_combo_trigger": 10,
  "click_combo_action": "special_animation",
  "drag_off_screen": {
    "ai_generation": {
      "enabled": true,
      "context_hints": "用户试图把桌宠拖出屏幕，表现委屈/愤怒/撒娇等情绪"
    }
  },
  "special_dates": [
    { "date": "01-01", "event": "new_year", "context_hint": "新年第一天" },
    { "date": "02-14", "event": "valentine", "context_hint": "情人节" },
    { "date": "12-25", "event": "christmas", "context_hint": "圣诞节" }
  ],
  "special_date_ai": {
    "enabled": true,
    "consider_relationship_level": true,
    "consider_interaction_history": true
  },
  "master_birthday_event": true,
  "hidden_commands": {
    "/dance": "dance_animation",
    "/secret": "unlock_secret_dialogue",
    "/debug": "show_debug_panel"
  },
  "pet_touch_expression": "shy",
  "growth_milestones": [
    { "days": 7, "stage": "familiar", "unlock": "new_outfit_1" },
    { "days": 30, "stage": "close", "unlock": "new_outfit_2" },
    { "days": 100, "stage": "bonded", "unlock": "special_form" }
  ]
}
```

---

# 第二部分：进阶复杂功能

> 特点：需要配置环境、依赖高延迟API或复杂逻辑

---

## 1. 观察日记生成

```
[Data Collection]
|-- 滚动日志系统: 记录最近3天交互
|    |-- 专注时长
|    |-- 喂食记录
|    |-- 心情变化
|    \-- 重要对话摘要

[Menu]
|-- Menu Item: "生成观察日记"
     |
     v (Click)

[Diary Generation]
|-- 将原始数据发送给API
|-- Prompt: "以第一人称口吻写一篇关于用户的观察日记"
|-- 字数: 200-500字
     |
     v (API Response)

[Diary Display]
|-- 日期标题: {today}
|-- 日记内容 (Markdown渲染)
\-- "保存到本地" 按钮
```

---

## 2. 本地TTS语音 (口型同步)

```
[TTS Pipeline]
|-- 接入模型: GPT-SoVITS / VITS
|-- 输入: 文本回复内容
     |
     v (调用本地TTS接口)
     |-- 生成 WAV 音频文件
     |
     v (音频分析)
     |-- 算法分析音频振幅 (Volume)
     |-- 根据音量大小实时控制嘴部图片
          |-- Volume > Threshold -> 嘴巴张开
          \-- Volume <= Threshold -> 嘴巴闭合
     |
     v (同步播放)
     |-- 播放音频
     \-- 同步切换嘴部图片 (视觉口型对齐)
```

**技术难点**: 音频振幅分析 + 图片切换时序同步

---

## 3. 屏幕视觉监控 (Vision)

```
[Quick Access Bar]
|-- Button: "看屏幕"
     |
     v (Click)

[Screen Capture]
|-- 使用 pyautogui 截取当前屏幕
|-- 压缩图片 + 转码 Base64
     |
     v (API Request)
     |-- 发送至 Vision 大模型 (GPT-4V / Claude Vision)
     |-- Prompt: "这是我现在的屏幕，请吐槽或辅助我"
     |
     v (API Response)

[Display Result]
\-- 展示AI的屏幕分析/建议
```

---

## 4. 长期记忆 (向量检索)

```
[Memory Storage]
|-- 向量数据库: ChromaDB / FAISS
|-- 存储内容: 对话摘要向量

[Conversation Flow]
|-- 用户发起新话题
     |
     v (Vector Search)
     |-- 计算相似度 (余弦相似度)
     |-- 检索最相似的历史记忆 (Top 3)
     |
     v (Context Injection)
     |-- 将检索结果注入 Prompt
     \-- 角色能回忆起很久以前的对话细节
```

---

## 5. 媒体/音乐嗅探

```
[Media Monitor]
|-- 调用 Windows Media API / 浏览器标题抓取
|-- 检测媒体播放状态变更
     |
     v (Detected: 正在播放)
     |-- 获取: "歌名 - 歌手"
     |
     v (API Request)
     |-- Prompt: "我正在听《{song}》，发表一下感想吧"
     |
     v (API Response)

[Display]
\-- 角色发表听歌感想气泡
```

---

## 6. 实时语音通话

```
[Voice Pipeline]
|-- 组件:
     |-- VAD (静音检测)
     |-- Whisper (STT 语音转文字)
     |-- LLM (大语言模型)
     \-- TTS (文字转语音)

[Conversation Flow]
|-- 按下快捷键 (Push-to-Talk)
     |
     v (Recording)
     |-- 录制用户语音
     |
     v (VAD 检测停止)
     |
     v (Whisper STT)
     |-- 语音 -> 文字
     |
     v (LLM Processing)
     |-- 生成回复
     |
     v (TTS)
     |-- 文字 -> 语音
     |
     v (Playback)
     \-- 播放语音回复
```

**技术难点**: 延迟优化 (目标 < 2秒)

---

## 7. 多角色联动与互动选择

```
[IPC Mechanism]
|-- 通信方式:
     |-- Option A: 本地端口 (Socket, 17600-17610)
     \-- Option B: 共享状态文件 (./data/multi_pet_state.json)

[Multi-Pet Discovery]
|-- 程序启动时扫描端口/状态文件
|-- 发现其他在线桌宠
     |
     v (构建在线列表)
     |-- Pet List: [{id, name, character_type, position, mood}, ...]
     \-- 更新频率: 每5秒

[Interaction Target Selection] ← 互动目标选择
|-- 触发方式:
|    |-- 方式1: 右键菜单 -> "互动对象" -> 选择目标
|    |-- 方式2: 拖拽本桌宠靠近目标桌宠 (距离<100px)
|    \-- 方式3: 使用指令 "/interact [目标名称]"
|
|-- [Target Selection Menu]
     |-- 显示所有在线桌宠列表
     |-- 每项显示: [头像] + [名称] + [当前状态]
     |-- 点击选择目标
          |
          v (已选择目标)
          |-- 在界面上显示当前互动对象: "正在与 [名称] 互动"
          |-- 后续互动指令自动发送给该目标
          \-- "取消互动" 按钮 -> 回到独立模式

[Multi-Pet Interaction]
|-- Pet A 向 Pet B 发起互动
     |
     v (读取彼此状态)
     |-- 交换: 位置、心情、当前动作、对话历史摘要
     |
     v (联动行为)
     |-- 两个OC互相"对话"
     |    |-- Pet A: "你好呀~"
     |    \-- Pet B: "嗨！今天心情不错~"
     |-- 两个OC互相"打闹"
     |    |-- 触发条件: 两者距离<50px + mood=Happy
     |    \-- 同步播放 "play_fight" 动画
     |-- 共享事件触发
     |    |-- 随机事件可能影响多个桌宠
     |    \-- 协作任务: 两个桌宠一起完成某个目标
     |
     v (互动结束)
     |-- 双方好感度 +2
     \-- 记录互动次数到 ./data/interaction_log.json

[Interaction Types]
|-- 1对1互动: 主动选择一个目标
|-- 1对多广播: 发送消息给所有在线桌宠
|-- 群组互动: 3个以上桌宠的集体事件
\-- 自动互动: 距离接近时自动触发简短对话
```

**配置文件更新** (`./config/multi_pet_settings.json`):

```json
{
  "enable_multi_pet": true,
  "max_pets": 5,
  "discovery_method": "socket",
  "socket_port_range": [17600, 17610],
  "state_file_path": "./data/multi_pet_state.json",
  "update_interval_seconds": 5,
  
  "interaction_target_selection": {
    "enable_manual_selection": true,
    "enable_proximity_auto": true,
    "proximity_threshold_px": 100,
    "show_target_indicator": true,
    "indicator_style": "arrow_pointing"
  },
  
  "interaction_types": {
    "chat": {
      "enabled": true,
      "affinity_bonus": 2,
      "cooldown_minutes": 5
    },
    "play_fight": {
      "enabled": true,
      "trigger_distance_px": 50,
      "required_mood": ["Happy", "Excited"],
      "animation": "actions/play_fight"
    },
    "shared_event": {
      "enabled": true,
      "event_probability": 0.1
    }
  },
  
  "auto_interaction": {
    "enable_proximity_chat": true,
    "proximity_chat_distance_px": 80,
    "proximity_chat_messages": [
      "嗨~你也在这里呀",
      "要一起玩吗？",
      "好巧啊~"
    ]
  },
  
  "interaction_log_path": "./data/interaction_log.json",
  "max_log_entries": 1000
}
```

---

# 第三部分：插件系统架构

> 特点：模块化设计，支持热插拔，便于社区扩展

---

## 插件系统架构

```
[Plugin Architecture]
|-- 核心理念: 游戏及扩展功能均以插件形式存在
|-- 支持热加载/卸载
|-- 插件间隔离，互不影响
\-- 统一的插件API接口

[Plugin Types]
|-- game: 小游戏插件 (猜拳、骰子、更多...)
|-- tool: 工具插件 (文件整理、翻译...)
|-- effect: 特效插件 (天气、节日...)
|-- integration: 集成插件 (音乐嗅探、系统监控...)
\-- custom: 自定义插件

[Plugin Lifecycle]
|-- onLoad: 插件加载时
|-- onEnable: 插件启用时
|-- onDisable: 插件禁用时
|-- onUnload: 插件卸载时
\-- onUpdate: 每帧/定时更新

[Plugin API]
|-- pet.say(message): 让宠物说话
|-- pet.playAnimation(name): 播放动画
|-- pet.setExpression(name): 设置表情
|-- economy.addCoins(amount): 增加金币
|-- economy.removeCoins(amount): 扣除金币
|-- affinity.add(amount): 增加好感度
|-- ui.showDialog(options): 显示对话框
|-- ui.showMenu(items): 显示菜单
|-- storage.get(key): 读取插件数据
|-- storage.set(key, value): 保存插件数据
\-- events.on(eventName, handler): 监听事件
```

**插件目录结构**:

```
./plugins/
|-- games/                   # 游戏插件目录
|    |-- rock_paper_scissors/
|    |    |-- plugin.json    # 插件清单
|    |    |-- main.py        # 插件主逻辑
|    |    \\-- assets/        # 插件资源
|    |-- dice_roll/
|    |-- card_game/          # 未来扩展
|    \\-- ...
|-- tools/
|    |-- file_organizer/
|    \\-- translator/
|-- effects/
|    |-- weather/
|    \\-- festival/
\\-- custom/
     \\-- user_plugins/
```

**插件清单** (`plugin.json` 示例):

```json
{
  "id": "rock_paper_scissors",
  "name": "猜拳游戏",
  "version": "1.0.0",
  "author": "Rainze Team",
  "description": "经典的石头剪刀布游戏",
  "type": "game",
  "entry": "main.py",
  "menu_entry": {
    "label": "猜拳",
    "icon": "✊",
    "category": "games"
  },
  "permissions": [
    "economy.read",
    "economy.write",
    "affinity.write",
    "ui.dialog"
  ],
  "config_schema": {
    "win_coins": { "type": "number", "default": 5 },
    "win_affinity": { "type": "number", "default": 1 }
  },
  "dependencies": [],
  "min_app_version": "1.0.0"
}
```

**全局插件配置** (`./config/plugin_settings.json`):

```json
{
  "enable_plugins": true,
  "plugin_directories": ["./plugins"],
  "auto_load_plugins": true,
  "disabled_plugins": [],
  "plugin_update_check": true,
  "sandbox_mode": true,
  "max_plugin_memory_mb": 100,
  "plugin_timeout_seconds": 30,
  "community_plugins_url": "https://rainze-plugins.example.com/registry"
}
```

---

# 附录：数据结构规范

## 技术栈摘要

| 组件 | 技术方案 | 说明 |
|------|----------|------|
| **向量索引** | FAISS (可选) | 本地运行、无需服务器、全异步向量化(零阻塞) |
| **关系存储** | SQLite + FTS5 | 结构化查询 + 全文搜索 (主检索策略) |
| **加密方案** | SQLCipher (可选) | AES-256加密 |
| **记忆架构** | 3层简化模型 | Identity/Working/Long-term (Facts+Episodes+Relations) |
| **记忆检索** | FTS5优先 + 向量回退 + 阈值门控 | 解决异步向量化漏检 + 避免幻觉 |
| **矛盾检测** | 规则检测 + Reflection | 避免合并矛盾记忆 |
| **响应策略** | 混合分层 (Tier1/2/3) | 模板 + 规则 + LLM |
| **降级策略** | Fallback 1-5 链 | AI → Cache → LocalLLM(可选) → Template → Fallback |
| **Agent循环** | Workflow优先架构 | 单步操作用Workflow，多步推理用Agent |
| **动画系统** | 6层叠加 | Base/Idle/Expression/Action/Effect/LipSync |
| **状态机** | 混合驱动 (5态+子态) | 规则层优先 + LLM层软决策 + 状态优先级矩阵 + 状态同步 |
| **工具调用** | ReAct模式 + 注意力管理 | 提醒/天气/启动/笔记 + 重试/缓存/确认 |
| **反馈系统** | 隐式+显式 | 优化记忆重要度与响应质量 |
| **可观测性** | 追踪 + 指标 + 监控 | 执行路径追踪、性能指标、错误监控、日报生成 |
| **检查点** | 多触发 + 备份 + 缓存 | 状态变化/对话结束/工具成功/定时保存 |

---

## 配置文件清单

### 核心配置 (./config/)

| 文件路径 | 用途 | 格式 | 版本 |
|---------|------|------|------|
| `./config/system_prompt.txt` | 核心人设 | Plain Text | v1.0 |
| `./config/generation_settings.json` | 混合响应策略配置 (Tier1/2/3 + Fallback链) | JSON | v2.3 |
| `./config/memory_settings.json` | 3层记忆系统配置 (FTS5优先+异步向量化+回退机制) | JSON | v3.0 |
| `./config/context_settings.json` | 上下文管理 + Prompt配置 (Token预算可配置) | JSON | v2.3 |
| `./config/context_manager_settings.json` | 统一上下文管理器配置 | JSON | v2.3 |
| `./config/conversation_settings.json` | 用户主动对话配置 (含提示词模板) | JSON | v2.3 |
| `./config/agent_loop_settings.json` | Agent自主循环配置 (Workflow/Agent模式) | JSON | v2.2 |
| `./config/reflection_settings.json` | 记忆反思机制 | JSON | v2.0 |
| `./config/privacy_settings.json` | 隐私保护层 | JSON | v2.0 |
| `./config/animation_settings.json` | 动画系统架构 | JSON | v2.0 |
| `./config/emotion_settings.json` | 情绪状态机 (混合驱动+规则优先+状态同步) | JSON | v2.3 |
| `./config/tool_settings.json` | Tool Use工具调用配置 (含注意力管理) | JSON | v2.2 |
| `./config/feedback_settings.json` | 用户反馈循环配置 | JSON | v2.1 |
| `./config/observability_settings.json` | 可观测性与监控系统配置 (追踪/指标/错误) | JSON | v3.0.2 |
| `./config/prompt_templates.json` | 统一Prompt模板系统(用户核心配置) | JSON | v2.3.1 |
| `./config/api_settings.json` | API消费控制与开关 (频率限制/Token上限/场景开关) | JSON | v2.3 |
| `./config/chat_settings.json` | 聊天记录设置 | JSON | v1.0 |
| `./config/chime_settings.json` | 整点报时设置 | JSON | v1.0 |
| `./config/focus_settings.json` | 专注时钟设置(含黑名单+AI警告) | JSON | v2.3 |
| `./config/affinity_settings.json` | 好感度体系设置 | JSON | v1.0 |
| `./config/schedule_settings.json` | 日程提醒设置 | JSON | v1.0 |
| `./config/random_event_settings.json` | 随机事件设置 | JSON | v1.0 |
| `./config/multi_pet_settings.json` | 多角色联动与召唤 | JSON | v1.0 |
| `./config/plugin_settings.json` | 插件系统配置 | JSON | v1.0 |
| `./config/idle_chat_settings.json` | 闲聊陪伴设置 | JSON | v1.0 |
| `./config/physics_settings.json` | 物理交互设置 | JSON | v1.0 |
| `./config/system_monitor_settings.json` | 系统监控+主动场景识别 | JSON | v2.0 |
| `./config/clipboard_settings.json` | 剪贴板互动设置 | JSON | v1.0 |
| `./config/sleep_settings.json` | 昼夜作息设置 | JSON | v2.3 |
| `./config/launcher.json` | 程序启动器 | JSON | v2.3 |
| `./config/bookmarks.json` | 网站书签 (含分类和图标) | JSON | v2.3 |
| `./config/minigame_settings.json` | 小游戏设置 | JSON | v2.3 |
| `./config/file_organizer_settings.json` | 文件整理设置 | JSON | v2.3 |
| `./config/economy_settings.json` | 经济系统设置 | JSON | v1.0 |
| `./config/network_settings.json` | 网络监控设置 | JSON | v2.3 |
| `./config/gaming_mode_settings.json` | 游戏模式设置(含白名单+AI问候) | JSON | v2.3 |
| `./config/notes_settings.json` | 便签功能设置(AI回忆) | JSON | v2.3 |
| `./config/weather_settings.json` | 天气感知设置 | JSON | v1.0 |
| `./config/easter_eggs_settings.json` | 彩蛋系统设置 | JSON | v2.3 |
| `./config/scene_rules.json` | 场景分类规则 (Tier判断) | JSON | v2.2 |
| `./config/simple_templates.json` | Tier1模板响应库 | JSON | v2.2 |
| `./config/generation_rules.json` | Tier2规则生成配置 | JSON | v2.2 |

### 数据存储 (./data/)

| 文件路径 | 用途 | 格式 | 版本 |
|---------|------|------|------|
| `./data/memory.db` | 混合存储数据库 (SQLite+FTS5) | SQLite | v2.2 |
| `./data/memory.faiss` | 向量索引文件 (可选) | FAISS | v2.0 |
| `./data/memory_ids.pkl` | 向量ID映射 | Pickle | v2.0 |
| `./data/pending_vectorization.json` | 待向量化队列 | JSON | v2.2 |
| `./data/archive/` | 归档记忆目录 | JSON | v2.0 |
| `./data/feedback_log.json` | 用户反馈记录 | JSON | v2.1 |
| `./data/feedback_reports/` | 反馈分析报告目录 | JSON | v2.1 |
| `./data/trace_logs/` | 执行追踪日志目录 | JSONL | v3.0.2 |
| `./data/error_logs/` | 错误日志目录 | JSONL | v3.0.2 |
| `./data/metrics/` | 性能指标数据目录 | JSON | v3.0.2 |
| `./data/daily_reports/` | 每日统计报告目录 | JSON | v3.0.2 |
| `./readme.md` | 动态说明书 | Markdown | v1.0 |
| `./data/master_profile.json` | 用户档案 | JSON | v1.0 |
| `./data/chat_history.json` | 聊天记录 | JSON | v1.0 |
| `./data/items.json` | 物品数据库 | JSON | v1.0 |
| `./data/user_state.json` | 用户状态(好感/金币等) | JSON | v2.2 |
| `./data/notes.txt` | 便签记录 | Plain Text | v1.0 |
| `./data/shop.json` | 商城数据 | JSON | v1.0 |
| `./data/user_inventory.json` | 用户背包 | JSON | v1.0 |
| `./data/schedules.json` | 日程数据 | JSON | v1.0 |
| `./data/preset_events.json` | 预设随机事件 | JSON | v1.0 |

---

## 资源目录结构

```
./assets/
|-- animations/              # 统一帧动画目录
|    |-- idle/               # 待机动画
|    |    |-- default/
|    |    |    |-- frame_001.png
|    |    |    |-- frame_002.png
|    |    |    \-- animation.json
|    |    \\-- happy/
|    |-- expressions/        # 表情动画
|    |    |-- smile/
|    |    |-- sad/
|    |    |-- angry/
|    |    |-- shy/
|    |    |-- surprised/
|    |    |-- sleepy/
|    |    \\-- thinking/
|    |-- actions/            # 动作动画
|    |    |-- eat/
|    |    |-- walk/
|    |    |-- sleep/
|    |    |-- dance/
|    |    |-- grabbed/
|    |    |-- jump/
|    |    |-- wave/
|    |    \\-- climb/
|    |-- effects/            # 特效动画
|    |    |-- rain/
|    |    |-- snow/
|    |    |-- sparkle/
|    |    |-- stars/
|    |    |-- heart/
|    |    \\-- tear_drop/
|    |-- lipsync/            # 口型动画
|    |    |-- closed.png
|    |    |-- A.png
|    |    |-- I.png
|    |    |-- U.png
|    |    |-- E.png
|    |    \\-- O.png
|    \\-- transitions/        # 过渡动画
|         |-- idle_to_sleep/
|         \\-- sleep_to_idle/
|-- clothes/                 # 服装图片组
|    |-- default/
|    |-- outfit_01/
|    \\-- outfit_02/
|-- items/                   # 物品图标
|-- audio/
|    |-- chime.wav           # 报时音效
|    |-- alert.wav           # 提醒音效
|    \\-- voice/              # 语音文件
\\-- ui/                      # UI资源
     |-- icons/
     \\-- backgrounds/

./characters/                # 多角色目录
|-- main/                    # 主角色
|    |-- config.json
|    |-- system_prompt.txt
|    \\-- assets/             # 角色专属资源
\\-- partner_a/               # 伙伴角色
     \\-- ...

./plugins/                   # 插件目录
|-- games/                   # 游戏插件
|-- tools/                   # 工具插件
|-- effects/                 # 特效插件
|-- local-llm/               # 本地LLM插件（可选）
\\-- custom/                  # 自定义插件

./backups/                   # 备份目录
\\-- {timestamp}/             # 按时间戳归档
```

---

> **文档生成**: 基于 Interface Flow 规范优化
> **生成时间**: 2025-12-29
> **版本**: v3.0.3
> **变更记录**:
>
> - v3.0.3: **逻辑一致性修复**
>   - 记忆检索策略: 明确`enable_smart_selection`为总开关，`default_strategy`改名为`fallback_strategy`
>   - Token预算默认模式: 从"deep"(64k)改为"standard"(32k)，对新用户更友好
>   - 状态覆盖逻辑: 区分"情绪覆盖"与"数值恢复"，明确数值变化可触发状态重新评估
>   - Tier映射配置: 添加`forced_tier`和`_tier_note`字段，明确各场景Tier配置
>   - 行为计划: 补充说明意图完成后等待下一整点统一生成新计划
>   - 小游戏配置: 补充minigame_settings与prompt_templates优先级说明
> - v3.0.2: **可观测性与健壮性增强**
>   - 新增可观测性系统 (0.9a节): 执行追踪、性能指标、错误监控、调试面板、日报生成
>   - 增强工具调用机制: 指数退避重试、工具结果缓存、状态回滚、高风险操作确认
>   - 完善检查点机制: 多触发条件、备份策略、崩溃恢复、内存缓存层
>   - Agent循环执行追踪: 每个Phase记录span，集成到可观测性系统
>   - 新增配置: observability_settings.json
>   - 更新tool_settings.json: 添加retry_strategy、tool_cache、high_risk_operations
> - v3.0.1: **文档一致性修复**
>   - 统一记忆层命名: Layer 1/2/3 替代所有 Tier 4/5 引用
>   - 情绪状态统一: 5态设计 (Happy/Normal/Tired/Sad/Anxious) + 子状态
>   - 饥饿度触发优化: 自主觅食阈值从90%降至70%，增长速率+2/小时
>   - 场景-Tier映射: 明确为"默认映射+可配置覆盖"机制
>   - Token预算一致性: 0.2节与0.5节预算描述统一
>   - 清理残留代码块
> - v3.0: **架构重构版本**
>   - 记忆系统简化: 5层→3层 (Identity/Working/Long-term)，边界更清晰
>   - 混合架构: 引入 Rust (Maturin/PyO3) 处理性能关键路径
>   - 状态系统重设计: 轻度养成×自适应主动性，新增自主觅食机制
>   - 内在驱动系统: 无聊感+依恋感，让桌宠有"自己的生活"
>   - API配置: 优惠额度充足
>   - 主动频率: 用户可完全自定义 (0-10次/小时)
>   - 免打扰模式: 支持手动开关+自动检测
> - v2.3.3: 逻辑自洽性审查修复 - 轻量模式Token预算校正、情绪覆盖条件明确、API消费控制配置
> - v2.1: 记忆矛盾检测、阈值门控、反馈系统
> - v2.0: 混合存储系统、动画系统
