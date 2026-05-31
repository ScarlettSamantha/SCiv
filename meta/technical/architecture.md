# Architecture

> Back to [Documentation Index](../INDEX.md)

This document explains the major runtime layers in SCiv and how they cooperate at a high level. Use it together with [Startup Flow](startup.md), [Asset System](asset-system.md), [World System](world-system.md), [Tile System](tile-system.md), [Player System](player-system.md), [Rendering System](rendering-system.md), [UI Runtime](ui-runtime.md), [World Generation](world-generation.md), [Entities and Save/Load](entities.md), and [Turn Processing](turns.md).

## System overview

```mermaid
flowchart TD
    Run[run.py] --> Bootstrap[sciv/__main__.py bootstrap()]
    Bootstrap --> OpenCiv[sciv/game.py OpenCiv]
    OpenCiv --> Managers[sciv/managers/*]
    Managers --> Gameplay[sciv/gameplay/*]
    Managers --> Systems[sciv/system/*]
    Managers --> UI[sciv/menus/*]
    Managers --> Helpers[sciv/helpers/*]
    Managers --> Mixins[sciv/mixins/*]

    Managers --> GameManager[managers/game.py Game]
    Managers --> WorldManager[managers/world.py World]
    Managers --> EntityManager[managers/entity.py EntityManager]
    Managers --> TurnManager[managers/turn.py Turn]
    Managers --> UIManager[managers/ui.py ui]

    GameManager --> TurnManager
    GameManager --> WorldManager
    GameManager --> EntityManager
    UIManager --> UI
    WorldManager --> Systems
    EntityManager --> Gameplay
    TurnManager --> Gameplay
```

## Main runtime layers

| Layer | Primary files | Responsibility |
| --- | --- | --- |
| Bootstrap | [`run.py`](../../run.py), [`sciv/__main__.py`](../../sciv/__main__.py), [`sciv/game.py`](../../sciv/game.py) | Starts the app, patches Kivy into Panda3D, sets up managers, and opens the initial UI flow. |
| Managers | [`sciv/managers/`](../../sciv/managers) | Owns long-lived coordination: game flow, world access, turn processing, UI state, players, entities, techs, civics, and logging. |
| Gameplay | [`sciv/gameplay/`](../../sciv/gameplay) | Domain model for players, tiles, cities, units, rules, effects, diplomacy, yields, and other game mechanics. |
| Systems | [`sciv/system/`](../../sciv/system) | Engine-facing systems such as rendering, camera, effects orchestration, save/load helpers, asset handling, and world generation. |
| UI | [`sciv/menus/`](../../sciv/menus), [`sciv/managers/ui.py`](../../sciv/managers/ui.py) | Kivy screens and widgets, plus the manager that bridges UI events back into the game runtime. |
| Shared utilities | [`sciv/helpers/`](../../sciv/helpers), [`sciv/mixins/`](../../sciv/mixins) | Reusable helpers and patterns such as caching, path helpers, debugging utilities, and the singleton implementation. |

## Core runtime ownership

### `OpenCiv` owns application bootstrap

`OpenCiv` in [`sciv/game.py`](../../sciv/game.py) is the main application host. It extends Panda3D's `ShowBase`, configures the engine and Kivy bridge, constructs major managers, and emits `system.main.ready` when the UI is ready to show the main menu.

### Managers own orchestration, not the domain model

The manager layer is where long-lived coordination lives:

- `Game` starts or loads a session, builds the world, and coordinates resets.
- `World` owns tile lookup, world dimensions, tile ownership changes, and world-level per-turn work.
- `PlayerManager` owns session/nature/barbarian/player role lookup and player registry access.
- `EntityManager` owns the saveable object registry and serialization.
- `Turn` owns the per-turn pipeline and signal emission.
- `Input` owns raw Panda3D input bindings, camera-ray picking, and hovered/selected world-object state.
- `ui` owns the Kivy screen bridge and the currently selected tile/unit UI state.

The gameplay layer provides the domain objects these managers operate on.

Deeper runtime contracts for those manager/gameplay boundaries live in [World System](world-system.md), [Tile System](tile-system.md), and [Player System](player-system.md).

### Gameplay objects are stateful domain entities

Gameplay objects such as players, tiles, cities, units, improvements, resources, and effects live under [`sciv/gameplay/`](../../sciv/gameplay). Many of them inherit from `BaseEntity`, which gives them stable identity, inspection hooks, and save/load support.

### Systems translate domain state into engine behavior

The system layer turns gameplay state into concrete engine behavior:

- rendering and scene updates
- save/load helpers
- world generation
- shader and asset handling
- effect and action execution

This layer is where Panda3D-facing code and serialization helpers tend to live.

The packaged archive, generated icon outputs, and atlas/cache bridges that feed those systems are documented separately in [Asset System](asset-system.md).

In the current world stack, rendering is split into a few distinct responsibilities:

- `TileModelGrid` owns terrain model placement and grouped terrain instances.
- `TileRenderer` owns each tile's local anchor, click surface, selector, model attachments, and world-space UI.
- `TileRendererSystem` owns the instanced resource/yield/population icon overlay above tiles.

The gameplay-facing side of that contract lives in [Tile System](tile-system.md), while the Panda3D-facing side lives in [Rendering System](rendering-system.md).

## Cross-cutting patterns

### Singleton-backed managers

Most managers rely on [`sciv/mixins/singleton.py`](../../sciv/mixins/singleton.py). The singleton mixin supports deferred `__setup__()` calls, which lets callers pass runtime dependencies during first construction without having to wire a dedicated service container.

### Messenger-driven coordination

SCiv uses Panda3D messenger signals heavily. Startup, turn flow, UI actions, and gameplay events are all routed through named messages. The signal catalog lives in [Signals](signals.md), while [Startup Flow](startup.md) and [Turn Processing](turns.md) explain the most important message sequences.

### Entity + weak-reference model

Persistent gameplay objects are tracked by `EntityManager`, while relationships between them often use weak references to reduce circular ownership. See [Entities and Save/Load](entities.md) for the full lifecycle.

### Panda3D + Kivy hybrid UI

SCiv does not run Panda3D and Kivy as separate apps. Instead, Kivy is patched into the Panda3D window during startup, then the UI manager and Kivy app coordinate screen changes and user interactions inside the same runtime.

### Camera-attached world picking

`Input` uses a Panda3D `CollisionRay` attached to the camera to pick tiles, units, and other world-selection targets. Keep the picker node as a from-only collider by clearing its `into` mask with `BitMask32.allOff()`: Panda3D `CollisionNode`s default to a nonzero `into` mask, which can otherwise surface `CollisionRay into CollisionRay` traversal errors when the input raycaster is active.

The world camera pivots over the rendered tile footprint, but its pan target is clamped to cached world tile bounds with a small zoom-scaled overscroll margin. That allows a little edge peeking so the map can sit slightly off-center without letting the player drift far into empty space.

Camera motion now eases toward desired pan, yaw, and zoom targets each frame instead of stepping in coarse update batches, and pan speed scales up with zoomed-out views so world navigation feels smoother and more strategy-game-like.

## Practical navigation guide

If you are trying to answer a specific question, start here:

- **How does the app boot?** → [Startup Flow](startup.md)
- **How are assets packaged, cached, and exposed to renderers/UI?** → [Asset System](asset-system.md)
- **How does the world runtime container work?** → [World System](world-system.md)
- **How does the live screen/UI runtime behave?** → [UI Runtime](ui-runtime.md)
- **How do gameplay tiles work?** → [Tile System](tile-system.md)
- **How do players, player roles, and player AI ownership work?** → [Player System](player-system.md)
- **How is the world rendered?** → [Rendering System](rendering-system.md)
- **How does a new world get built?** → [World Generation](world-generation.md)
- **Where are turn stages defined?** → [Turn Processing](turns.md)
- **How are entities persisted?** → [Entities and Save/Load](entities.md)
- **Where are signals listed?** → [Signals](signals.md)
- **What files exist and where?** → [Project Structure](../structure.md) or [`meta/generated/project-index.json`](../generated/project-index.json)