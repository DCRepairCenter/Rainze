# Create Conventional Commit

Analyze the current staged changes and create a well-structured commit message following Conventional Commits.

## Steps

1. Run `git diff --cached --stat` to see what files changed
2. Run `git diff --cached` to understand the changes in detail
3. Determine the appropriate type: feat|fix|docs|style|refactor|perf|test|build|ci|chore
4. Determine scope based on changed files (gui, core, memory, ai, agent, animation, rust)
5. Write description in imperative mood, <50 chars
6. Add body if needed (explain WHAT and WHY)
7. Add footer with `Reviewed-by: Claude [MODEL]`
8. Execute the commit

## Example Output

```
feat(gui): add transparent window support

Implemented transparency support for the main pet window
using Qt's WA_TranslucentBackground attribute.

Reviewed-by: Claude Sonnet 4.5
```
