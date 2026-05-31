---
name: sciv-orientation
description: "Orient to the SCiv codebase before implementation. Use for ambiguous tasks, cross-cutting changes, unfamiliar subsystems, or when you need to know what files and docs to read first."
argument-hint: "Describe the task, subsystem, or question you need to orient on."
user-invocable: true
---

# SCiv Orientation

Use this skill before implementation when the correct docs or code areas are not obvious.

## When to Use

- Ambiguous tasks that could touch multiple subsystems
- Cross-cutting refactors
- Startup, turn, save/load, or UI-bridge work
- "Where does this live?" or "What should I read first?" questions

## Procedure

1. Read [`meta/INDEX.md`](../../../meta/INDEX.md).
2. Use the [`sciv-project-index`](../sciv-project-index/SKILL.md) skill or `python3 scripts/query_project_index.py search "<query>"` when you need targeted matches from the generated manifest.
3. Read [`meta/structure.md`](../../../meta/structure.md) and [`meta/generated/project-index.json`](../../../meta/generated/project-index.json) directly when you need raw inventory detail or the helper output is insufficient.
4. Use the [routing matrix](./references/routing-matrix.md) to map the task to the correct subsystem docs.
5. Read the matching `meta/technical/*.md` pages before proposing edits.
6. Identify the most likely edit targets.
7. Identify which docs must be updated if the code changes.

## Constraints

- Do not implement fixes as part of this skill.
- Do not duplicate architecture notes that already live in `meta/`.
- If the routing matrix is wrong or incomplete, report that and suggest updating it.

## Output Format

Return a concise orientation report with:

- consulted docs
- likely code areas/files
- likely follow-up docs to update
- open questions or ambiguity to resolve before editing
