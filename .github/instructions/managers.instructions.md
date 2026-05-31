---
name: "SCiv Managers Routing"
description: "Use when editing SCiv managers, startup orchestration, turn processing, game flow, entity manager logic, or state manager behavior. Routes manager and runtime-core work to the required technical docs first."
applyTo: "{sciv/managers/**,sciv/game.py}"
---

# SCiv Managers Routing

- Read [`meta/technical/architecture.md`](../../meta/technical/architecture.md) first for ownership boundaries.
- If the task touches startup order, loading-screen continuation, or manager creation, read [`meta/technical/startup.md`](../../meta/technical/startup.md) before editing.
- If the task touches manager-side UI handoff, loading-screen activation, screen selection, or click forwarding into `GameUIScreen`, also read [`meta/technical/ui-runtime.md`](../../meta/technical/ui-runtime.md) and [`meta/technical/signals.md`](../../meta/technical/signals.md).
- If the task touches world-generation sequencing, generator selection, or the handoff from `Game`/`World` into generator code, also read [`meta/technical/world-generation.md`](../../meta/technical/world-generation.md).
- If the task touches manager-side render orchestration, atlas/bootstrap, `TileRendererSystem` registration, terrain model-grid handoff, or render-node picking tags, also read [`meta/technical/rendering-system.md`](../../meta/technical/rendering-system.md).
- If the task touches world-tile ownership, lookup, or turn work rooted in tile state, also read [`meta/technical/tile-system.md`](../../meta/technical/tile-system.md).
- If the task touches turn stages, end-turn flow, or turn-related signals, read [`meta/technical/turns.md`](../../meta/technical/turns.md) and [`meta/technical/signals.md`](../../meta/technical/signals.md) first.
- If the task touches `EntityManager`, `State`, or manager-owned persistence boundaries, also read [`meta/technical/entities.md`](../../meta/technical/entities.md).
- When manager responsibilities move, update the matching `meta/technical/*.md` pages in the same change and review [`meta/technical/update-triggers.md`](../../meta/technical/update-triggers.md).
