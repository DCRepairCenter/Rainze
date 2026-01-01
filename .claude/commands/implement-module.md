# Implement Module

Implement the module specified: $ARGUMENTS

## Pre-Implementation Checklist

1. **Read Documentation**
   - [ ] Check `.github/prds/modules/MOD-{name}.md` for design spec
   - [ ] Review `.github/prds/PRD-Rainze.md` for requirements
   - [ ] Check `.github/techstacks/TECH-Rainze.md` for tech decisions

2. **Understand Dependencies**
   - [ ] Identify required contracts from `rainze.core.contracts`
   - [ ] Check upstream/downstream module interfaces
   - [ ] Verify layer placement (core/agent/ai/gui)

## Implementation Steps

1. Create directory structure per specification
2. Implement base classes/types
3. **IMPORTANT**: Import contracts from `rainze.core.contracts`, never duplicate
4. Add full type annotations (Python) or explicit types (Rust)
5. Write docstrings for all public APIs
6. Handle errors properly (specific exceptions, chain with `from e`)

## Validation

1. Run `make lint` - ruff check
2. Run `make typecheck` - mypy
3. Run `make test` - pytest
4. For Rust: `make rust-check` - cargo clippy

## Code Standards

- Python: Google-style docstrings, line-length=88
- Rust: `///` doc comments, use anyhow/thiserror
- Both: Bilingual comments (中文 / English)
