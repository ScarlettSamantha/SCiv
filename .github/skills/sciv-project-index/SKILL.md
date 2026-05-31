---
name: sciv-project-index
description: "Use when you need structured lookup against SCiv's generated project index to find likely files, docs, entry points, areas, or routing rules before reading source. Helpful for project index questions, file discovery, subsystem lookup, and 'where does this live?' work."
argument-hint: "Describe the file, subsystem, symbol, or routing question you want to resolve from SCiv's generated project index."
user-invocable: true
---

# SCiv Project Index Navigator

Use this skill when the full `meta/generated/project-index.json` manifest is too large for a quick read and you want focused results first.

## When to Use

- "Where does this live?" questions
- File or subsystem discovery before implementation
- Looking for likely docs to read before editing
- Finding entry points, runtime areas, or routing rules
- Sanity-checking whether the generated index already covers a surface

## Procedure

1. Start with [`meta/INDEX.md`](../../../meta/INDEX.md) if you need the curated doc map.
2. Run `python3 scripts/query_project_index.py search "<query>"` for a broad lookup across docs, routes, entry points, areas, and modules.
3. Use `python3 scripts/query_project_index.py route "<topic-or-route-id>"` when you specifically want routing-rule matches.
4. Use `python3 scripts/query_project_index.py area "<area-name-or-topic>"` when you specifically want indexed runtime-area matches.
5. If one result needs more detail, run `python3 scripts/query_project_index.py show "<path-or-id>"` and narrow with `--kind` if needed.
6. Read the returned source files or docs before editing. The helper narrows candidates; it does not replace source review.
7. If the task is still ambiguous or cross-cutting after the lookup, continue with [`sciv-orientation`](../sciv-orientation/SKILL.md).

## Handy queries

- `ui runtime`
- `system.main.ready`
- `save load`
- `entity serialization`
- `world generation`
- `manager ui`
- `combat log`
- `route ui-bridge-and-screens`
- `area sciv/menus`

## Output Format

Return a concise lookup report with:

- top matches
- docs to read first
- likely code files
- any obvious gaps or stale index coverage
