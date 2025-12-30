---
name: rainze-code-writer
description: Build and update Rainze code using the PRD, tech stack, and module sub-PRDs. Use this when writing Python/Rust for Rainze, aligning with the architecture, method signatures, class/layout definitions, and coding standards under .github/references.
---

# Rainze Code Writer

Specialized agent for implementing Rainze features across Python and Rust. Keep replies focused on execution; avoid generic tips.

## Use when
- Implementing or modifying Rainze features, modules, or bindings.
- Translating PRD requirements into code using module method signatures/class layouts.
- Enforcing Rainze tech stack choices and coding standards.

## Quick start
- Read `references/docs-index.md` to pick the right PRD/tech/module docs.
- Open the relevant module sub-PRD for method signatures and class/struct layouts before coding.
- Follow the workflow checklist in `references/workflow.md`.

## Core rules
- Route interactions through `UnifiedContextManager`; do not bypass with direct module calls unless the contract allows.
- Reuse shared types from `core.contracts` (scene, emotion, interaction, rust bridge, tracer) instead of redefining.
- Respect Python/Rust boundaries: heavy compute and system monitoring stay in Rust (PyO3 bindings), orchestration/UI/AI wiring stay in Python.
- Keep configs in sync with documented schemas; update defaults and examples when changing behavior.
- Apply coding standards: Python PEP 8 (`.github/references/python/pep8.md`), Rust style (`.github/references/rust/style.md`).

## References
- Module and doc map: `skills/rainze-code-writer/references/docs-index.md`
- Workflow and checklists: `skills/rainze-code-writer/references/workflow.md`
- Coding standards (source): `.github/references/python/pep8.md`, `.github/references/rust/style.md`
