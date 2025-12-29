---
applyTo: "**"
---

# Repository Scanning Instructions

When user asks to scan repository, analyze codebase, or generate repo summary:

1. **READ** [.github/agents/repo-scanner.agent.md](.github/agents/repo-scanner.agent.md) for the complete scanning protocol
2. **OUTPUT** results to `.prompt/repo-index.md`

## Key Principles

- Create file INDEX with references, NOT content copies
- Use format: `[filename](path#L1-L50)` for line references
- Keep output under 200 lines
- Respect `.gitignore` but always include `.prompt/`, `.github/`

## Quick Command

User triggers: "scan repo", "analyze repository", "generate repo index"
