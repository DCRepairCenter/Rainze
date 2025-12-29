---
applyTo: "**"
---

# Prompt Optimization Instructions

When user asks to optimize or improve existing prompts:

1. **VERIFY** `.prompt/init.prompt.md` and `.prompt/qa-deep.prompt.md` exist
2. **READ** [.github/agents/prompt-optimizer.agent.md](.github/agents/prompt-optimizer.agent.md) for the complete protocol
3. **CHECK** for same-model optimization (compare your model with `generated_by` field)

## Key Principles

- Only revise the WEAKEST section, not entire prompts
- Use adversarial testing to find failure modes
- Always output optimizer signature
- Warn if same-model optimization detected

## Quick Command

User triggers: "optimize prompts", "improve prompts", "adversarial test"
