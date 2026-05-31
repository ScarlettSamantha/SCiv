# SCiv Instruction Layer

This folder contains thin dispatcher instructions for future Copilot sessions.

## Purpose

- Route the agent to the right Git-tracked docs before implementation starts.
- Keep file- or subsystem-specific guidance out of the always-on entrypoint.
- Avoid duplicating durable knowledge that already lives in `meta/`.

## Reading model

1. `.github/copilot-instructions.md` is the single always-on entrypoint.
2. Matching `*.instructions.md` files attach on relevant edits and route to the right docs.
3. `meta/` remains the source of truth for architecture and subsystem behavior.
4. The `sciv-orientation` skill handles ambiguous or cross-cutting tasks.
5. Shared Python, typing, and changelog workflow policy belongs in `meta/technical/`, with instruction files acting only as dispatchers to those docs.

## Rules for maintaining this layer

- Keep these files short, keyword-rich, and link-based.
- Use one concern per instruction file.
- If the routing for a guarded subsystem changes, update the corresponding instruction file and `meta/technical/update-triggers.md` together.
- Keep repo-wide coding policy in `meta/technical/python-conventions.md` and repo-wide changelog policy in `meta/technical/changelog-workflow.md`; do not duplicate those rules inline here.
- Do not move durable architecture notes into this folder; link to `meta/` instead.