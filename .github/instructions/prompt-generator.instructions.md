---
applyTo: "**"
---

# Prompt Generation Instructions

When user asks to generate initial prompts or onboarding prompts:

1. **VERIFY** `.prompt/repo-index.md` exists (run repo-scanner first if not)
2. **READ** [.github/agents/prompt-generator.agent.md](.github/agents/prompt-generator.agent.md) for the complete protocol
3. **OUTPUT** to:
   - `.prompt/init.prompt.md`
   - `.prompt/qa-deep.prompt.md`

## Key Principles

- Source code is the ONLY authoritative truth
- Use file references from repo-index.md, NOT content copies
- Always include metadata header with generator info
- Prompts should be 100-200 lines each

## Quick Command

User triggers: "generate prompts", "create init prompt", "onboard repo"
