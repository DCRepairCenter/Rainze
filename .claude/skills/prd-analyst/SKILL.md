---
name: prd-analyst
description: PRD document analyst. Use when analyzing requirements, creating Interface Flow documentation, or understanding module interactions.
---

# PRD Analyst Skill

Analyze Product Requirements Documents and extract structured information.

## Output Format: Interface Flow

For each module interaction, document:

```markdown
## IF-{XX}: {简短标题}

**触发场景**: {什么情况下触发}

**数据流**:
```
[模块A] --{数据类型}--> [模块B] --{处理结果}--> [模块C]
```

**契约引用**: `{TypeName}` from `core.contracts`

**错误处理**: {异常情况及处理方式}
```

## Workflow

1. Read PRD from `.github/prds/PRD-Rainze.md`
2. Read module designs from `.github/prds/modules/MOD-*.md`
3. Identify module boundaries and interactions
4. Document data flow with contract types
5. Note error handling requirements

## Key PRD Sections to Analyze

- §0.15 - Cross-module contracts
- §1.x - Core features
- §2.x - AI integration
- §3.x - Memory system
- §4.x - GUI components

## Contract Types Reference

Import from `rainze.core.contracts`:
- `EmotionTag` - Emotion classification
- `SceneType` - Scene categorization
- `InteractionEvent` - User interaction events
- `ResponseTier` - Response tier (1/2/3)
