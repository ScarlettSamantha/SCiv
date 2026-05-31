# City Production and Growth

> Back to [Documentation Index](../INDEX.md)
>
> Related: [Mechanics Overview](workings.md) | [Turn Processing](turns.md) | [Signals](signals.md) | [Effects](effects.md)

This document explains how cities process food, production, border growth, and city-owned improvements in the current SCiv implementation.

## Core files

| File | Responsibility |
| --- | --- |
| [`sciv/gameplay/city.py`](../../sciv/gameplay/city.py) | City state, turn processing, production, border growth, and persistence. |
| [`sciv/menus/kivy/parts/city.py`](../../sciv/menus/kivy/parts/city.py) | UI-side city interaction and city production requests. |
| [`sciv/managers/world.py`](../../sciv/managers/world.py) | Handles city tile-ownership requests triggered by border growth. |

## Mental model

The current city system is built around a **single active build slot**, not a full production queue.

A city is responsible for:

- owning and exploiting nearby tiles
- processing food and population changes
- collecting production toward one active build
- growing borders through culture
- contributing non-food yields back to the player

## Important city state

Key production-related fields in [`sciv/gameplay/city.py`](../../sciv/gameplay/city.py) include:

- `is_building`
- `building`
- `resource_required`
- `resource_required_amount`
- `resource_collected`

Growth-related fields include:

- `population`
- `food_collected`
- `new_population_food_required`
- `population_food_usage`

Border-growth fields include:

- `border_growth_points`
- `border_growth_cost`
- `border_growth_next_tile`

## Request and start flow

The city registers tagged handlers such as:

- `game.gameplay.city.request_start_building_improvement_{city.tag}`
- `game.gameplay.city.request_start_building_unit_{city.tag}`
- `game.gameplay.city.request_cancel_building_improvement_{city.tag}`

When the city accepts a build request, it records the current build target and resets production state.

### Improvement start

`on_request_start_building_improvement()` sets:

- `is_building = True`
- required resource type
- required amount
- collected amount reset to zero
- `building` set to the requested improvement

It then emits `game.gameplay.city.starts_building_improvement`.

### Unit start

`on_request_start_building_unit()` follows the same pattern, then emits `game.gameplay.city.starts_building_unit`.

## Per-turn city flow

`City.on_turn_end(turn)` currently processes city state in this order:

1. city effects
2. tile yield calculation
3. food handling
4. production handling if a build is active
5. player contribution handling
6. border growth
7. tile renderer update

This ordering matters because effects are processed before yields are used.

## Production flow

### Yield source

`calculate_yield_from_tiles()` combines:

- yields from all owned tiles
- yield bonuses from city improvements
- yield bonuses from improvement effects
- maintenance costs from improvements and improvement effects

So the city's production pool is not just tile production; it already includes improvement-side modifiers and maintenance subtraction.

### Collecting production

During `_process_production()`:

1. production is extracted from the current turn's yield
2. production is added to `resource_collected`
3. if enough has been collected, the active build finishes

### Finishing an improvement

If the active build is a `BaseCityImprovement`, the city:

- assigns owner and tile
- resets build state
- registers/adds the improvement to the city
- emits `game.gameplay.city.finish_building_improvement`

### Finishing a unit

If the active build is a unit, the city:

- tries to spawn it on the city tile if possible
- otherwise searches nearby tiles in radii `1..4`
- requires a tile that is unoccupied, passable, and non-water
- calls `spawn_on(...)`
- refreshes rendering
- emits `game.gameplay.city.finish_building_unit`

This means unit completion is coupled to map availability, not just resource accumulation.

## Food and population flow

Food is processed separately from generic production.

### Surplus calculation

`calculate_food_surplus()` computes:

$$\text{food surplus} = \text{owned tile food yield} - (\text{population food usage} \times \text{population})$$

### Population growth

If positive food plus stored food reaches `new_population_food_required`, the city:

- increases population
- resets stored food
- emits population/UI refresh signals

### Starvation

If negative food would push stored food below zero, the city:

- loses population
- recalculates required food
- emits `game.gameplay.city.population_starve`

## Border growth flow

Border growth is driven by culture through `_process_border_growth()`.

Each turn the city:

1. adds culture yield to `border_growth_points`
2. recalculates `border_growth_next_tile` if needed
3. requests the next tile once enough points are available

The actual ownership handoff happens through the world manager in response to `game.gameplay.city.requests_tile`.

### Tile choice heuristic

`recalculate_border_growth_next_tile()` searches outward by radius, preferring:

1. available nearby tiles
2. resource-bearing tiles first when available
3. otherwise a random available tile in the nearest valid radius

So border growth is not purely random; it has a resource bias.

## Persistence behavior

Cities serialize more than just population and ownership. `dump()` includes:

- improvement set
- city effects
- active build state
- food and production accumulation
- owned tile tags
- border-growth state
- city icons and health

`load_state()` rebuilds:

- tile and owner references
- improvements and effects containers
- owned tiles
- active build instances
- border-growth target references

This makes city production one of the denser gameplay state surfaces in the current codebase.

## Signals worth knowing

Important signals around city production/growth include:

- `game.gameplay.city.starts_building_improvement`
- `game.gameplay.city.finish_building_improvement`
- `game.gameplay.city.starts_building_unit`
- `game.gameplay.city.finish_building_unit`
- `game.gameplay.city.canceled_production`
- `game.gameplay.city.requests_tile`
- `game.gameplay.city.gets_tile_ownership`
- `game.gameplay.city.border_growth`
- `game.gameplay.city.grows_population`
- `game.gameplay.city.population_starve`

See [Signals](signals.md) for the broader catalog.

## Implementation notes and current limitations

- The current model supports one active build, not a queue.
- Unit spawning is constrained by nearby valid tiles.
- Food, production, border growth, and owner contributions all happen inside the same city turn pass.
- Improvement effects are part of the city's computed yields, so production balance can be sensitive to effect ordering and maintenance values.

If you change the order of city turn processing or the build-state model, also update [Turn Processing](turns.md), [Signals](signals.md), and [Update Triggers](update-triggers.md).