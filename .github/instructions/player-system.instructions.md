---
name: "SCiv Player System Routing"
description: "Use when editing SCiv player registry, player entities, player AI ownership, player-role setup, or player-owned tile collections. Routes player-system work to the right docs first."
applyTo: "{sciv/managers/player.py,sciv/gameplay/player.py,sciv/gameplay/player_tiles.py,sciv/gameplay/repositories/player.py,sciv/gameplay/ai/**,sciv/system/generators/base.py}"
---

# SCiv Player System Routing

- Read [`meta/technical/player-system.md`](../../meta/technical/player-system.md) first for player-role storage, player lifecycle, AI assignment, startup/turn hooks, and save/load boundaries.
- Also read [`meta/technical/turns.md`](../../meta/technical/turns.md), [`meta/technical/world-generation.md`](../../meta/technical/world-generation.md), and [`meta/technical/entities.md`](../../meta/technical/entities.md) because player setup, turn work, and persistence are split across those layers.
- If the change touches player-owned tiles, border claims, or ownership transfer with the world manager, also read [`meta/technical/world-system.md`](../../meta/technical/world-system.md) and [`meta/technical/tile-system.md`](../../meta/technical/tile-system.md).
- Remember that `PlayerManager.all()` returns normal/session players by default; nature and barbarian are separate mechanic-player slots unless explicitly requested.
- When player ownership or routing changes, update [`meta/technical/player-system.md`](../../meta/technical/player-system.md), [`meta/technical/update-triggers.md`](../../meta/technical/update-triggers.md), and the orientation routing matrix in the same change.
