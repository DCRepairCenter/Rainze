---
applyTo: "src/**/*.py,rainze_core/**/*.rs"
---

# Code Writer Instructions

When user asks to write code, implement features, or create modules:

1. **READ** [.github/agents/code-writer.agent.md](.github/agents/code-writer.agent.md) for the complete protocol
2. **REFERENCE** [.github/prds/modules/README.md](.github/prds/modules/README.md) for module overview
3. **CHECK** [.github/prds/modules/MOD-{module}.md] for specific module design

## Quick Reference

### Python Standards (PEP 8)

| Element | Convention | Example |
|---------|------------|---------|
| Module | `snake_case` | `event_bus.py` |
| Class | `PascalCase` | `StateManager` |
| Function | `snake_case` | `get_state()` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| Private | `_underscore` | `_internal` |

### Rust Standards

| Element | Convention | Example |
|---------|------------|---------|
| Module | `snake_case` | `memory_search` |
| Struct | `UpperCamelCase` | `MemorySearcher` |
| Function | `snake_case` | `search_memories()` |
| Constant | `SCREAMING_SNAKE_CASE` | `MAX_BATCH_SIZE` |

### Critical Rules

1. **Cross-Module Contracts** (PRD §0.15):
   - Import shared types from `rainze.core.contracts`
   - NEVER duplicate type definitions

2. **UCM Entry Rule**:
   - All user interactions must go through UCM
   - Never bypass to call AI services directly

3. **Type Annotations**:
   - Python: ALL functions must have type hints
   - Rust: Use explicit types, avoid excessive inference

4. **Error Handling**:
   - Python: Specific exceptions, chain with `from e`
   - Rust: Use `anyhow` for apps, `thiserror` for libs

5. **Documentation**:
   - Python: Google-style docstrings with Args/Returns/Raises
   - Rust: `///` doc comments with Examples

## Module Implementation Checklist

```markdown
- [ ] Read relevant MOD-{name}.md design document
- [ ] Create directory structure per specification
- [ ] Implement base classes/types
- [ ] Import contracts from core.contracts (NOT duplicate)
- [ ] Add full type annotations
- [ ] Write docstrings for all public APIs
- [ ] Handle errors properly
- [ ] Run linting: `ruff check` / `cargo clippy`
- [ ] Run type check: `mypy` / `cargo check`
```

## Quick Command

User triggers: "write code", "implement module", "create class", "add feature"
