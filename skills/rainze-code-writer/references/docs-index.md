# Docs Index for Rainze Code Writer

Use this map to locate the right source before coding. Always open the module sub-PRD to see the latest method signatures and class/struct layouts.

## Primary requirement docs
- `.github/prds/PRD-Rainze.md`: Full product PRD. Key sections: §0.* AI驱动核心架构 (tech choices, memory hierarchy, fallback chain, UCM, contracts), §1.* 基础功能 (26 items), §2.* 进阶功能, §3 插件系统架构, 附录数据结构/配置清单。
- `.github/techstacks/TECH-Rainze.md`: Tech stack decisions (Python 3.12+, Rust performance via PyO3, PySide6 GUI, FAISS + SQLite storage, LLM cloud-first strategy, packaging via PyInstaller/Nuitka, env setup).

## Module sub-PRDs (.github/prds/modules/)
- `MOD-Core.md`: Core infra (Application, ConfigManager, EventBus, DIContainer, Logger), contracts (EmotionTag, SceneType/ResponseTier, InteractionRequest/Response, IRustBridge, Tracer, UCM protocol), config loading and schemas.
- `MOD-Agent.md`: Agent brain (UnifiedContextManager entry, AgentLoop, BehaviorPlanner, SceneClassifier, IntentRecognizer, ConversationManager, proactive behaviors, workflow/react execution, configs for context/loop/plan/conversation).
- `MOD-AI.md`: AI service layer (PromptBuilder, TokenBudgetManager, LLMClient, ResponseGenerator, FallbackManager, scene classifier, embedding service), schemas/exceptions, response examples.
- `MOD-Memory.md`: Memory system (MemoryManager, MemoryCoordinator, HybridRetriever, ImportanceEvaluator, ConflictDetector, VectorizeQueue), data models (MemoryItem, RetrievalResult, TimeWindow), configs/tests.
- `MOD-State.md`: State management (StateManager, EmotionStateMachine, IntensityParser, property manager, StateStore, CheckpointManager), state events/configs (emotion/state settings), usage/tests.
- `MOD-Tools.md`: Tool use (BaseTool, ToolRegistry, ToolExecutor, ReActEngine, HighRiskConfirmation), built-in tools (SystemReminder, WeatherQuery, AppLauncher, NoteManager), tool configs/events.
- `MOD-Plugins.md`: Plugin system (PluginManager/API/Base, PermissionManager with defaults/limits, PluginManifest), plugin vs tools/features boundaries, sample plugin, configs/errors/tests.
- `MOD-Features-Basic.md`: Base features (BaseFeature, FeatureRegistry) plus services for chat history, hourly chime, focus timer, inventory/shop/economy, scheduler/events, idle chat, system/gaming/network monitors, clipboard, launcher/bookmarks/minigames, notes/weather/easter eggs, etc.; data models (Schedule, Item); feature configs.
- `MOD-GUI.md`: GUI (TransparentWidget, MainWindow, SystemTray, ChatBubble, MenuSystem, InputPanel, ThemeManager), dialog set (settings/schedule/backpack/history/shop), GUI settings, dependency graph.
- `MOD-Animation.md`: Animation stack (AnimationController, AnimationLayer base, ExpressionLayer, LipSyncManager, EffectLayer, ResourceLoader), animation settings, events, usage for AI responses.
- `MOD-Storage.md`: Persistence (Database, Repository, FAISSIndex, JSONStore, BackupManager), DB schemas (memory/FTS, user prefs, behavior, chat, schedule), storage config.
- `MOD-RustCore.md`: Rust performance modules (lib.rs entry; memory_search FAISSWrapper/Reranker/SearchCache; vectorize queue/batch processor; system_monitor monitors; text_process tokenizer/entity detector; errors), Cargo deps, runtime config, PyO3 exports/type stubs, examples/tests/perf, platform guidance.

## Coding standards
- Python: `.github/references/python/pep8.md`
- Rust: `.github/references/rust/style.md`
