---
applyTo: "**"
---

# Commit Helper Instructions

When user asks to create a commit or needs help with commit messages:

1. **READ** [.github/agents/commit-helper.agent.md](.github/agents/commit-helper.agent.md) for the complete workflow
2. **REFERENCE** [.github/references/git/conventional-commit.md](.github/references/git/conventional-commit.md) for specification

## Commit Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

## Common Types

| Type | Use Case |
|------|----------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code restructure, no behavior change |
| `perf` | Performance improvement |
| `test` | Adding/updating tests |
| `chore` | Build process, tooling |

## Examples

```
feat(gui): add transparent window support
fix(memory): resolve FAISS index memory leak
docs: update PRD with new interaction flow
refactor(core)!: restructure plugin system

BREAKING CHANGE: Plugin API signature changed
```

## AI-Generated Commits

When AI generates commits, ALWAYS include reviewer info:
```
Reviewed-by: [MODEL_NAME]
```

## Quick Command

User triggers: "create commit", "commit message", "conventional commit"
