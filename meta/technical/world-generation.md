# World Generation

> Back to [Documentation Index](../INDEX.md)
>
> Related: [Architecture](architecture.md) | [World System](world-system.md) | [Player System](player-system.md) | [Startup Flow](startup.md) | [Rendering System](rendering-system.md) | [Signals](signals.md) | [Documentation Audit](../documentation-audit.md)

This document covers SCiv's **new-game** world generation path: how a start-game request turns into live gameplay `Tile` entities, resources, starting units, renderable terrain, and the signals that hand control back to the active game UI.

## Scope and boundaries

- This page covers the **new-game generation path**, not save/load restoration.
- [`Game.load()`](../../sciv/managers/game.py) restores persisted entities and bypasses generator code.
- [`World.generate()`](../../sciv/managers/world.py) only configures world dimensions and spacing. It does **not** instantiate gameplay tiles by itself. The runtime world-container contract lives in [World System](world-system.md).
- The default generator is [`Basic`](../../sciv/system/generators/basic.py), which bridges the lower-level hexgen pipeline into gameplay tiles.

## Ownership snapshot

| Layer | Primary files | Responsibility |
| --- | --- | --- |
| Game start orchestration | [`sciv/managers/game.py`](../../sciv/managers/game.py), [`sciv/menus/screens/game_config.py`](../../sciv/menus/screens/game_config.py) | Accept start-game requests, store settings, schedule loading-screen work, and activate the runtime after generation completes. |
| World runtime container | [`sciv/managers/world.py`](../../sciv/managers/world.py) | Owns map dimensions, world spacing, the authoritative gameplay tile grid, and world-level lookup helpers. |
| Generator contract | [`sciv/system/generators/base.py`](../../sciv/system/generators/base.py) | Defines the generator API, shared player setup, debug metadata, and starting-unit placement helpers. |
| Default generator implementation | [`sciv/system/generators/basic.py`](../../sciv/system/generators/basic.py) | Runs hexgen, converts raw hexes into gameplay tiles, assigns models, allocates resources, and places starting units. |
| Raw terrain pipeline | [`sciv/system/subsystems/hexgen/`](../../sciv/system/subsystems/hexgen) | Produces the temporary hex grid, height/temperature/moisture data, rivers, territories, geoforms, and terrain classification inputs. |
| Post-conversion population | [`sciv/system/generators/resource_allocator.py`](../../sciv/system/generators/resource_allocator.py) | Places bonus/luxury/strategic resources across the generated gameplay tile grid. |

## End-to-end flow

```mermaid
flowchart TD
    Config[GameConfigMenu / MainMenu] --> StartSignal[system.game.start_load]
    StartSignal --> Start[Game.on_game_start()]
    Start --> Delay[loading screen + _try_game_start()]
    Delay --> Prep[Game.generate_world()]
    Prep --> Players[BaseGenerator.setup_players()]
    Players --> Seed[active_generator.randomize_seed()]
    Seed --> Generate[active_generator.generate()]
    Generate --> HexGen[MapGen]
    HexGen --> Convert[terrain classification + tile instantiation]
    Convert --> Resources[ResourceAllocator.allocate_resources()]
    Resources --> Units[place_starting_units()]
    Units --> Activate[render field + borders + vision]
    Activate --> Ready[game.state.true_game_start]
```

## Important messages in the sequence

| Message | Emitter | Meaning |
| --- | --- | --- |
| `system.game.start_load` | `GameConfigMenu.start_game()` or main-menu quick start | Requests a new game with map size, player civ, player count, and optional pregame config. |
| `ui.request.loading_screen` | `Game.on_game_start()` | Opens the loading screen before heavy work starts. |
| `ui.loading.next_step` | `Basic.generate()` | Advances the visible loading-screen stage as generation progresses. |
| `game.state.load_complete` | `Game._try_game_start()` | Marks the end of the generation/load-style world build phase. |
| `game.state.true_game_start` | `Game._try_game_start()` | Signals that the new playable runtime is ready. |
| `game.border.refresh` | `Game._try_game_start()` | Refreshes border visuals after the world and players exist. |

## New-game sequence in practice

### 1. Start request and settings capture

[`GameConfigMenu.start_game()`](../../sciv/menus/screens/game_config.py) emits `system.game.start_load` with:

- the requested map size
- the local player's civilization
- the configured player count
- a `start_config` payload containing pregame options, rules, and per-player civ/leader selections

[`Game.on_game_start()`](../../sciv/managers/game.py) then:

1. updates `GameSettings` with width, height, civilization, and player count
2. stores `start_config` if present
3. sends `ui.request.loading_screen`
4. schedules `_try_game_start()` after a short delay so the loading screen can appear first

### 2. Pre-generation setup in `Game._try_game_start()`

Before terrain generation begins, [`Game._try_game_start()`](../../sciv/managers/game.py) re-establishes core runtime state:

- caches the active `ShowBase`
- creates or refreshes debug and entity managers
- calls `generate_world()`
- creates session players through `setup_players()`
- randomizes and stores the world seed

The subtle but important part is that `generate_world()` does **not** build tiles yet. It only prepares the world container and instantiates the active generator.

### 3. What `Game.generate_world()` actually does

[`Game.generate_world()`](../../sciv/managers/game.py) performs three setup steps:

1. resets the `World` manager
2. calls [`World.generate()`](../../sciv/managers/world.py) to set columns, rows, radius, spacing, and world-center values
3. instantiates the current generator from `self.properties.generator`

After this point, the active generator exists, but the gameplay tile grid is still empty.

### 4. Player setup happens before terrain conversion

[`BaseGenerator.setup_players()`](../../sciv/system/generators/base.py) runs before `active_generator.generate()`.

That setup phase:

- creates the local human player
- creates the special nature and barbarian players
- creates remaining AI opponents
- assigns AI implementations based on player role
- applies configured civilization/leader selections when present in `start_config`

The actual map still does not exist yet at this stage. Starting units are placed later, after tile generation finishes.

The long-lived runtime contract for those players after setup lives in [Player System](player-system.md).

## Generator contract and current default

[`BaseGenerator`](../../sciv/system/generators/base.py) is the common contract shared by world generators.

Its main responsibilities are:

- `generate()` — build the world and return success/failure
- `randomize_seed()` — choose and persist a generation seed
- `generate_player()` / `setup_players()` — create human, AI, nature, and barbarian players
- `place_starting_units()` — place starting units on the final gameplay tile grid
- `model_grid` — expose the generated `TileModelGrid` used by the live runtime
- `world_generation_stats` and `debug_dump_data` — hold generation metadata for inspection/debugging

The default implementation is [`Basic`](../../sciv/system/generators/basic.py), whose declared purpose is “Generates a hex-based map using HexGen.”

## `Basic.generate()` pipeline

`Basic.generate()` is the current authoritative new-game generation pipeline.

### Phase 1: Raw hexgen map

`Basic.generate()` creates a [`MapGen`](../../sciv/system/subsystems/hexgen/mapgen.py) instance and stores its resulting [`Grid`](../../sciv/system/subsystems/hexgen/grid.py).

At this stage the world is still made of temporary hexgen `Hex` objects rather than gameplay `Tile` entities.

### Phase 2: Terrain classification and conversion prep

The generator iterates over the requested output rectangle and assigns each raw hex:

- a terrain string via `classify_terrain()`
- a render position based on world spacing and odd/even column offset

Terrain classification currently depends on:

- altitude thresholds from `WorldParams`
- water / lake / coast / sea / ocean classification
- moisture-derived biome decisions
- cold/hot thresholds
- feature overrides such as volcanoes

### Phase 3: Water and terrain cleanup passes

After raw classification, `Basic` performs several generator-side cleanup passes before gameplay tiles are instantiated:

- `adjust_water_levels()` — lowers contiguous water clusters to one below their minimum adjacent land altitude
- `_promote_single_sea_between_coasts()` — promotes a narrow `Sea` tile into `Coast` in a specific opposite-coast case
- `_desertize_adjacent_tundra()` — converts certain tundra tiles adjacent to desert into desert

These are generator conversion rules, not general gameplay rules.

### Phase 4: Gameplay tile instantiation

`instantiate_tiles()` turns classified raw hexes into live gameplay tiles:

1. choose a gameplay tile class from `gameplay/tiles`
2. instantiate it with grid coordinates and render coordinates
3. copy worldgen-derived data with `enrich_from_extra_data()`
4. register the tile into `World.map`, `World.grid`, and later `TileRepository.grid`

`enrich_from_extra_data()` transfers worldgen data such as:

- altitude
- temperature
- moisture
- biome
- geoform / waterbody type
- worldgen features
- resource chosen by hexgen, if any
- land/water/coast/lake/sea flags

It also carries over weak references to the raw hexgen `Edge` objects into the gameplay tile edge slots.

### Phase 5: Terrain model grid

Once tiles exist, `Basic`:

- assigns each tile its terrain model metadata
- builds a [`TileModelGrid`](../../sciv/system/tile_grid.py)
- attaches that model grid to render
- recalculates per-tile grid positions

This model grid becomes the generator's exposed `model_grid` and is later reused by the live game runtime.

The details of how that model grid behaves once attached to the scene live in [Rendering System](rendering-system.md).

### Phase 6: Resource allocation

After tile instantiation and terrain-model setup, [`ResourceAllocator`](../../sciv/system/generators/resource_allocator.py) places gameplay resources.

The allocator:

- filters tiles by water/land rules and terrain compatibility
- respects each resource's spawn filters and coverage targets
- optionally clusters resources with a distance-based dropoff
- writes resources onto gameplay tiles, not raw hexgen hexes

### Phase 7: Starting units

Finally, `place_starting_units()` runs on gameplay tiles.

The current heuristic looks for spawn tiles that are:

- spawnable and passable
- not too close to already assigned starting positions
- not too close to the map edge
- surrounded by enough land within a configurable radius
- preferably near coast

For each normal player, the generator currently places:

- a `Settler`
- an adjacent `ClubMan` when a valid companion tile exists

### Phase 8: Stats, metadata, and completion

At the end of `Basic.generate()` the generator records:

- phase durations in milliseconds
- the final seed
- map size
- timestamps for the start/end of the pipeline

These stats are stored in `EntityManager` metadata as `world_generation_stats`.

## Inside the hexgen subsystem

[`MapGen`](../../sciv/system/subsystems/hexgen/mapgen.py) is the heavy lower-level terrain generator that feeds `Basic`.

### `Heightmap`

[`Heightmap`](../../sciv/system/subsystems/hexgen/heightmap.py) creates a square height grid by:

- seeding corner values
- recursively subdividing the grid with random roughness offsets
- computing average, minimum, and maximum height
- deriving sea level from average height and configured sea percentage

### `Grid` and `Hex`

[`Grid`](../../sciv/system/subsystems/hexgen/grid.py) converts the heightmap into a square array of [`Hex`](../../sciv/system/subsystems/hexgen/hex.py) objects.

Each `Hex` exposes derived worldgen state such as:

- land vs water from altitude vs sea level
- latitude and hemisphere
- base temperature from latitude and altitude
- moisture
- biome
- neighboring hexes and edge graph
- geoforms, territories, and features

### Major `MapGen` passes

The current `MapGen` sequence is roughly:

1. build the heightmap
2. build the hex grid
3. compute inland/coast distance fields
4. generate rivers and aquifer-style moisture sources when hydrosphere is enabled
5. optionally add craters and volcanoes
6. generate territories
7. determine landforms and water geoforms
8. detect lakes
9. diffuse moisture from coasts, rivers, and lakes
10. run integrity checks in debug mode

### Geoforms and features

The hexgen subsystem distinguishes between:

- **geoforms** such as `ocean`, `sea`, `lake`, `continent`, `large_island`, `small_island`, `isthmus`, and `peninsula`
- **features** such as `volcano`, `crater`, `lake`, `bay`, `strait`, and `peninsula`

Geoforms are grouped via [`Geoform`](../../sciv/system/subsystems/hexgen/geoform.py), while hydrology is represented as linked [`RiverSegment`](../../sciv/system/subsystems/hexgen/river.py) objects and territory expansion uses [`Territory`](../../sciv/system/subsystems/hexgen/territory.py).

## Data handoff and persistence boundary

The important boundary is this:

- raw hexgen `Hex`, `Edge`, `Geoform`, `RiverSegment`, and `Territory` objects are generator-time structures
- gameplay `Tile` entities are the long-lived world objects used by the rest of the runtime

After generation completes, the authoritative world state lives in:

- `World.map`
- `World.grid`
- `TileRepository.grid`

The generator-time structures are not registered as gameplay entities through `EntityManager`.

## Activation after generation

Once `active_generator.generate()` returns successfully, [`Game._try_game_start()`](../../sciv/managers/game.py):

1. stores the generator's `model_grid` as `world_tile_grid`
2. registers all generated tiles with [`TileRendererSystem`](../../sciv/system/tile_renderer.py)
3. renders the field by calling `tile.render()` for every tile
4. activates ages, borders, vision, and player start hooks
5. emits `game.state.load_complete`, `game.state.true_game_start`, and `game.border.refresh`

This is the handoff point from world generation to the live playable runtime.

## Debugging and inspection hooks

There are two main generation-debug outputs today:

- `world_generation_stats` metadata written through `EntityManager`
- `Debug.dump_map_generation_data()` which writes a gzipped JSON map dump when world-generation debug dumping is enabled

The per-tile debug dump includes:

- coordinates
- altitude
- temperature
- moisture
- terrain
- water / land / coast / sea / lake flags
- geoform type
- features
- visible resource assignment

## Observed current implementation notes

These describe the **current code path**, not necessarily the long-term design target.

- `GameSettings.__init__()` currently stores `Basic` as `self.generator`, even though a `generator` constructor parameter exists.
- `Basic` currently calls `MapGen(..., debug=True)`, so hexgen debug timing/logging is always enabled from that path.
- `Basic.map_params["size"]` is `max(width, height)`, so hexgen builds a square raw grid before `Basic` converts only the configured rectangular output area.
- `World.generator`, `Game.choose_generator()`, and `GeneratorRepository` exist, but the default new-game path ultimately instantiates `self.properties.generator(...)` in `Game.generate_world()`.
- Gameplay tiles still keep weak references to hexgen `Edge` objects after conversion.

## Files to inspect when changing world generation

- [`sciv/managers/game.py`](../../sciv/managers/game.py)
- [`sciv/managers/world.py`](../../sciv/managers/world.py)
- [`sciv/system/game_settings.py`](../../sciv/system/game_settings.py)
- [`sciv/system/generators/base.py`](../../sciv/system/generators/base.py)
- [`sciv/system/generators/basic.py`](../../sciv/system/generators/basic.py)
- [`sciv/system/generators/resource_allocator.py`](../../sciv/system/generators/resource_allocator.py)
- [`sciv/system/subsystems/hexgen/`](../../sciv/system/subsystems/hexgen)
- [`sciv/menus/screens/game_config.py`](../../sciv/menus/screens/game_config.py)

Update this page when changes affect:

- generator selection or seed ownership
- hexgen terrain/hydrology/geoform behavior
- the conversion boundary from raw hexes into gameplay tiles
- resource placement or starting-unit heuristics
- the signals or runtime handoff that follow generation