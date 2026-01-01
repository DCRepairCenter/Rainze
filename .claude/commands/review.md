# Code Review

Review the recent code changes and provide feedback on:

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

## Scope

$ARGUMENTS
