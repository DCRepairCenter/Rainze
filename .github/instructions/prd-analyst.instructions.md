---
applyTo: ".github/prds/**/*.md"
---

# PRD Analysis Instructions

When working with PRD documents or user asks to analyze/create requirements:

1. **READ** [.github/agents/prd-analyst.agent.md](.github/agents/prd-analyst.agent.md) for the complete protocol
2. **REFERENCE** [.github/roles/product-requirements-analyst.md](.github/roles/product-requirements-analyst.md) for formatting rules

## Key Principles

- NEVER generate code or technical implementation
- Use [Interface Flow] structured format only
- Maximum 3 levels of nesting
- Ask clarifying questions BEFORE generating output

## Interface Flow Quick Reference

```
[Stage Name]
|-- Element A
|-- Element B + Element C
\-- Last element
     |
     v (trigger)
     |-- Result A
     \-- Result B
```

## Quick Command

User triggers: "analyze PRD", "create interface flow", "convert to structured format"

Input: User provides natural language feature description
Output: Structured [Interface Flow] document
