---
name: "SCiv Gameplay Routing"
description: "Use when editing gameplay systems such as units, cities, tiles, rules, effects, civics, techs, diplomacy, or other code under sciv/gameplay/. Routes gameplay work to the right mechanics docs before editing."
applyTo: "sciv/gameplay/**"
---

# SCiv Gameplay Routing

- Start with [`meta/technical/architecture.md`](../../meta/technical/architecture.md) for subsystem boundaries, then read [`meta/technical/workings.md`](../../meta/technical/workings.md) for mechanics context.
- If the task touches tile ownership, occupancy, terrain/resource/improvement slots, or tile-side render hooks, also read [`meta/technical/tile-system.md`](../../meta/technical/tile-system.md).
- If the task touches persistent modifiers, timed bonuses, or effect placement, also read [`meta/technical/effects.md`](../../meta/technical/effects.md).
- If the task touches one-shot commands, targeting flows, or action-bar behavior, also read [`meta/technical/actions.md`](../../meta/technical/actions.md).
- If the task touches city builds, food growth, border growth, or city-side turn behavior, also read [`meta/technical/city-production.md`](../../meta/technical/city-production.md).
- If the gameplay change affects tile selectors, unit rendering, unit healthbars/icons/hover overlays, world-space tile UI, or tile-local render models, also read [`meta/technical/rendering-system.md`](../../meta/technical/rendering-system.md).
- If the task touches rules, balance, or rule definitions, also read [`meta/technical/rules.md`](../../meta/technical/rules.md).
- If the gameplay change affects turn sequencing or per-turn behavior, also read [`meta/technical/turns.md`](../../meta/technical/turns.md).
- If the change affects persistence or entity lifecycle, also read [`meta/technical/entities.md`](../../meta/technical/entities.md).
- When adding or changing a reusable gameplay pattern, prefer updating or creating a guide in `meta/` rather than encoding the pattern only in chat memory.
