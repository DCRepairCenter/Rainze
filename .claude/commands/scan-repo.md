# Scan Repository

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
