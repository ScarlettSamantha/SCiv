# Tile System

> Back to [Documentation Index](../INDEX.md)
>
> Related: [Architecture](architecture.md) | [World System](world-system.md) | [World Generation](world-generation.md) | [Rendering System](rendering-system.md) | [Entities and Save/Load](entities.md)

This page documents the current gameplay tile system: where runtime tiles come from, what state a `Tile` owns, which managers and repositories are authoritative, and how tile state fans out into rendering, ownership, pathing, and persistence.

## Scope and boundaries

- This page is about gameplay `Tile` entities after world generation or save/load restoration.
- The world-container responsibilities that own `World.map`, `World.grid`, and ownership transfer live in [World System](world-system.md).
- Raw hexgen `Hex` objects are generator-time structures; once `Basic.instantiate_tiles()` finishes, `Tile` is the long-lived runtime object.
- Terrain meshes, icon overlays, selectors, borders, and world-space tile UI are documented in [Rendering System](rendering-system.md).
- Save/load mechanics for entities more broadly live in [Entities and Save/Load](entities.md).

## Ownership snapshot

| File | Responsibility |
| --- | --- |
| [`sciv/gameplay/tile.py`](../../sciv/gameplay/tile.py) | Core `Tile` entity: coordinates, terrain, flags, ownership, units/resources/improvements, yield calculation, selection hooks, and save/load handoff. |
| [`sciv/managers/world.py`](../../sciv/managers/world.py) | Authoritative world container for `map`, `grid`, tile ownership transfer, and world-level turn fan-out. |
| [`sciv/gameplay/repositories/tile.py`](../../sciv/gameplay/repositories/tile.py) | Lookup, neighbors, radius queries, distance helpers, and pathfinding over the tile grid. |
| [`sciv/gameplay/terrain/**`](../../sciv/gameplay/terrain) | Terrain-specific movement, yields, render model choice, and terrain bits. |
| [`sciv/gameplay/tile_slots.py`](../../sciv/gameplay/tile_slots.py) | Slot layouts used by tile bits and per-tile prop placement. |

## Lifecycle at a glance

```mermaid
flowchart TD
    Hexgen[hexgen Hex] --> Instantiate[Basic.instantiate_tiles()]
    Instantiate --> TileInit[Tile.__post_init__()]
    TileInit --> Register[EntityManager register Tile]
    Register --> WorldGrid[World.map / World.grid]
    WorldGrid --> Repo[TileRepository.grid]
    TileInit --> RenderHook[TileRenderer created]
    WorldGrid --> Turn[World.on_turn_end()]
    WorldGrid --> Save[Tile.dump()/__getstate__()]
    Save --> Load[Tile.load_state()]
```

## What a `Tile` owns

A live `Tile` combines grid identity, environment data, gameplay contents, and runtime hooks.

### Spatial identity

`Tile` keeps both grid-space and render-space coordinates:

- `x`, `y` — odd-q style hex-grid coordinates
- `pos_x`, `pos_y`, `pos_z` — world-space placement used by renderers
- `tag` — stable `tile_<x>_<y>` identity used by input picking and persistence
- `hpr` and `z_scale` — orientation and height helpers used by terrain placement

`compute_hex_center()` and `recalculate_grid_position()` derive world-space xy from grid coordinates, while `calculate_z_pos_on_altitude()` converts altitude into render z.

For alternate world views such as the minimap, this mapping is the contract to mirror exactly. Do not assume that raw grid rows or columns map directly to intuitive screen north/south placement; use the derived world-space coordinates and keep any normalization/cropping math aligned with them.

### Environment and terrain state

Each tile stores the worldgen-derived environment that gameplay uses later:

- `tile_terrain`
- `altitude`, `temperature`, `moisture`
- `biome`, `geoforms`, `features`
- `is_water`, `is_land`, `is_sea`, `is_lake`, `is_coast`, `is_inland_sea`
- `edges` pointing at hexgen `Edge` objects via weak references

When `Dynamic Worlds` is the active generator, tiles may also carry extra world-label metadata added after the shared generation pipeline finishes, such as:

- `landmass_name`, `landmass_type`, `landmass_size`
- `biome_region_name`, `biome_region_type`, `biome_region_size`
- `river_names`, `primary_river_name`, `river_count`

`tile_terrain` also controls default passability, movement cost modifiers, yields, terrain bits, and the terrain model path used by the renderer stack.

### Gameplay contents and ownership

A tile owns or references its local gameplay contents:

- `resources`
- `units`
- `_improvements`
- `effects`
- `owner`
- `city`
- `city_owner`

`calculate()` aggregates tile yield from terrain, city state, improvements, effects, and resources into `tile_yield`.

## From generator output to live tiles

`Basic.instantiate_tiles()` is the main new-game handoff from hexgen to gameplay tiles.

1. pick a gameplay tile class from `gameplay/tiles`
2. instantiate `Tile(x, y, render_x, render_y)`
3. call `enrich_from_extra_data()` to copy altitude, biome, moisture, water flags, features, geoforms, resources, and edges
4. set `pos_z` from altitude
5. store the tile in `World.map` and `World.grid`

`Tile.__post_init__()` then creates the tile-local `Effects`, creates a `TileRenderer`, and registers the tile with `EntityManager`.

`Dynamic Worlds` now keeps that shared `Basic.instantiate_tiles()` handoff intact and applies its optional naming metadata afterward by walking the finished `World.grid`. That keeps the baseline generator boundary stable while still letting Dynamic-specific map labels live on runtime tiles.

After that point, the authoritative runtime collections are:

- `World.map`
- `World.grid`
- `TileRepository.grid`

## Ownership, cities, and occupancy

### Ownership changes flow through `World`

`World.set_ownership_of_tile()` is the authoritative ownership transfer path. It:

- removes the tile from the old owner's tile set if needed
- clears or rewires city ownership references
- assigns the new player and city owner
- updates player-owned collections
- emits `game.gameplay.tiles.ownership_changed`

### Founding a city mutates tile role

`Tile.found()` turns a regular tile into a city tile by:

- founding a `City`
- assigning tile and player ownership
- storing the player's capital reference when applicable
- calling `become_city()`
- recalculating yields
- rerendering terrain
- sending `game.border.refresh`

`become_city()` swaps terrain to the city terrain class and changes the available prop slots from `default_slots` to `city_slots`.

### Units and improvements stay tile-local

`add_unit()` and `remove_unit()` update the local `Units` collection and notify the renderer when the tile becomes occupied or empty.

`build()` validates improvement placement, constructs the improvement, wires it into resources/improvements/terrain state, and rerenders the tile.

## Pathing and tile lookup

`TileRepository` is the main query layer on top of `World.grid`.

It provides:

- `get_tile()` and search helpers
- direct-neighbor and radius queries
- cached neighborhood expansion
- distance helpers (`hex`, `euclidean`, `manhattan`, `chebyshev`)
- pathfinding (`astar`, `dijkstra`, `theta_star`, bidirectional Dijkstra)
- conversion helpers such as `hex_to_world()` and `tile_list_to_vec3()`

In practice, gameplay and input code usually resolve tiles through tags -> coordinates -> `TileRepository.get_tile()`.

## Tile-to-render handoff

`Tile` does not render terrain meshes directly. Its responsibility is to tell the render stack when state changed.

The main hooks are:

- `render()` — recompute yields if requested, then delegate to `renderer.render()`
- `set_terrain()` — swap terrain and request terrain rerender
- `select()` / `deselect()` — toggle tile selection and selector visuals
- `disable_icons()` / `enable_icons()` — toggle instanced yield/resource icon overlays

The concrete Panda3D node layout lives in [Rendering System](rendering-system.md).

## Save/load boundary

`Tile.dump()` and `__getstate__()` serialize the gameplay-facing tile state plus enough renderer memory to rebuild local presentation.

Saved data includes:

- terrain dump
- water/land flags
- resources, units, improvements, and effects
- owner/city references by tag
- rounded coordinates and rotation
- renderer memory from `TileRenderer.dump()`

On load, `Tile.load_state()` reconstructs terrain, resources, improvements, effects, and units, then recreates `TileRenderer` before restoring its saved renderer memory.

## Current implementation notes

- `Tile.is_alive()` always returns `True`; tiles are treated as permanent world entities until explicit world reset or destruction.
- `World.on_turn_end()` only calls `tile.on_turn_end()` for tiles that are interesting enough to process: owned, occupied, improved, effected, city-backed, or marked with `needs_tile_proecessing`.
- The `needs_tile_proecessing` field name is misspelled in current code and is part of the active runtime contract.
- Tiles keep weak references to hexgen `Edge` objects after generation; those edges are worldgen artifacts, not `EntityManager` entities.
- `Tile.dump()` and `__getstate__()` both start from `self.__dict__.copy()`, so generator-attached runtime metadata such as Dynamic world labels persists automatically unless a later change explicitly strips it.