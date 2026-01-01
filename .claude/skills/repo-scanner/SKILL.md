---
name: repo-scanner
description: Analyze repository structure and generate comprehensive index. Use to understand codebase organization or create repo-index.md.
---

# Repository Scanner Skill

Analyze the repository structure and generate a comprehensive index.

## Output

Generate `.prompt/repo-index.md` with:

1. **Project Metadata**
   - Name, type, languages, package manager

2. **Directory Structure** (2 levels)
   - Key directories with one-sentence descriptions

3. **Key Files Index**
   - File paths with line ranges and purposes

4. **Entry Points**
   - Main entry, CLI entry, config locations

5. **Commands**
   - Install, build, test, lint commands

## Constraints

- Output under 200 lines
- Use file links `[name](path#L1-L50)`
- Reference over copy - don't include file contents
- Respect `.gitignore` but include `.claude/`, `.github/`

## Rainze Project Structure

```
src/rainze/           # Python main code
├── core/             # Core module, contracts
├── agent/            # UCM, scene classifier
├── ai/               # LLM integration
├── gui/              # PyQt6 GUI
├── memory/           # Memory & retrieval
├── animation/        # Animation system
└── state/            # State management

rainze_core/          # Rust performance module
config/               # JSON configuration
.github/prds/         # PRD documents
```

## Workflow

1. Use `find` or `ls -R` to discover structure
2. Read key files (pyproject.toml, Cargo.toml, etc.)
3. Identify entry points and dependencies
4. Generate structured index with links
