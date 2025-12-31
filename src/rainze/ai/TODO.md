# TODO - AI 模块

AI 服务层模块，提供 LLM 调用和三层响应生成策略。

## 进行中 (In Progress)

- [ ] 实现 Prompt 构建器 ~3d #feature
  - [ ] PromptBuilder 类
  - [ ] TokenBudgetManager 类
  - [ ] PromptTemplateManager 类
- [ ] 实现场景分类器 ~2d #feature
  - [ ] SceneClassifier 类
  - [ ] ClassifiedScene 数据类
- [ ] 实现降级链管理器 ~2d #feature
  - [ ] FallbackManager 类
  - [ ] FallbackLevel 枚举
  - [ ] FallbackResult 数据类

## 待办 (Backlog)

- [ ] 实现响应缓存 ~1d #feature
  - [ ] ResponseCache 类
  - [ ] 相似度匹配逻辑
- [ ] 实现 Embedding 服务 ~2d #feature
  - [ ] EmbeddingService 类
  - [ ] OpenAIEmbeddingProvider 实现
  - [ ] LocalEmbeddingProvider 实现
- [ ] 添加 OpenAI 客户端 ~1d #enhancement
  - [ ] OpenAIClient 实现
- [ ] 添加本地 LLM 支持 ~3d #enhancement
  - [ ] LocalLLMClient 实现
- [ ] 性能优化 ~2d #perf
  - [ ] 连接池管理
  - [ ] 请求队列
- [ ] 单元测试 ~2d #test
  - [ ] LLM 客户端测试
  - [ ] 生成器测试
  - [ ] Mock 响应测试

## 已完成 ✓

- [x] 创建模块目录结构 2025-12-30
- [x] 实现异常类 (exceptions.py) 2025-12-30
- [x] 实现配置模型 (schemas.py) 2025-12-30
- [x] 实现 LLM 客户端抽象 (llm/client.py) 2025-12-30
- [x] 实现 Anthropic 客户端 (llm/providers/anthropic.py) 2025-12-30
- [x] 实现响应生成策略 (generation/strategy.py) 2025-12-30
- [x] 实现 Tier1 模板生成器 (generation/tier1_template.py) 2025-12-30
- [x] 实现 Tier2 规则生成器 (generation/tier2_rule.py) 2025-12-30
- [x] 实现 Tier3 LLM 生成器 (generation/tier3_llm.py) 2025-12-30
- [x] 创建模块导出 (__init__.py) 2025-12-30
