---
name: fix-github-issue
description: Workflow for analyzing and fixing GitHub issues. Use when given an issue number to investigate and resolve.
---

# Fix GitHub Issue Skill

Analyze and fix GitHub issues systematically.

## Workflow

1. **Get Issue Details**
   ```bash
   gh issue view <issue_number>
   ```

2. **Understand the Problem**
   - Read issue description and comments
   - Identify affected components
   - Determine root cause

3. **Search Codebase**
   - Find relevant files
   - Understand current implementation
   - Check related tests

4. **Implement Fix**
   - Follow coding standards (see code-writer skill)
   - Import contracts from `rainze.core.contracts`
   - Add bilingual comments

5. **Validate**
   ```bash
   make lint      # Check linting
   make typecheck # Check types
   make test      # Run tests
   ```

6. **Commit & PR**
   - Use conventional commit format
   - Reference issue number: `Fixes #<number>`
   - Create PR with description

## Requirements

- Follow CLAUDE.md coding standards
- Run `make check` before committing
- Include test for the fix when applicable
