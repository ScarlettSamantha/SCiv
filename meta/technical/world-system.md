# World System

> Back to [Documentation Index](../INDEX.md)
>
> Related: [Architecture](architecture.md) | [World Generation](world-generation.md) | [Tile System](tile-system.md) | [Turn Processing](turns.md) | [City Production and Growth](city-production.md)

This page documents SCiv's runtime world container: how the `World` manager is initialized, how it tracks the authoritative tile collections, how new-game and load paths populate those collections, and how tile ownership and world-level turn work are coordinated.

## Scope and boundaries

- This page covers the live `World` manager after startup, during new-game setup, and during save/load restoration.
- It does **not** replace [World Generation](world-generation.md); that page documents how the generator builds tiles and terrain data.
- It does **not** replace [Tile System](tile-system.md); that page documents what each gameplay `Tile` owns.
- It does **not** cover Panda3D terrain nodes or renderers. Those live in [Rendering System](rendering-system.md).

## Ownership snapshot

| File | Responsibility |
| --- | --- |
| [`sciv/managers/world.py`](../../sciv/managers/world.py) | `World`: authoritative runtime container for tile collections, map size, lookup helpers, ownership transfer, and world-stage turn work. |
| [`sciv/managers/game.py`](../../sciv/managers/game.py) | Orchestrates new-game world reset/setup, save-load rehydration, and the handoff into render/camera/UI activation. |
| [`sciv/gameplay/repositories/tile.py`](../../sciv/gameplay/repositories/tile.py) | Query/pathing layer built on top of `World.grid`. |
| [`sciv/gameplay/tile.py`](../../sciv/gameplay/tile.py) | Tile entity instances stored inside `World.map` and `World.grid`. |
| [`sciv/system/generators/base.py`](../../sciv/system/generators/base.py) and [`sciv/system/generators/basic.py`](../../sciv/system/generators/basic.py) | Populate the live world on the new-game path. |

## End-to-end flow

```mermaid
flowchart TD
    Startup[OpenCiv.__init__()] --> Init[World singleton + __setup__()]
    Init --> NewGame[Game.generate_world()]
    NewGame --> Configure[World.generate()]
    Configure --> Populate[Generator creates tiles]
    Populate --> Grid[World.map / World.grid]
    Grid --> TileRepo[TileRepository.grid]
    Grid --> Claims[city requests + ownership transfer]
    Grid --> Turns[Turn.process() -> World.on_turn_end()]
    Load[Game.load()] --> Restore[World.load()]
    Restore --> Grid
    Reset[Game.reset_game()] --> Clear[World.reset()]
```

## World singleton lifecycle

### Startup construction

`OpenCiv.__init__()` creates `World(self)`, registers it as the singleton instance, and calls `world.__setup__(self)`.

`World.__setup__()` initializes:

- default map geometry fields
- `map` and `grid`
- `effects`
- the optional `generator` slot
- the city tile-request listener registration

### New-game preparation

`Game.generate_world()` uses the world manager as a container, not as a generator.

It:

1. calls `world.reset()`
2. calls `world.generate(cols, rows, radius, spacing)`
3. instantiates the active generator separately

So `World.generate()` prepares world dimensions and repository bindings, but does **not** instantiate tiles on its own.

### Save/load restoration

`Game.load()` bypasses generator code and calls `world.load(world_tiles)`.

That load path repopulates the runtime collections, recalculates world size, rebinds `TileRepository.grid`, restores dependent entities, and then hands tile state back to each `Tile.load_state()` call.

## Authoritative collections and geometry

The world manager keeps two authoritative tile collections:

- `map`: keyed by tile tag string
- `grid`: keyed by `(x, y)` coordinates

It also stores world geometry metadata:

- `cols`, `rows`
- `hex_radius`
- `col_spacing`, `row_spacing`
- `middle_x`, `middle_y`

The query/pathing layer in [`TileRepository`](../../sciv/gameplay/repositories/tile.py) is only as current as `World.grid`, which is why both `generate()` and `load()` rebind `TileRepository.grid`.

## What `World.generate()` actually does

`World.generate()` sets up runtime geometry and lookup surfaces for a new game:

- stores radius and spacing
- calculates middle coordinates
- resets tile-repository caches
- binds `TileRepository.grid` to the current world grid

It does **not** create gameplay tiles, improvements, or cities. The generator layer does that afterward.

## What `World.load()` actually does

The load path is ordered carefully.

`World.load()`:

1. repopulates `map` from restored tile entities
2. rebuilds `grid` from those tiles
3. recalculates `cols`, `rows`, and world center
4. rebinds `TileRepository.grid`
5. calls `load_state()` on improvements
6. calls `load_state()` on cities
7. calls `load_state()` on effects
8. calls `tile.load_state()` for every tile

That ordering matters because tiles, cities, and improvements restore references to one another.

## Ownership and city tile requests

### `set_ownership_of_tile()` is the authoritative transfer path

`World.set_ownership_of_tile(tile, player, city)` is the main ownership handoff for tiles.

It currently:

- removes the tile from the old owner's tile set if there was one
- detaches city ownership references from the old owner / old city when needed
- adds the tile to the new player's `PlayerTiles`
- stores `tile.city_owner` as a weak reference to the claiming city
- sets `tile.owner`
- updates city/player ownership when the tile itself is a city tile
- appends the tile to `city.owned_tiles`
- emits `game.gameplay.tiles.ownership_changed`

This is the canonical place where player-owned tile state and tile-side ownership state are kept in sync.

### City border growth routes through the world manager

`World` listens for `game.gameplay.city.requests_tile`.

`on_city_requests_tile()` only allows the claim when the target tile is:

- unowned
- owned by the session player
- or owned by the nature player

If the claim is allowed, it transfers ownership and emits:

- `game.gameplay.city.gets_tile_ownership`
- `game.gameplay.city.gets_tile_ownership_{city.tag}`

That listener is the bridge between city-side border growth and world-side ownership bookkeeping.

## World turn stage

`Turn.process()` runs the world stage first, and that stage delegates to `World.on_turn_end(turn)`.

The world manager does **not** process every tile every turn. It only forwards `tile.on_turn_end(turn)` for tiles that appear active enough to matter:

- owned tiles
- city tiles
- tiles with units
- tiles with effects
- tiles with improvements
- tiles marked with `needs_tile_proecessing`

After tile fan-out, world-level effects run through `self.effects.on_turn_end(turn)`.

The world stage now also owns gameplay vision recomputation. `World.refresh_player_vision()` aggregates city and unit emitters for a player, updates linger turns, recomputes tile states, and emits `game.gameplay.vision.updated`. `World.on_turn_end()` calls `refresh_all_player_vision()` before tile processing so fog transitions advance on turn boundaries.

Outside the turn loop, the world manager also refreshes vision on unit spawn, unit movement, unit destruction, city founding, and tile ownership changes. That keeps player vision authoritative in one place instead of scattering recompute logic across city, tile, and unit code.

## Reset semantics

`World.reset()` is a destructive runtime cleanup step, not just a dictionary clear.

It currently:

- clears `map` and `grid`
- rebuilds world-level `effects`
- destroys all live units from `EntityManager`
- destroys all live tiles from `EntityManager`
- resets `ModelHelper`

This is why `Game.reset_game()` can rely on the world manager as the main cleanup boundary for live tile/unit world state.

## Lookup helpers used around the codebase

The most common world-manager helpers are:

- `get_size()`
- `lookup_on_tag(tag)`
- `lookup(tag)`
- `get_grid()`
- `random_tile()`
- `get_generator()`

Most gameplay code eventually resolves into `TileRepository`, but the world manager is still the authoritative owner of the underlying collections.

## Current implementation notes

- `World.generate()` prepares the container and geometry only; tile creation still belongs to the generator layer.
- `World.generator` exists on the manager, but the default new-game path currently instantiates `self.properties.generator(...)` directly in `Game.generate_world()`.
- `on_city_requests_tile()` only allows claims against unowned, session-player-owned, or nature-owned tiles.
- `World.reset()` destroys entities in addition to clearing container state, so callers should treat it as a full runtime teardown boundary.