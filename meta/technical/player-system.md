# Player System

> Back to [Documentation Index](../INDEX.md)
>
> Related: [Architecture](architecture.md) | [World System](world-system.md) | [World Generation](world-generation.md) | [Turn Processing](turns.md) | [Entities and Save/Load](entities.md)

This page documents SCiv's player runtime: how players are created, how `PlayerManager` stores normal and mechanic players, what a gameplay `Player` owns, how player-side AI is assigned, and how player state participates in startup, turn processing, and save/load.

## Scope and boundaries

- This page covers the runtime player system: the player manager, gameplay `Player` entity, player-owned weak-reference tile set, AI ownership, and turn hooks.
- It does **not** cover Kivy player panels or HUD widgets. UI surfaces live in [UI Runtime](ui-runtime.md).
- It does **not** replace [World Generation](world-generation.md); that page documents when players are created during new-game startup.
- It does **not** replace [World System](world-system.md) or [Tile System](tile-system.md); those pages cover world ownership transfers and tile-side state.

## Ownership snapshot

| File | Responsibility |
| --- | --- |
| [`sciv/managers/player.py`](../../sciv/managers/player.py) | `PlayerManager`: role-aware registry for session, nature, barbarian, and normal players. |
| [`sciv/gameplay/player.py`](../../sciv/gameplay/player.py) | `Player`: empire-level entity owning units, cities, tiles, yields, civics, techs, effects, and AI. |
| [`sciv/gameplay/player_tiles.py`](../../sciv/gameplay/player_tiles.py) | Weak-reference wrapper for the tiles a player owns. |
| [`sciv/system/generators/base.py`](../../sciv/system/generators/base.py) | Creates players during new-game setup, sets player-role flags, and assigns AI implementations. |
| [`sciv/gameplay/ai/core.py`](../../sciv/gameplay/ai/core.py) | Base AI contract that exposes player-controlled units, cities, tiles, and world/player queries. |
| [`sciv/managers/turn.py`](../../sciv/managers/turn.py) | Runs player and city turn stages after the world stage. |
| [`sciv/gameplay/repositories/player.py`](../../sciv/gameplay/repositories/player.py) | Repository-style discovery for civilizations and leaders used during player setup. |

## End-to-end flow

```mermaid
flowchart TD
    Start[Game._try_game_start()] --> Setup[BaseGenerator.setup_players()]
    Setup --> Generate[BaseGenerator.generate_player()]
    Generate --> Assign[assign_ai()]
    Assign --> Register[Player.register() -> EntityManager]
    Register --> Slots[PlayerManager add / set_nature / set_barbarian]
    Slots --> MapGen[active_generator.generate()]
    MapGen --> GameStart[players.on_game_start()]
    GameStart --> Turns[Turn.process() player stage]
    Turns --> Save[Player.dump() / PlayerManager.load()]
    Save --> Load[Player.load_state()]
```

## Roles and registry model

`PlayerManager` does **not** store every role in the same collection.

### Normal players vs mechanic players

- `_players` holds the session player plus normal AI opponents, keyed by `turn_order`.
- `_session_player` stores a direct reference to the local human player.
- `_nature_player` stores the nature/system player.
- `_barbarian_player` stores the barbarian/system player.

That split matters because many call sites iterate `PlayerManager.all()` and only see `_players` unless they explicitly ask for mechanic players too.

### `all()` is role-sensitive

`PlayerManager.all(add_mechanic_players=False)` returns a copy of `_players`.

Because the session player is also stored in `_players`, the practical effect is:

- default `all()` => session player + normal AI enemies
- `all(add_mechanic_players=True)` => session player + normal AI enemies + nature + barbarian

So the extra flag mostly matters for the mechanic players.

## Player creation during new-game startup

### `BaseGenerator.setup_players()` owns initial creation

The current new-game path creates players **before** tile generation finishes.

In the default ordering:

- turn order `0` = local human player
- turn order `1` = nature player
- turn order `2` = barbarian player
- remaining turn orders = normal AI opponents

If `start_config.players` is present, the generator preserves that configured ordering for normal players, while still injecting nature and barbarian slots immediately after the local player.

### `generate_player()` sets the role contract

`BaseGenerator.generate_player()`:

1. chooses or generates a leader if needed
2. constructs the gameplay `Player`
3. sets `is_human`, `is_nature`, and `is_barbarian`
4. installs the default tech and civic trees
5. assigns an AI implementation
6. registers the player with `EntityManager` if not already registered

AI assignment is role-driven:

- human player → `PlayerAI`
- nature player → `NatureAI`
- barbarian player → `BarbariansAI`
- normal opponents → `EnemyAI`

## What a gameplay `Player` owns

`Player` is a large empire-level entity. The most important categories are:

### Identity and role

- `turn_order`
- `civilization`
- `leader`
- `tag` / `entity_key`
- `is_human`, `is_nature`, `is_barbarian`, `is_defeated`

### Empire collections

- `cities`
- `units`
- `tiles`
- `claims`
- `vision`
- `citizens`
- `resources`

### Economy and progression

- `science`, `culture`, `faith`, `gold`
- `tech`
- `civics`
- `government`
- `effects`

### Relationships and higher-level state

- `mood` / `moods`
- `relationships`
- `votes`
- `trades`
- war-fatigue and standing-style fields

In practice, `Player` is the runtime home for empire state, while `PlayerManager` is the role-aware lookup surface for the rest of the game.

## Player-owned vision state

`Player.vision` is now the gameplay-owned visibility index for each empire.

Important details:

- units and cities emit visible tiles independently
- the player aggregates those emitters through `collect_visible_tiles()`
- the `Vision` object stores per-tile states instead of only a flat visible-tile bag
- visibility can linger for a configurable number of turns after sight is lost
- player effects can extend linger duration and modify emitter ranges

See [Vision and Fog of War](vision-fog.md) for the detailed state machine and recompute flow.

## Player-owned tile state

`Player.tiles` is a [`PlayerTiles`](../../sciv/gameplay/player_tiles.py) wrapper, not a plain dictionary.

Important details:

- tiles are stored by `(x, y)`
- values are weak references to `Tile`
- `get_tiles()` resolves only still-live tile references
- `dump()` serializes tile tags
- `load_state()` rebuilds the weak references through `EntityManager`

This is why world ownership transfer flows through the world manager instead of letting callers mutate player-owned tile state directly.

## Save/load boundary

### `Player.dump()` serializes the empire surface

Player serialization includes:

- leader, personality, civilization, and AI dump payloads
- cities, units, and owned-tile references
- civics and tech manager state
- vision, citizens, effects, resources, and messages
- capital reference by tag

### `Player.load_state()` rebuilds nested systems

On load, `Player.load_state()` reconstructs or restores:

- `TechManager` and `CivicsManager`
- `Cities`, `Units`, and `PlayerTiles`
- `Effects`
- civilization, leader, AI, and personality objects through dynamic import
- messenger state and logger bindings

`PlayerManager.load()` then reassigns players into session, nature, barbarian, or normal-player buckets based on the saved role flags.

## Startup and turn lifecycle

### Startup-owned handoff

After world generation and render setup, [`Game._try_game_start()`](../../sciv/managers/game.py) calls `self.players.on_game_start()`.

Before that handoff, `Game.calculate_vision()` now delegates to the world manager so each player's vision cache is built from live unit and city emitters instead of revealing the full map.

`PlayerManager.on_game_start()` currently:

1. calls `get_nature().on_game_start()`
2. calls `on_game_start()` for every player in `_players`

That means the normal human/enemy players and the nature player get a startup hook through the manager.

### Turn-owned fan-out

The authoritative per-turn player order lives in [`Turn.process()`](../../sciv/managers/turn.py):

1. nature player
2. barbarian player
3. every player in `PlayerManager.all()`
4. every city owned by each normal/session player

At the player level, `Player.on_turn_end()`:

- runs player-side effects
- runs AI turn logic unless debug settings disable AI turn processing

### Current AI activity level

The AI layer is wired up for all player roles, but the implementations are not equally active today:

- `NatureAI` performs meaningful startup and turn work, including spawn-cache setup and goal processing
- `PlayerAI`, `EnemyAI`, and `BarbariansAI` currently expose the right hooks but mostly implement no-op `on_game_start()` / `on_turn_end()` bodies

So the player system already has a stable role/AI contract, but only part of it is fully behavior-rich right now.

The shared AI base now also exposes settler-site helper methods backed by the shared founding recommendation/scoring module. That gives future AI implementations a common way to ask for recommended city sites without duplicating the generator's settlement heuristics, even though the default human/enemy/barbarian AI turn bodies are still mostly no-op today.

## Common lookup surface

The most-used `PlayerManager` helpers are:

- `player()` / `session_player()` — local human player
- `get_nature()`
- `get_barbarian()`
- `get(turn_order)`
- `get_by_tag(tag)`
- `all(add_mechanic_players=...)`
- `get_capital(player)` / `if_has_capital(player)`

When a caller needs mechanic players included, it should say so explicitly.

## Current implementation notes

- `PlayerManager.on_game_start()` currently calls the nature player and normal/session players, but **not** the barbarian player.
- `PlayerManager.reset()` currently clears `_players`, `_session_player`, and `_nature_player`, but does **not** clear `_barbarian_player`.
- The session player is stored in both `_players` and `_session_player`, so `all()` already includes the session player even without `add_mechanic_players=True`.
- Player creation is generator-owned, while per-turn fan-out is turn-manager-owned.