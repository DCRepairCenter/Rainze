# Fix GitHub Issue

Please analyze and fix the GitHub issue: $ARGUMENTS.

## Workflow

1. Use `gh issue view $ARGUMENTS` to get issue details
2. Understand the problem described
3. Search the codebase for relevant files
4. Implement the necessary changes
5. Write and run tests to verify the fix
6. Ensure code passes linting (`make lint`) and type checking (`make typecheck`)
7. Create a descriptive commit message following Conventional Commits
8. Push and create a PR

## Requirements

- Follow the coding standards in CLAUDE.md
- Import shared types from `rainze.core.contracts`
- Add bilingual comments (中文/English)
- Run `make check` before committing
