---
name: "SCiv World System Routing"
description: "Use when editing SCiv's runtime world container, tile ownership handoff, or world-level turn orchestration. Routes world-system work to the right docs first."
applyTo: "{sciv/managers/world.py}"
---

# SCiv World System Routing

- Read [`meta/technical/world-system.md`](../../meta/technical/world-system.md) first for the live world container, authoritative tile collections, ownership transfer flow, and world-stage turn filtering.
- Also read [`meta/technical/tile-system.md`](../../meta/technical/tile-system.md), [`meta/technical/world-generation.md`](../../meta/technical/world-generation.md), and [`meta/technical/turns.md`](../../meta/technical/turns.md) because the world manager sits between generation, tile state, and turn processing.
- If the change touches city border growth or tile-claim signals, also read [`meta/technical/city-production.md`](../../meta/technical/city-production.md) and [`meta/technical/signals.md`](../../meta/technical/signals.md).
- Remember that `World.generate()` prepares dimensions and repository bindings, but tile creation still belongs to the generator layer.
- When world-container ownership or routing changes, update [`meta/technical/world-system.md`](../../meta/technical/world-system.md), [`meta/technical/update-triggers.md`](../../meta/technical/update-triggers.md), and the orientation routing matrix in the same change.
