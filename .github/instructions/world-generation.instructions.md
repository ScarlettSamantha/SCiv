---
name: "SCiv World Generation Routing"
description: "Use when editing SCiv world generation, generator selection, hexgen terrain creation, resource allocation, or starting-unit placement. Routes generator work to the required technical docs first."
applyTo: "{sciv/system/generators/**,sciv/system/subsystems/hexgen/**,sciv/system/game_settings.py,sciv/managers/world.py,sciv/managers/game.py,sciv/gameplay/repositories/generators.py}"
---

# SCiv World Generation Routing

- Read [`meta/technical/world-generation.md`](../../meta/technical/world-generation.md) first for the new-game generation flow, generator contract, and hexgen-to-gameplay boundary.
- If the change touches the conversion boundary from hexgen into gameplay tiles or the generator-created `model_grid`, also read [`meta/technical/tile-system.md`](../../meta/technical/tile-system.md) and [`meta/technical/rendering-system.md`](../../meta/technical/rendering-system.md).
- If the task touches the loading-screen handoff or the larger new-game start path, also read [`meta/technical/startup.md`](../../meta/technical/startup.md) and [`meta/technical/architecture.md`](../../meta/technical/architecture.md).
- When generator responsibilities or routing change, update [`meta/technical/world-generation.md`](../../meta/technical/world-generation.md), [`meta/technical/update-triggers.md`](../../meta/technical/update-triggers.md), and the orientation routing matrix in the same change.
