# Vision and Fog of War

> Back to [Documentation Index](../INDEX.md)
>
> Related: [Player System](player-system.md) | [World System](world-system.md) | [Tile System](tile-system.md) | [Effects](effects.md) | [Turn Processing](turns.md) | [Signals](signals.md)

This page documents SCiv's gameplay-owned vision model and the current fog-of-war runtime. It covers who emits vision, how player vision is recomputed, how lingering visibility works, and how the main map consumes that state today.

## Scope and current milestone

The current implementation establishes the **gameplay-side source of truth** for vision and fog state and now applies an initial render-side consumer for the session player.

It includes:

- entity-owned vision emitters
- player-owned aggregated vision state
- lingering visibility after line-of-sight is lost
- effect hooks for range and linger-turn modifiers
- save/load support for explored and fogged tile records
- world-level refresh hooks and a dedicated vision-updated signal
- player-scoped reveal-source plumbing for future gameplay or event-driven terrain reveals

It currently applies these render-side behaviors for the session player:

- `visible` and `lingering` tiles render normally
- `fogged` tiles hide their underlying terrain instance and replace it with a height-aware hex fog volume while tile-local bits, tile-top icons, and units are hidden
- `unseen` tiles hide their underlying terrain instance and replace it with a darker height-aware fog volume
- landmass and territory labels stay hidden until the whole map has been explored, so they do not leak unseen geography

It still does **not** implement line-of-sight occlusion or separate explored-terrain interaction rules.

## Ownership snapshot

| File | Responsibility |
| --- | --- |
| [`sciv/gameplay/vision.py`](../../sciv/gameplay/vision.py) | Pure helper functions plus the persistent `Vision` tile-state index. |
| [`sciv/gameplay/player.py`](../../sciv/gameplay/player.py) | Owns aggregated player vision, save/load state, and empire-level linger settings. |
| [`sciv/gameplay/unit.py`](../../sciv/gameplay/unit.py) | Unit-side vision emitters with a default radius of 2 hexes. |
| [`sciv/gameplay/city.py`](../../sciv/gameplay/city.py) | City-side vision emitters based on owned territory plus extra border rings. |
| [`sciv/managers/world.py`](../../sciv/managers/world.py) | Recomputes player vision during world-stage turn work and on runtime events. |
| [`sciv/gameplay/effect.py`](../../sciv/gameplay/effect.py) and [`sciv/system/effects.py`](../../sciv/system/effects.py) | Vision modifier hooks for persistent effects. |
| [`sciv/managers/game.py`](../../sciv/managers/game.py) | Delegates startup/load-time visibility bootstrap to the world manager and forwards `game.gameplay.vision.updated` into the active render consumer. |
| [`sciv/system/renderers/fog_of_war.py`](../../sciv/system/renderers/fog_of_war.py) | Session-player fog controller that maps vision states onto terrain instances, tile overlays, instanced icons, units, and landmass labels. |

## Mental model

Vision is tracked in three layers:

1. **Emitters** decide which tiles an entity can currently see.
2. **Players** aggregate visible tiles from all of their emitters.
3. **Vision records** remember current visibility, lingering turns, and explored fogged tiles.

That means fog is **not** derived from render state. It is a gameplay-owned index that rendering, AI, and UI systems can consume.

## Tile states

Each player-owned `Vision` instance stores tile records keyed by tile tag.

| State | Meaning |
| --- | --- |
| `unseen` | The player has never seen the tile. |
| `visible` | The tile is currently in range of at least one emitter. |
| `lingering` | The tile just fell out of range but remains visible for a limited number of turns. |
| `fogged` | The tile has been explored before but is no longer currently visible. |

Lingering visibility currently defaults to **2 turns** after vision is lost.

## Emitters

### Units

Units emit vision in a circular-radius neighborhood using [`TileRepository.get_neighbors()`](../../sciv/gameplay/repositories/tile.py).

Current defaults:

- base unit vision radius = `2`
- final unit vision radius = base radius + unit effect bonuses + player effect bonuses
- effect overrides can replace the base/final value before bonuses are added

### Cities

Cities emit vision from their controlled footprint outward.

Current defaults:

- base city vision = owned territory footprint + `1` extra hex ring
- the city center tile is always included even if `owned_tiles` has not been fully backfilled yet
- city and player effects can add bonuses or overrides just like units

## Recompute flow

The authoritative refresh path lives in [`World.refresh_player_vision()`](../../sciv/managers/world.py).

That method:

1. asks the player for its linger duration
2. updates the player's `Vision.default_linger_turns`
3. collects all visible tiles from the player's cities and units
4. recomputes tile records
5. emits `game.gameplay.vision.updated`

`World.refresh_all_player_vision()` applies the same process to every normal and mechanic player.

## Runtime refresh triggers

The world manager now refreshes vision when these events occur:

- world-stage turn processing begins
- a unit is spawned
- a unit finishes moving
- a unit is destroyed
- a city is founded
- tile ownership changes

The world manager also now exposes player-scoped reveal-source plumbing for future gameplay systems through:

- `game.gameplay.vision.request_reveal_tiles`
- `game.gameplay.vision.request_clear_reveal_tiles`

Those signals let future effects, scripted events, or other mechanics register and clear named reveal sources for a player without bypassing the normal `Vision` source of truth.

The post-move refresh uses `game.gameplay.unit.moved` rather than the older pre-move visit signal so vision reflects the unit's real final position.

## Save/load behavior

`Player.dump()` serializes the full `Vision` payload.

The current format stores:

- `linger_turns`
- a list of per-tile records containing `tile_tag`, `state`, and `turns_remaining`

`Vision.load_state()` remains backward-compatible with the older list-only format that treated saved tiles as currently visible.

## Effect hooks

The effect system now exposes three no-op query hooks on base `Effect`:

- `get_vision_range_bonus()`
- `get_vision_range_override()`
- `get_vision_linger_turns_bonus()`

`Effects` containers aggregate those hooks so unit, city, and player logic can ask for final modifiers without knowing which concrete effects are attached.

## Signals

The gameplay-side visibility flow currently uses these signals:

- `game.gameplay.unit.spawned`
- `game.gameplay.unit.moved`
- `game.gameplay.unit.destroyed`
- `system.unit.destroyed`
- `game.gameplay.city.founded`
- `game.gameplay.tiles.ownership_changed`
- `game.gameplay.vision.updated`
- `game.gameplay.vision.request_reveal_tiles`
- `game.gameplay.vision.request_clear_reveal_tiles`

Render and UI work should subscribe to `game.gameplay.vision.updated` rather than recomputing visibility themselves.

## Current render contract

The current map-side fog consumer follows this contract:

- use the session player's `Vision` state as the only visibility source
- treat `lingering` the same as `visible` for rendering
- hide units unless their current tile is visible
- hide tile-top icons unless their tile is currently visible
- hide tile-local bits and city UI on `fogged` and `unseen` tiles
- replace both `fogged` and `unseen` terrain with fog volumes that extend from the tile surface toward a shared world fog ceiling, using a lighter color for `fogged` tiles and a darker one for `unseen` tiles

Future render work should extend that contract instead of bypassing it with ad-hoc unit or tile queries.

## Implementation notes

- AI target/threat scans now use each unit's actual gameplay vision radius instead of a stale hardcoded value.
- The new gameplay layer is ready for effect-based vision traits without requiring emitter-specific branching.
- City visibility intentionally includes the city tile itself so freshly founded cities have sight even before all ownership bookkeeping settles.
- The current render consumer lives on the game/render side rather than inside `Vision` itself: gameplay owns the truth, while `FogOfWarController` applies that truth to terrain, tile overlays, units, and map labels.
- Runtime reveal sources are stored on `Vision` as a player-scoped union of named tile-tag sets. The world manager merges those tags into the normal unit/city emitter result before recomputing visibility.
