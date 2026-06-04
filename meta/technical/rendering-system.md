# Rendering System

> Back to [Documentation Index](../INDEX.md)
>
> Related: [Architecture](architecture.md) | [Asset System](asset-system.md) | [Tile System](tile-system.md) | [World Generation](world-generation.md) | [UI Runtime](ui-runtime.md)

This page documents the current world-rendering stack in SCiv: how the icon atlas is prepared, how terrain and tile-local presentation are split, how node tags feed input picking, and where shader-driven overlays live.

## Scope and boundaries

- This page covers the Panda3D-side world render stack, not Kivy screen layout.
- Detailed archive packaging, asset-manager caches, and atlas-cache lifecycle live in [Asset System](asset-system.md); this page focuses on render-time consumption.
- `Tile` remains the gameplay owner of terrain, occupancy, ownership, and yield state; renderers consume that state.
- Startup and screen flow live in [Startup Flow](startup.md) and [UI Runtime](ui-runtime.md).
- Generator-time terrain creation lives in [World Generation](world-generation.md); this page starts at the handoff into live render nodes.

## Ownership snapshot

| File | Responsibility |
| --- | --- |
| [`sciv/game.py`](../../sciv/game.py) | Builds the icon atlas during startup, initializes Panda3D/Kivy, and caches the live `ShowBase`. |
| [`sciv/managers/game.py`](../../sciv/managers/game.py) | Wires generator output into `TileModelGrid`, registers tiles with `TileRendererSystem`, and triggers `tile.render()`. |
| [`sciv/system/tile_grid.py`](../../sciv/system/tile_grid.py) | `TileModelGrid`: terrain model placement and grouped `RigidBodyCombiner` nodes. |
| [`sciv/system/renderers/tile_renderer.py`](../../sciv/system/renderers/tile_renderer.py) | `TileRenderer`: per-tile anchor node, model attachment, selector quad, click overlay, and world-space UI. |
| [`sciv/system/tile_renderer.py`](../../sciv/system/tile_renderer.py) | `TileRendererSystem`: instanced resource/yield/population icon overlay system. |
| [`sciv/system/renderers/landmass_label_overlay.py`](../../sciv/system/renderers/landmass_label_overlay.py) | `LandmassLabelOverlay`: zoom-gated continent/landmass name labels built from tile metadata after world render. |
| [`sciv/system/zoom_visibility.py`](../../sciv/system/zoom_visibility.py) | `ZoomVisibilityController`: reusable zoom-band visibility/fade controller for world-space overlays and future zoom-sensitive surfaces. |
| [`sciv/gameplay/unit.py`](../../sciv/gameplay/unit.py) | Active runtime unit rendering path: model load, selection ring, icon billboard, healthbar shader, hover indicator, and unit-side tags. |
| [`sciv/system/unit_renderer.py`](../../sciv/system/unit_renderer.py) | Alternate standalone unit renderer class present in the repo but not currently referenced by the main unit lifecycle. |
| [`sciv/system/renderers/bits_renderer.py`](../../sciv/system/renderers/bits_renderer.py) | Deterministic slotting of terrain, resource, improvement, and city bits into tile-local model slots. |
| [`sciv/system/atlas.py`](../../sciv/system/atlas.py) | Atlas generation, mapping lookup, and Panda3D/Kivy texture extraction for icon assets. |
| [`sciv/system/shaders.py`](../../sciv/system/shaders.py) | Simple shader cache used by border and other systems that want named shader reuse. |
| [`sciv/gameplay/border.py`](../../sciv/gameplay/border.py) | Border and hex-border shader overlays for territory visuals. |
| [`sciv/managers/input.py`](../../sciv/managers/input.py) | Camera-attached picking ray that resolves tagged render nodes back to tiles and units. |

## End-to-end flow

```mermaid
flowchart TD
    Startup[OpenCiv startup] --> Atlas[AtlasGenerator cached in Cache]
    Startup --> Archive[P3DAssetArchive cached in Cache]
    Generate[Game start or load] --> Grid[TileModelGrid attached to render]
    Generate --> Register[TileRendererSystem.register_tiles()]
    Register --> TileRender[Tile.render() per tile]
    TileRender --> Terrain[terrain model instance]
    TileRender --> Bits[BitsRenderer models]
    TileRender --> Overlay[TileRendererSystem instanced icons]
    TileRender --> UI[world-space city bars/nameplates/selectors]
    Terrain --> Input[Input raycaster]
    Bits --> Input
    UI --> Input
```

## Startup-owned rendering prerequisites

### Atlas and asset archive bootstrap

`OpenCiv.generate_non_static_assets()` builds or loads an `AtlasGenerator` over `assets.mf`, then stores it in `Cache.set_icon_atlas()`.

That atlas is later used by:

- `TileRendererSystem` for instanced tile icons
- `TileRenderer` for city bars and action icons
- Kivy-side UI that needs the same icon lookup surface

Separately, `Game.__init__()` mounts `assets.mf` through `P3DAssetArchive.mount_only()` and stores the archive in `Cache.set_asset_archive()`. Renderers then load models, images, fonts, and some shaders from that archive-backed surface.

## Default material path vs explicit shaders

### World models use the default Panda3D/simplepbr path unless code opts out

`OpenCiv.__init__()` calls `simplepbr.init()` during startup. In the current runtime, that is the default material/shading path for most loaded 3D models.

That means:

- terrain models created by `TileModelGrid`
- unit models loaded by `Unit.load_model()`
- bit and improvement models attached by `TileRenderer.add_model()`

all normally render using their model-authored textures/materials plus Panda3D's standard model pipeline, rather than a bespoke SCiv terrain shader.

The main exceptions are places that explicitly change render state:

- `TileRenderer.add_model()` can call `setLightOff()` and/or `setShaderOff()` when a bit asks for non-default behavior
- border, selection, icon, healthbar, hover, and targeting overlays attach custom GLSL shaders directly to specific nodes

### The terrain-atlas shader path exists but is not wired into the live terrain layer

The repository contains:

- `assets/shaders/terrain.vert.glsl`
- `assets/shaders/terrain.frag.glsl`
- `Cache.set_terrain_atlas()` / `Cache.get_terrain_atlas()`

Those shader files expect a `terrain_atlas` sampler and a `uv_index` selector, but the current runtime does not bind those uniforms onto `TileModelGrid` instances or otherwise attach these shaders to the terrain nodes.

So the current terrain rendering contract is:

- live terrain visuals come from model assets loaded per terrain type
- not from a custom atlas-driven terrain shader path

Treat the terrain-atlas shader pair as a dormant or experimental surface unless a future change explicitly wires it into the terrain layer.

## Terrain layer: `TileModelGrid`

Despite the name, `TileModelGrid` is not a single handcrafted terrain mesh. It instantiates one terrain model per tile and groups instances by terrain key under `RigidBodyCombiner` nodes.

The main steps are:

1. extract terrain model path, scale, hpr, and z offset from each tile's terrain
2. cache a prototype `NodePath` per model path
3. copy the prototype into an `rbc_<terrain-key>` node
4. position the instance from odd-q world spacing plus altitude-derived z
5. call `collect()` on each combiner

`Basic.generate()` builds this grid for new games and attaches it to render immediately. `Game.load()` rebuilds a fresh grid from saved tiles.

`update_tile()` removes and recreates one tile's terrain instance, then recollects the combined nodes. `TileRenderer.rerender_terrain()` uses that path when terrain changes at runtime.

Because `TileModelGrid` only places normal model instances, terrain materials currently come from the loaded model asset itself. No per-tile terrain shader inputs are set in this layer.

## Active unit rendering path

The current gameplay runtime renders units primarily through methods on `Unit` in [`sciv/gameplay/unit.py`](../../sciv/gameplay/unit.py), not through `sciv/system/unit_renderer.py`.

The main lifecycle is:

1. `Unit.spawn()` registers actions and the entity if needed
2. `calculate_model_position()` copies tile-space position into the unit's cached world position
3. `load_model()` loads the unit model, parents it to `base.render`, and applies rotation/scale/collision tags
4. optional overlays are attached to that model: icon card, healthbar, selection ring, and hover indicator

### Unit model placement and base state

`Unit.load_model()` currently:

- resolves the model from `self._model`
- loads it through `base.loader.loadModel(...)`
- reparents it directly to `base.render`
- calls `flatten_strong()` on the loaded model
- places it at the tile altitude from `tile.calculate_z_pos_on_altitude()`
- applies `model_rotation`, `model_size`, and collide mask bit `1`
- tags the node as `NET_TYPE.UNIT` with `NET_NODE_TAG_ID_FIELD = unit.tag`

This is the authoritative picking surface for units in the main runtime.

### Unit icon billboard and healthbar

When a unit has an `icon`, `Unit.load_model()` attaches a card node under the model and uses three shader-backed layers:

- `unit_icon.vert` / `unit_icon.frag` for the icon card itself
- `unit_healthbar.vert.glsl` / `unit_healthbar.frag.glsl` for the healthbar quad attached beneath that card
- color/alpha blending and fixed-bin ordering to keep these overlays visible above the model

The icon card uses the unit's tight bounds to place itself above the model, then stores the icon texture as `iconTex`.

The healthbar shader is driven mainly by:

- `health_ratio`
- `border`
- `color`

`receive_damage()` and `heal()` update `health_ratio` on the cached healthbar quad rather than rebuilding the node tree.

### Selection ring and hover state

`Unit.select()` creates a ring from `LineSegs`, attaches it to the model, shows it, and starts a rotation task. `deselect()` hides it and stops the task.

There is an important current-code nuance here:

- `Unit` loads `unit_selection.vert.glsl` and `unit_selection.frag.glsl`
- the selection-circle path in `sciv/gameplay/unit.py` sets shader inputs on the circle node
- but it does **not** currently call `setShader(self.selection_shader)` on that node

By contrast, the alternate `sciv/system/unit_renderer.py` implementation does explicitly bind the selection shader. So the active gameplay-unit path and the standalone renderer class are not identical.

Hover state is separate again: `Unit.hover()` adds a `HoverIndicator` to the unit model, and `Unit.unhover()` removes it.

### Movement, destruction, and rebuild behavior

Unit render nodes are rebuilt from gameplay state rather than serialized directly.

- movement calls `_move_to_tile()`, updates the tile relationship, reloads the model when needed, and recalculates placement
- `load_state()` restores references and shader objects, then defers model recreation until the unit is actually spawned/loaded
- `destroy()` unloads the model, removes the unit from tile/player/manager collections, and emits the appropriate gameplay or system signal

## Standalone `UnitRenderer` status

`sciv/system/unit_renderer.py` is indexed and still useful as a reference surface, but there are no current call sites creating `UnitRenderer` instances in the runtime path.

That class differs from the active `Unit`-owned rendering flow in a few ways:

- it keeps its own cached model copy path
- it explicitly binds the unit selection shader to a selector quad or selection circle
- it lives in `sciv/system/`, while the active path is embedded in the gameplay `Unit` entity itself

When documenting or changing the live game behavior, prefer `sciv/gameplay/unit.py` first and treat `sciv/system/unit_renderer.py` as an alternate or incomplete path unless runtime wiring changes.

## Tile-local layer: `TileRenderer`

Each gameplay tile owns one `TileRenderer`. The renderer creates a small node tree rooted under chunked world nodes:

- `world_root`
- `chunk_<cx>_<cy>`
- `tile_<x>_<y>_anchor`
- `geometry_group`
- optional `ui_group`

`TileRenderer` uses `CHUNK_SIZE_X = 32` and `CHUNK_SIZE_Y = 32` to partition tile anchors into chunk roots, which keeps the world node tree more organized than one giant flat list.

The renderer owns several node types:

- a hidden click overlay card for reliable tile picking
- a shader-driven selector quad for selection state
- attached model instances for bits and other tile-local models
- optional city UI nodes such as health bars, population bars, build bars, action icons, and city nameplates

`render()` is the main sync point. It repositions the anchor, clears and redraws UI, syncs the instanced icon overlay, optionally requests a terrain rerender, and then lets `BitsRenderer` place tile-local models.

## Zoom-gated world labels

`LandmassLabelOverlay` adds layered, lightly transparent world-space labels for named regions once the camera is zoomed far enough out.

Important traits of this layer:

- rebuilds from live `World.grid` tile metadata after `Game.render_field()` finishes tile rendering
- carries separate zoom bands for territory labels and broader landmass labels so the map can crossfade between regional and continental naming layers
- groups tiles by runtime metadata such as `territory_id` / `territory_name` and `landmass_name`, filters to larger named regions, and chooses a label anchor from either the recorded territory seed tile or the tile nearest the group's centroid
- renders billboarded `TextNode` labels in a late fixed bin with depth testing disabled so names stay readable above terrain
- fades through the generic `ZoomVisibilityController` instead of hard-coding label-specific zoom polling

The current runtime uses this for named territories at closer zoomed-out views and for named landmasses such as continents and larger islands farther out. The same zoom-visibility controller is intended to be reused later for city-detail overlays, zoom-sensitive tactical surfaces, or similar world-space presentation layers.

## Bits and slot assignment

`BitsRenderer` handles terrain bits, resource bits, improvement bits, and city-improvement bits.

Its slotting rules are part of the active render contract:

- slots come from `tile.get_prop_slots()` and switch between `default_slots` and `city_slots`
- preferred slots win when available
- previous slot assignments are remembered per bit id for stability
- deterministic fallback slot order is derived from CRC32 of the bit id
- `DisplayMode` flags can hide bits on units, resources, selection, or resource improvements
- `RESOURCE_IMPROVEMENT` blockers can suppress non-blocking bits and resource-model presentation

Bits are rendered as normal model instances through `TileRenderer.add_model()`. They are not part of the instanced icon overlay system.

## Instanced icon overlay: `TileRendererSystem`

`TileRendererSystem` is a singleton node under `base.render` dedicated to tile-top icon overlays.

Important traits of this system:

- uses its own `tile_renderer_system` node with transparency enabled
- disables collisions, depth write, and depth test
- renders in a fixed bin above most terrain content
- uses `tile_icons_instanced.vert.glsl` and `tile_icons_instanced.frag.glsl`
- stores one instance row per tile containing `i_pos_scale` plus seven UV rectangles

The first slot is either the city population icon or the tile's primary resource. The remaining slots come from `base_yields.export_basic()` and represent yield icons.

Because the system is instance-driven, hiding everything does not remove nodes; it clears per-instance rows instead.

## Shader-driven overlays and specials

Several world-space visuals are handled separately from terrain instances:

- tile selection uses `tile_selector.vert.glsl` and `tile_selector.frag.glsl`
- unit selection, unit icon cards, and unit healthbars use the `unit_selection`, `unit_icon`, and `unit_healthbar` shader sets
- borders use `border.vert` with `border_ring.frag`, plus `hex_border.vert` and `hex_border.frag`
- hover indicators and ranged-targeting visuals are separate overlay systems rooted in gameplay helpers rather than the tile terrain grid

`game.border.refresh` is the main border-refresh message after ownership or city changes.

## Picking contract: node tags and collide masks

The input raycaster depends on a stable tagging contract between renderers and `Input`.

Tile-facing nodes typically set:

- `NET_TYPE_FIELD`
- `NET_NODE_TAG_ID_FIELD`
- collide mask bit `1`

Important current conventions:

- `TileRenderer` tags the anchor, geometry node, click overlay, and selector as tile or geom nodes
- `BitsRenderer` tags model instances as `BIT`
- `Unit.load_model()` tags the unit model as `UNIT`
- `Input.pick_object()` treats `TILE`, `BIT`, and `GEOM` as tile-resolvable targets
- `Input.pick_object()` treats `UNIT` (and legacy/model-oriented paths) as unit-resolvable targets
- for `BIT`, tile coordinates are parsed from the net id prefix; for `TILE` and `GEOM`, they are parsed from the trailing `tile_<x>_<y>` tag

This contract is why tile render nodes and tile tags must stay boringly predictable.

## Save/load and rebuild behavior

Render nodes themselves are not persisted.

Instead, the runtime rebuilds them from gameplay state:

- startup rebuilds or loads the atlas cache
- new-game generation builds `TileModelGrid`
- save/load rebuilds `TileModelGrid` from restored tiles
- `Tile.load_state()` recreates `TileRenderer` and restores only renderer memory such as bit-slot state

## Current implementation notes

- `TileLayers` currently exists as a placeholder and is not an active layer-management system.
- `Game` currently keeps both `tile_hex_grid` and `world_tile_grid`; new-game terrain rerenders use `world_tile_grid`, while save/load rebuilds `tile_hex_grid` directly.
- `TileModelGrid` uses grouped `RigidBodyCombiner` nodes, not GPU instancing.
- The authoritative live unit-render path is in `sciv/gameplay/unit.py`; `sciv/system/unit_renderer.py` is currently unreferenced by the main runtime flow.
- `LandmassLabelOverlay` is rebuilt as a post-render overlay from tile metadata and currently depends on generators that populate `territory_id` / `territory_name` / `territory_size` plus `landmass_name` / `landmass_type` / `landmass_size` onto runtime tiles.
- `ZoomVisibilityController` is the shared zoom-band fade mechanism for world-space overlays; future zoom-sensitive layers should prefer it over bespoke per-feature thresholds.
- `assets/shaders/terrain.vert.glsl` and `terrain.frag.glsl`, plus `Cache._terrain_atlas`, are present but not currently wired into live terrain rendering.
- `Game.render_field()` calls `tile.render()` for all tiles and then runs `SceneOptimizer.flatten_scene(self.base.render)`, so later dynamic attachments should be treated as post-flatten runtime nodes.