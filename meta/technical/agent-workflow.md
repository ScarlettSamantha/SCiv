# SCiv Agent Workflow

> Back to [Documentation Index](../INDEX.md)
>
> Related: [Architecture](architecture.md) | [World Generation](world-generation.md) | [Update Triggers](update-triggers.md) | [SCiv Copilot Instructions](../../.github/copilot-instructions.md)

This document defines the preferred workflow for repo-specialized coding agents working on SCiv.

The goals are simple:

- read the right docs before editing
- stay tightly scoped to the requested task
- prefer small, surgical changes over broad refactors
- write durable learnings back into Git-tracked docs
- avoid oversized responses or sweeping patches unless the user explicitly asks for them

## Start-of-task workflow

Before making code changes, a SCiv-focused agent should:

1. Read [`meta/INDEX.md`](../INDEX.md).
2. For targeted file or doc discovery, use the `sciv-project-index` skill or `python3 scripts/index.py` first; then read [`meta/structure.md`](../structure.md), [`meta/generated/project-index.json`](../generated/project-index.json), and [`project-index-helper.md`](project-index-helper.md) directly when you need raw inventory detail or command guidance.
3. Read [`../../.github/copilot-instructions.md`](../../.github/copilot-instructions.md) to identify the guarded subsystem.
4. Read [`update-triggers.md`](update-triggers.md) and the matching focused technical docs for the touched area.
	- World-container, tile-ownership, or world-turn work should usually include [`world-system.md`](world-system.md), [`tile-system.md`](tile-system.md), [`world-generation.md`](world-generation.md), and [`turns.md`](turns.md).
	- Player-registry, player-role, or empire-state work should usually include [`player-system.md`](player-system.md), [`turns.md`](turns.md), [`world-generation.md`](world-generation.md), and [`entities.md`](entities.md).
	- Tile-domain work should usually include [`tile-system.md`](tile-system.md).
	- Terrain or world-rendering work should usually include [`rendering-system.md`](rendering-system.md).
	- Asset/archive/atlas work should usually include [`asset-system.md`](asset-system.md), [`startup.md`](startup.md), and [`architecture.md`](architecture.md).
5. If the task edits Python files or typing/tooling workflow, read [`python-conventions.md`](python-conventions.md).
6. If the task changes contributor-visible behavior, workflow, or tooling, read [`changelog-workflow.md`](changelog-workflow.md) before finishing.
7. Investigate only the files needed to solve the task.
8. Create a short todo list before implementation.

When the task involves Kivy typing errors, `*.pyi` files, or missing third-party symbols, also confirm which stub root is active:

- repo-local / CI Pyright expects `./stubs`
- the shared local workspace stub checkout lives under sibling `../Stubs/kivy`

Agents should document and preserve that distinction rather than assuming both paths are populated.

If the task is ambiguous or obviously cross-cutting, the agent should orient first and only then implement.

## Execution rules

### Stay on task

- Solve the user’s requested problem first.
- Do not broaden scope just because nearby cleanup is tempting.
- Note adjacent issues briefly when relevant, but do not fix them unless they block the requested work or the user asks.
- Prefer small, focused changes that are easy to review over big sweeping edits unless broader scope is explicitly required.

### Prefer surgical changes

- Make the smallest viable change that solves the task.
- Prefer small, focused diffs over large sweeping rewrites.
- Prefer narrow patches over whole-file rewrites.
- Preserve public APIs, file layout, and style unless the task requires otherwise.
- Avoid multi-subsystem refactors unless the user explicitly asks for them.
- Prefer extracting smaller reusable chunks, modules, or components when that meaningfully improves cohesion and reuse.
- Keep code in separate focused files when practical and useful so responsibilities stay clearer and targeted edits create less token churn.
- Follow [`python-conventions.md`](python-conventions.md): SCiv targets Python 3.14, new modules should not add `from __future__ import annotations`, and Pyright strict mode is the canonical typing contract.
- Default to strong typing for parameters, returns, long-lived state, and non-trivial local variables instead of relying on implicit inference.
- Keep comments sparse; add them only when code still needs a brief note for genuinely non-obvious logic, such as tricky math, and keep them short so the code stays clean.
- Use whitespace intentionally so code is logically grouped, easy to scan, and visually pleasant rather than packed as densely as possible.

### Keep change batches small

- Prefer implementation batches under roughly `500` changed lines.
- Prefer touching as few files as practical for each logical step.
- If the best solution will exceed that size, split the work into phases and complete one phase at a time.

### Validate continuously

- Re-check the relevant files after each meaningful edit.
- Run focused validation after each logical change when practical.
- Prefer targeted tests/checks over broad expensive runs unless the task is broad.
- After changing stubs or typing-heavy UI code, explicitly check diagnostics and prefer `make pyright-diff`; use `make pyright-full` when shared stubs changed in a way that could fan out broadly.

## Completion workflow

When the task is done, the agent should:

1. Revisit [`update-triggers.md`](update-triggers.md) and confirm whether behavior or ownership changed.
2. Update the matching `meta/technical/*.md` docs when the change affects behavior, workflow, or subsystem contracts.
3. Write down verified new learnings in the most relevant Git-tracked doc instead of leaving them implicit in chat.
4. Do this automatically for every completed task when the session surfaced a stable codebase or workflow fact, even if the code change itself was small.
5. If the learning changes task routing or repo-local agent behavior, update [`../../.github/copilot-instructions.md`](../../.github/copilot-instructions.md), the relevant `.github/instructions/*.instructions.md`, or the orientation routing matrix in the same change.
6. If no existing doc is the right home for the learning, create a narrowly scoped doc or note it in backlog/project docs for follow-up.
7. If the change is meaningful to users or contributors, update [`../../CHANGELOG.md`](../../CHANGELOG.md) through the helper documented in [`changelog-workflow.md`](changelog-workflow.md), preferring gitmoji-prefixed entries and ticket references when the task has a tracked issue.
8. Refresh generated docs if `meta/**`, `.github/**`, `scripts/index.py`, or the legacy index wrappers changed.
9. Leave a concise summary of what changed, how it was verified, and what follow-up remains.

## Output and response limits

- Keep normal user-facing responses comfortably under roughly `500` lines.
- Do not dump giant code blocks or long patch explanations when a concise summary will do.
- If the explanation would be too long, summarize the change and point to the edited files.

## Definition of done

A SCiv task is not truly done until:

- the requested change is implemented or a blocker is clearly identified
- relevant validation has been run
- the todo list is updated
- the related docs are updated when needed
- verified stable learnings from the task are written back automatically when the session surfaced them
- `CHANGELOG.md` is updated when the change is contributor-visible or user-visible
- generated documentation is refreshed when the indexed surfaces changed

## Notes for future improvements

This workflow is guidance, not a hard enforcement layer. If the repository later wants deterministic limits for patch size, tool choice, or mandatory doc updates, add hooks or validation scripts in a separate change.