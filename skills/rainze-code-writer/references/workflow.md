# Workflow & Checklists

Follow this path when implementing Rainze code. Load only the docs you need.

## Step-by-step
1) **Frame the task**: Identify the PRD section (use docs-index). Confirm feature tier and success criteria (latency, memory limits, fallbacks).
2) **Pick modules**: Map the task to modules in `.github/prds/modules/`. Open the relevant sub-PRD for method signatures/class layouts and expected configs/events.
3) **Plan**: Decide Python vs Rust responsibilities (Python orchestration/UI/AI flow; Rust for retrieval, vectorization, system monitoring, text processing). Note required configs and contracts (scene/emotion/interaction, tracer, UCM rules).
4) **Implement**:
   - Use `core.contracts` types; do not redefine enums/models already specified.
   - Keep `UnifiedContextManager` as the interaction entry; avoid bypassing with direct module calls.
   - Update config schemas and defaults when adding behaviors; sync docs/comments.
   - Respect AI fallback chain and response tiers (see PRD §0.6); preserve observability spans.
   - For Rust (PyO3), keep Rust structs minimal and expose Python-friendly methods; enforce thread-safety and avoid GUI work off the main thread.
5) **Test**: Run module-specific tests per sub-PRD (unit/integration/perf). For new Rust bindings, add `cargo test`/`maturin develop` smoke. For Python, add `pytest` cases around new behaviors.
6) **Verify**: Check configs load, contracts align, logs/traces emitted, and PRD feature acceptance is met. Update changelog or notes if required.

## Checklists
- Architecture: UCM entry respected; ReAct/tool use follows `MOD-Tools`; plugin boundaries obey `MOD-Plugins`.
- Memory: Retrieval path and reflection per `MOD-Memory`; storage schemas updated if data changes.
- State/Emotion: Use `SceneType/ResponseTier/EmotionTag` enums; keep state transitions within `StateManager/EmotionStateMachine`.
- GUI/Animation: Render via GUI module; drive emotion/expression through animation layers; avoid blocking UI thread.
- Performance: Heavy compute in Rust; use FAISS + SQLite; keep resident memory < target; cache where specified.

## Coding standards
- Python: follow `.github/references/python/pep8.md` (types, naming, imports).
- Rust: follow `.github/references/rust/style.md` (rustfmt rules, struct/enum layout, imports).
- Documentation: inline comments only when non-obvious; keep ASCII.
