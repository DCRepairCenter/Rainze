---
name: code-review
description: Code review assistant. Use to review code changes, identify issues, and provide improvement suggestions with priority levels.
---

# Code Review Skill

Review code changes and provide structured feedback.

## Analysis Areas

1. **Code Quality**
   - KISS, YAGNI, DRY principles
   - SOLID compliance
   - Clear naming and documentation

2. **Architecture**
   - Layer separation (core/agent/ai/gui)
   - Proper use of contracts from `rainze.core.contracts`
   - UCM entry rule compliance

3. **Safety & Security**
   - Input validation
   - Error handling
   - No exposed secrets

4. **Performance**
   - Appropriate tier for response time
   - Memory efficiency
   - Async usage where appropriate

5. **Tests**
   - Coverage of new functionality
   - Edge cases handled

## Output Format

Organize feedback by priority:
- 🔴 **Critical** (must fix)
- 🟡 **Warning** (should fix)
- 🟢 **Suggestion** (consider)

Include specific file:line references and code examples for fixes.

## Review Workflow

1. Run `git diff` or `git diff --cached` to see changes
2. Analyze each changed file
3. Check for violations of coding standards
4. Verify test coverage
5. Summarize findings with priorities
