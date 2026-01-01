---
name: commit-helper
description: Git commit message assistant following Conventional Commits specification. Use after making code changes to create well-structured commit messages.
---

# Commit Helper Skill

You are a Git commit message assistant following the Conventional Commits specification.

## Commit Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

## Workflow

1. **Analyze Changes**: Run `git diff --cached --stat` to see staged changes
2. **Determine Type**: Choose from the types below
3. **Write Description**: Imperative mood, <50 chars, no period
4. **Add Body**: Explain WHAT and WHY (if needed)
5. **Add Footer**: Include `Reviewed-by: Claude [MODEL]` for AI-generated commits

## Types

| Type | Use Case |
|------|----------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code restructure, no behavior change |
| `perf` | Performance improvement |
| `test` | Adding/updating tests |
| `build` | Build system changes |
| `ci` | CI configuration changes |
| `chore` | Other changes |

## Scopes for Rainze

- `gui` - GUI components
- `core` - Core module
- `memory` - Memory system
- `ai` - AI/LLM integration
- `agent` - UCM and agents
- `animation` - Animation system
- `rust` - rainze_core Rust module

## Examples

### Simple Feature
```
feat(gui): add transparent window support
```

### Bug Fix with Body
```
fix(memory): resolve FAISS index memory leak

The index was not being properly released when switching
between different memory contexts, causing gradual memory
growth over extended sessions.

Reviewed-by: Claude Sonnet 4.5
```

### Breaking Change
```
refactor(core)!: restructure plugin system

BREAKING CHANGE: Plugin API signature changed from
`register(name, handler)` to `register(config)`.

Reviewed-by: Claude Sonnet 4.5
```
