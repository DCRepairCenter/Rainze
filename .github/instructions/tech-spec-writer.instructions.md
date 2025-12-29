---
applyTo: ".github/techstacks/**/*.md"
---

# Technical Specification Writing Instructions

When user asks to create technical specification or tech stack document:

1. **READ** the target PRD document (user provides path)
2. **READ** [.github/agents/tech-spec-writer.agent.md](.github/agents/tech-spec-writer.agent.md) for the complete protocol
3. **REFERENCE** [.github/roles/technical-specification-writer.md](.github/roles/technical-specification-writer.md) for structure

## Key Principles

- Bridge PRD requirements to implementation details
- Include self-reflection step: "wait，我要反思我的技术栈选择"
- Consider environment constraints (Python, Rust versions)
- Output to `.github/techstacks/TECH-[Name].md`

## Document Structure

1. Front Matter (title, author, dates)
2. Introduction (overview, glossary, goals)
3. Solutions (current, proposed, test plan)
4. Further Considerations (security, performance)
5. Success Evaluation (metrics, monitoring)
6. Work Breakdown (milestones, timeline)

## Quick Command

User triggers: "write tech spec", "create technical specification", "document tech stack"

Input: PRD document path
Output: Technical specification in `.github/techstacks/`
