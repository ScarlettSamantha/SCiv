# World Generation

> Back to [Documentation Index](../INDEX.md)
>
> Related: [Architecture](architecture.md) | [World System](world-system.md) | [Player System](player-system.md) | [Startup Flow](startup.md) | [Rendering System](rendering-system.md) | [Signals](signals.md) | [Documentation Audit](../documentation-audit.md)

This document covers SCiv's **new-game** world generation path: how a start-game request turns into live gameplay `Tile` entities, resources, starting units, renderable terrain, and the signals that hand control back to the active game UI.

## Scope and boundaries

- This page covers the **new-game generation path**, not save/load restoration.
- [`Game.load()`](../../sciv/managers/game.py) restores persisted entities and bypasses generator code.
- [`World.generate()`](../../sciv/managers/world.py) only configures world dimensions and spacing. It does **not** instantiate gameplay tiles by itself. The runtime world-container contract lives in [World System](world-system.md).
- [`Basic`](../../sciv/system/generators/basic.py) remains the baseline generator implementation that bridges the lower-level hexgen pipeline into gameplay tiles.
- SCiv also ships [`Dynamic`](../../sciv/system/generators/dynamic.py), a separate preset-driven generator that layers map-script and climate options on top of the same hexgen pipeline.
- The pregame config screen and the debug quick-start path currently default to [`Dynamic`](../../sciv/system/generators/dynamic.py), while keeping `Basic` available as an explicit selector choice.

## Ownership snapshot

| Layer | Primary files | Responsibility |
| --- | --- | --- |
| Game start orchestration | [`sciv/managers/game.py`](../../sciv/managers/game.py), [`sciv/menus/screens/game_config.py`](../../sciv/menus/screens/game_config.py) | Accept start-game requests, store settings, schedule loading-screen work, and activate the runtime after generation completes. |
| World runtime container | [`sciv/managers/world.py`](../../sciv/managers/world.py) | Owns map dimensions, world spacing, the authoritative gameplay tile grid, and world-level lookup helpers. |
| Generator contract | [`sciv/system/generators/base.py`](../../sciv/system/generators/base.py) | Defines the generator API, shared player setup, debug metadata, and starting-unit placement helpers. |
| Default generator implementation | [`sciv/system/generators/basic.py`](../../sciv/system/generators/basic.py) | Runs hexgen, converts raw hexes into gameplay tiles, assigns models, allocates resources, and places starting units. |
| Preset-driven generator implementation | [`sciv/system/generators/dynamic.py`](../../sciv/system/generators/dynamic.py), [`sciv/system/generators/dynamic_worlds/`](../../sciv/system/generators/dynamic_worlds) | Extends the basic pipeline with selectable landmass and biome presets, script-aware coastline polish, named world metadata, and Dynamic-specific post-processing while still reusing the shared basic conversion flow. |
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
- a `start_config` payload containing pregame options, rules, per-player civ/leader selections, and generator configuration

[`Game.on_game_start()`](../../sciv/managers/game.py) then:

1. updates `GameSettings` with width, height, civilization, and player count
2. selects the requested generator class and sanitizes any generator-specific setup options from `start_config`
3. stores `start_config` if present
4. sends `ui.request.loading_screen`
5. schedules `_try_game_start()` after a short delay so the loading screen can appear first

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
- `get_setup_fields()` / `sanitize_setup_options()` — declare and validate generator-specific setup-screen options
- `model_grid` — expose the generated `TileModelGrid` used by the live runtime
- `world_generation_stats` and `debug_dump_data` — hold generation metadata for inspection/debugging

The default implementation is [`Basic`](../../sciv/system/generators/basic.py), whose declared purpose is “Generates a hex-based map using HexGen.”

The preset-driven implementation is [`Dynamic`](../../sciv/system/generators/dynamic.py), which reuses the same runtime pipeline but exposes UI-selectable presets for:

- landmass style
- biome style
- world age
- temperature
- humidity
- sea level
- ocean connectivity
- river amount
- river length bias
- tributary density
- river network style

`Dynamic` no longer delegates its full world build to `Basic.generate()`. It now builds its raw hex world through [`sciv/system/generators/dynamic_worlds/mapgen.py`](../../sciv/system/generators/dynamic_worlds/mapgen.py), which reshapes the heightmap by landmass preset before hexgen finishes and then applies an extra biome-style moisture pass before tile conversion.

That Dynamic-specific raw builder now also performs additional world-shaping work that `Basic` does not:

- carves preset-driven channels and inland seas directly into the heightmap
- can optionally carve low-cost straits that connect all edge-touching ocean basins before rivers and geoforms are computed
- smooths those carved heightmaps and compresses the highest peaks per landmass profile so Dynamic maps avoid harsh seam lines and overly mountain-heavy interiors, with inland-heavy scripts tuned to spill excess peaks into hills more often before the shared mountain cutoff runs
- grows extra tributary river sources for stronger river networks on suitable landmasses
- adds bounded split/rejoin distributaries plus river-to-river connector branches so major rivers can braid or link up without the viewer/export path stalling on large searches
- lowers land along river systems into shallow valleys before terrain conversion
- pushes biome moisture more strongly by latitude belts, coastality, rivers, and rain shadow

In addition to parameter presets, `Dynamic` now uses its own starting-location heuristic after resources are allocated so different map scripts produce more reliable early-game starts.
That start heuristic now reuses the shared gameplay settlement scorer under [`sciv/gameplay/founding/`](../../sciv/gameplay/founding), which also powers settler-site recommendations outside the generator path.

## `Basic.generate()` pipeline

`Basic.generate()` is the current authoritative new-game generation pipeline, and `Dynamic` now reuses its shared conversion-prep helpers instead of keeping a second copy of the visible-area classification loop.

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

`Dynamic` now layers an extra script-aware coastline polish pass on top of the baseline sea-to-coast promotion. That pass currently lives in [`sciv/system/generators/dynamic_worlds/coastline.py`](../../sciv/system/generators/dynamic_worlds/coastline.py) and makes archipelago/fractal-style maps keep more shallow coastal water around islands, peninsulas, bays, and straits.

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

`Basic` still uses the shared baseline heuristic. `Dynamic` now overrides this phase with script-aware scoring that prefers stronger opening rings by weighing:

- first- and second-ring food and production
- coastal access, with stronger coastal preference on archipelago-style scripts
- river adjacency and nearby freshwater edges
- nearby resource density and expansion room
- reduced preference for mountain-choked or deep-water-fringed starts
- distance from the map edge, with a relaxed fallback pass if spacing is too strict

The shared scoring logic now lives outside the generator in [`sciv/gameplay/founding/site_scoring.py`](../../sciv/gameplay/founding/site_scoring.py). `Dynamic` provides its landmass- and biome-style-specific weighting through [`sciv/system/generators/dynamic_worlds/profiles.py`](../../sciv/system/generators/dynamic_worlds/profiles.py) rather than keeping that logic embedded directly in `dynamic.py`.

`Dynamic.generate()` now uses its own raw generation path instead of calling `Basic.generate()` directly. The current split is:

- [`sciv/system/generators/dynamic_worlds/mapgen.py`](../../sciv/system/generators/dynamic_worlds/mapgen.py) for Dynamic-specific heightmap shaping and biome-style moisture shaping
- [`sciv/system/generators/dynamic_worlds/landmasses.py`](../../sciv/system/generators/dynamic_worlds/landmasses.py) for landmass masks plus preset-driven channel and inland-sea carving
- [`sciv/system/generators/dynamic_worlds/rivers.py`](../../sciv/system/generators/dynamic_worlds/rivers.py) for tributary growth, bounded connector/distributary side channels, river naming, and river-valley shaping
- [`sciv/system/generators/dynamic_worlds/biomes.py`](../../sciv/system/generators/dynamic_worlds/biomes.py) for named biome regions and stronger biome-belt/rain-shadow moisture shaping
- shared `Basic` helpers for terrain classification, tile instantiation, terrain-model setup, resource allocation, and the common conversion boundary into gameplay tiles
- Dynamic-specific metadata and starting-unit logic layered after those shared conversion helpers

After that Dynamic-specific world build finishes, `Dynamic` also performs a metadata pass over the visible gameplay rectangle. That pass:

- names visible landmasses from the existing hexgen geoforms
- groups contiguous visible land tiles by biome into named biome regions
- names visible river systems from the generated river-source chains
- copies those labels onto the final gameplay `Tile` objects and records summary metadata in `world_generation_stats`

`world_generation_stats` for Dynamic worlds now also includes a `dynamic_generation` section that records the Dynamic-only shaping counts such as carved channels, inland seas, tributaries added, connector/distributary branches added, valley segments touched, and the average biome moisture delta applied during biome shaping.

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
- `Debug.dump_map_generation_data()` which now writes a richer gzipped raw-world export when debug dumping is enabled

The raw export path is now shared between the live runtime and an offline helper under [`sciv/system/generators/debug_export.py`](../../sciv/system/generators/debug_export.py).

By default, the export writes into the repo-local, gitignored folder `sciv/debugging/worldgen/`.

When triggered from the live game, the export currently includes:

- generator name, class path, seed, setup options, and sanitized map params
- requested runtime dimensions plus the full square raw hex-grid size
- the raw heightmap grid and sea-level summary
- every raw hex with biome, moisture, coast/inland flags, geoform id/type, territory id, neighbor coords, and river-segment membership
- geoforms, territories, river chains, and generated landmass/biome/river naming data
- the final runtime tile dump with terrain/resource flags plus copied Dynamic naming metadata when present
- any recorded `world_generation_stats` and legacy debug payload metadata

`OptionsScreen` now exposes a dedicated Developer-tab setting block for this export path under `debug.world_generation_export`, including:

- an enable toggle for runtime post-generation exports
- the export folder path
- the default offline batch count used by the standalone helper

Runtime export compatibility is intentionally loose: the old `debug.debugs.world_generation` flag still enables dumping when debug mode is on, but the richer export format and repo-local output folder are now the preferred path.

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

For offline iteration, [`scripts/export_worldgen.py`](../../scripts/export_worldgen.py) can generate the same raw export structure without launching the playable runtime. The helper currently supports:

- `CivLike` raw hexgen exports
- `Dynamic Worlds` raw exports with `--option key=value` overrides for preset fields such as `map_script`, `biome_style`, `world_age`, `temperature`, `humidity`, and `sea_level`
- batch generation with per-world exports plus a compressed batch manifest
- the same default repo-local export folder and offline batch-count setting used by the Developer-tab options surface

Those exports can now be inspected through the standalone [`scripts/worldgen_viewer.py`](../../scripts/worldgen_viewer.py) desktop tool. The viewer uses PyQt6, accepts either a single `.json` / `.json.gz` export or a batch manifest, renders the raw grid as SCiv's flat-top odd-q layout, and exposes overlay toggles for rivers plus landmass/biome/river labels. It also supports base-layer switches for biome, altitude, moisture, geoform, territory ownership, a dedicated river/hydrology overview, runtime terrain, runtime resources, and runtime visibility so raw-shaping changes can be reviewed without starting the full game runtime. The current viewer also reports per-layer overlay coverage percentages, lets that breakdown target either the runtime-visible rectangle or the full raw dump, highlights matching tiles on the map when the user hovers a compatible legend entry, exposes left-sidebar section toggles through the top-level `View` menu, keeps the left rail vertically scrollable instead of compressing every panel into the available height, and includes small inspector helpers for jumping to coordinates, centering or clearing the current selection, and copying the current inspector text. River mode now classifies tiles into headwaters, braids, connector branches, ordinary channels, confluences, mouths, and non-river land/water backgrounds while also keeping a stronger glow-backed river line overlay visible so hydrology is easier to read in both the dedicated overview and the normal map layers. Its overlay summary now reports river-chain and river-network counts, branch-category tile totals, and top named systems instead of only percentages, and the selected-hex inspector includes river role plus branch-type details. `scripts/worldgen_viewer.py` now stays as the stable compatibility entrypoint while the bulk of the implementation has started moving into the internal [`scripts/worldgen_viewer_tool/`](../../scripts/worldgen_viewer_tool/) package, which currently hosts the app entry, geometry helpers, palette helpers, and reusable viewer widgets.

The viewer is no longer limited to opening existing dumps. It can now drive the same offline generator registry used by the export helper directly inside the UI, with width, height, seed, a worlds-per-batch count, and generator-specific preset controls. The preview width and height spinboxes currently allow oversized offline runs up to `500 × 500` for debugging or inspection work, even though normal playable maps are expected to stay much smaller. For `Dynamic Worlds`, those shared controls now include hydrology tuning for river amount, river length bias, tributary density, river-network style, and optional forced main-ocean connectivity in addition to the existing landmass/climate presets. Preview generation now runs on a background Qt worker thread so the standalone UI stays responsive while a staged progress bar advances through the shared offline build/export steps, and the seed row includes an explicit randomize button next to the spinbox for quickly locking in a fresh seed before generating. Multi-world batches now fan out across several worker processes instead of generating strictly one after another, and when the requested batch count is greater than one the viewer opens a clickable comparison grid of generated worlds in the center pane. That grid now rescales its cards and thumbnails with the available window width so a normal full-width overview keeps a clean three-across presentation instead of leaving large unused gaps. Selecting a card loads that world into the normal detail view, a generated-world switcher at the top of the right-side inspector can jump directly between batch results, and a dedicated Back to overview action returns to the generated-world grid without rerunning the batch. That shared generation path now lives in [`scripts/worldgen_generation_support.py`](../../scripts/worldgen_generation_support.py), which centralizes the offline bootstrap, generator specs, option sanitization, payload building, and coarse progress reporting used by both tools.

That shared offline helper now also applies the visible-area terrain-classification and cleanup passes that the live generator performs before gameplay-tile instantiation. In practice that means offline previews and exports now populate `raw.hexes[*].terrain` with the same `Sea` / `Coast` / land-terrain labels the live conversion step would assign, including Dynamic's extra coastline polish where appropriate.

Those common conversion rules now live in [`sciv/system/generators/terrain_conversion.py`](../../sciv/system/generators/terrain_conversion.py), a pure-Python helper module that intentionally avoids Kivy, Panda3D, entity-registration, and other runtime-only dependencies. `Basic` delegates its terrain classification plus baseline cleanup passes there, and the standalone export/viewer path imports the same helpers directly so offline previews no longer maintain their own parallel copy of the conversion logic. `Dynamic` still layers its script-aware coastline polish on top of that shared baseline rather than replacing it.

After those cleanup passes finish, the standalone path now also synthesizes a visible-rectangle `runtime.tiles` dump from the post-conversion terrain state instead of leaving the viewer to infer runtime terrain from raw biomes alone. That gives the PyQt viewer finalized terrain keys, water/land/coast flags, and Dynamic naming metadata without having to boot Panda3D, entity registration, or live gameplay `Tile` objects just to inspect a preview.

The offline helper now also runs the shared [`ResourceAllocator`](../../sciv/system/generators/resource_allocator.py) over a lightweight visible-rectangle proxy grid that mirrors the live generator's terrain/resource compatibility checks closely enough for export and viewer inspection. In practice that means fresh offline exports now populate runtime resource keys in `runtime.tiles` and also copy those keys back onto the matching visible raw hexes for easier inspection and parity debugging in the viewer.

This synthesized runtime section still stops short of full live tile instantiation: starting-unit placement, render attachment, entity registration, and other post-instantiation work remain exclusive to the live in-game generation path.

The viewer UI now also keeps a dynamic legend in sync with the active base layer and exposes the primary file/generation/view actions through a top menu/toolbar instead of burying them only in the side panel. Its right-side hex inspector can now show terrain texture previews plus terrain/resource model thumbnails for the selected tile, so exported worlds can be inspected against the actual shipped assets instead of only text fields. That asset-preview path lives in [`scripts/worldgen_asset_preview_support.py`](../../scripts/worldgen_asset_preview_support.py): it source-parses gameplay terrain/resource class metadata to resolve texture, icon, model, and transform data without importing the heavy runtime classes, and then uses a small Panda3D offscreen render path for cached model thumbnails. Biome mode intentionally renders water with waterbody colors instead of the underlying raw climate biome because ocean hexes still carry climate metadata internally. The biome and runtime-terrain legends are now generated from the categories actually present in the loaded dump instead of a short fixed list, so terrain variants such as snow hills, tundra hills, pine forests, and other runtime subtypes appear in the legend when they are on the map. The standalone viewer/export support intentionally tolerates missing Kivy imports in the local environment so raw dump inspection and offline preview generation do not require the full runtime UI stack just to start.

## Observed current implementation notes

These describe the **current code path**, not necessarily the long-term design target.

- `GameSettings.__init__()` now respects the passed generator class and stores generator-specific setup options separately in `self.generator_options`.
- `Game.on_game_start()` now accepts generator metadata from `start_config`, so setup-screen selection decides which generator class `Game.generate_world()` instantiates.
- `GameConfigMenu` now preselects `Dynamic Worlds`, and the main-menu debug quick start now sends a minimal `start_config` payload that also defaults to `Dynamic Worlds`, so the richer generator path is used unless the player explicitly switches back to `Basic`.
- `GeneratorRepository` now loads concrete generators from `sciv/system/generators`, which is what powers setup-screen generator selection.
- `GeneratorRepository` now filters selector entries to concrete `BaseGenerator` subclasses, and the setup UI refreshes that cache when opening the generator picker so stale helper classes do not leak into the popup.
- The shared `PyLoad` discovery path used by `GeneratorRepository` now skips AST-discovered class names that are not present as runtime module attributes, so conditional fallback helpers inside generator modules do not break setup-screen generator selection.
- `Dynamic` is a separate preset-driven generator; it now uses its own Dynamic-specific raw map builder, changes hexgen parameter presets, reshapes the heightmap by landmass profile, smooths those preset-driven landmass cuts before final stats are derived, applies landmass-specific peak compression to keep mountain density playable without changing the shared hill/mountain thresholds, carves preset-driven channels and inland seas, applies a biome-style moisture pass with stronger latitude/rain-shadow shaping, can grow extra tributaries, bounded connector/distributary side channels, and river valleys, adds a script-aware coastline polish pass, applies named landmass/biome/river metadata, and overrides starting-unit placement with script-aware start scoring.
- `Dynamic.get_setup_fields()` now also exposes hydrology controls for river amount, river length bias, tributary density, river-network style, and optional forced main-ocean connectivity; `build_dynamic_map_params()` folds those into `num_rivers`, `river_source_spacing`, `river_source_min_distance`, `tributary_factor`, the bounded connector/distributary parameters that drive split/rejoin river behavior, and a raw-hexgen `force_connected_oceans` flag, so the same knobs are available in the new-game config UI and the standalone viewer/export path.
- When `force_connected_oceans` is enabled, `MapGen` now links separate edge-touching water basins with low-cost carved straits before river, territory, and geoform generation, so the final world keeps one connected main ocean instead of several disconnected edge seas.
- The same settlement scoring surface is now available to runtime settler recommendation code, so generator start placement and in-game city-site guidance can stay aligned.
- `MapGen` now injects its seeded RNG into `Heightmap`, so heightmap creation follows the same generation seed instead of using ambient module-level randomness.
- `MapGen._generate_rivers()` now supports both `river_source_spacing` and `river_source_min_distance`, which space the top drainage-picked river sources apart, bias the first source pass farther inland, and rank candidates by drainage plus distance-to-water before falling back to closer candidates when needed.
- `Basic` no longer forces `MapGen(..., debug=True)`; debug output follows the normal debug controls again.
- `Basic.build_map_params()` now delegates to a shared helper in [`sciv/system/generators/map_params.py`](../../sciv/system/generators/map_params.py), which keeps the offline exporter aligned with the live generator's raw-hex settings.
- `Basic` terrain classification plus the baseline water/coast/tundra cleanup rules now delegate to the pure helper module [`sciv/system/generators/terrain_conversion.py`](../../sciv/system/generators/terrain_conversion.py), which the offline export path also imports directly so live and standalone conversion stay aligned.
- The shared terrain-conversion helpers now intentionally accept indexed array-like raw grids such as the NumPy-backed `hex_grid.grid`, not just nested built-in sequences, so future typed helpers at that boundary should keep that broader contract.
- `Biome` and `GeoformType` still derive fields like `id` and `title` from `SuperEnum.__keys__`; keep explicit attribute annotations on those enum subclasses in sync with the declared keys so typed generator and debug-export code can access those fields directly.
- `Basic.map_params["size"]` is `max(width, height)`, so hexgen builds a square raw grid before `Basic` converts only the configured rectangular output area.
- `World.generator`, `Game.choose_generator()`, and `GeneratorRepository` exist, but the default new-game path ultimately instantiates `self.properties.generator(...)` in `Game.generate_world()`.
- Gameplay tiles still keep weak references to hexgen `Edge` objects after conversion.
- Dynamic world naming still runs on the final gameplay rectangle, but `Dynamic` no longer depends on `Basic.generate()` to create that raw world first; it now only reuses the later shared conversion/runtime helpers.

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