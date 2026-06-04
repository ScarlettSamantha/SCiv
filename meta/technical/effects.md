# Effects

> Back to [Documentation Index](../INDEX.md)
>
> Related: [Mechanics Overview](workings.md) | [Entities and Save/Load](entities.md) | [Turn Processing](turns.md) | [Rules](rules.md)

This document explains how SCiv models persistent gameplay modifiers through the effect system.

## Core files

| File | Responsibility |
| --- | --- |
| [`sciv/gameplay/effect.py`](../../sciv/gameplay/effect.py) | Base `Effect` class, persistence state, placement metadata, and per-turn callback contract. |
| [`sciv/system/effects.py`](../../sciv/system/effects.py) | `Effects` container plus `EffectPlacers` and helper functions for attaching/removing effects. |
| `sciv/gameplay/effects/**` | Concrete effect implementations. |

## Mental model

In SCiv, an effect is a **persistent gameplay modifier** attached to another runtime object such as a tile, city, player, unit, improvement, or the world. Compared with one-shot actions, effects are intended to survive long enough to matter to game state and save/load.

Each effect carries three kinds of information:

1. **Attachment metadata** — what object it is attached to and how it should be placed.
2. **Mechanical impact** — most commonly `yield_impact` and `maintenance_impact`.
3. **Lifecycle behavior** — whether it is timed, whether it needs turn processing, and what callbacks it runs on placement, expiry, or removal.

The effect system also now exposes visibility-specific query hooks for gameplay vision and fog-of-war.

## Main runtime pieces

### `Effect`

The base class in [`sciv/gameplay/effect.py`](../../sciv/gameplay/effect.py) inherits from `BaseEntity`, which means effects participate in the persistent entity model:

- they have `tag`, `entity_key`, and `entity_type_ref`
- they can be registered with `EntityManager`
- they can be serialized and reconstructed during load

Important fields on the base class include:

- `place_method`
- `effect_types`
- `yield_impact`
- `maintenance_impact`
- `is_timed`, `duration`, and `turns_left`
- `needs_turn_processing`
- `attached_entity_type` and `attached_entity_key`

### `Effects`

The container class in [`sciv/system/effects.py`](../../sciv/system/effects.py) lives on effect-capable parent objects. It is responsible for:

- storing the current effect instances by tag
- registering effects on add when requested
- backfilling parent references on the effect
- executing placement/removal lifecycle hooks
- iterating effects on turn end

This means the effect logic is split across two layers:

- the **effect instance** decides what it does
- the **container** decides how it is stored, attached, and iterated

## Vision modifier hooks

Base `Effect` now exposes three no-op query methods that visibility code can override:

- `get_vision_range_bonus()`
- `get_vision_range_override()`
- `get_vision_linger_turns_bonus()`

`Effects` aggregates those hooks so unit, city, and player code can ask for final modifiers without hard-coding knowledge of specific effect subclasses.

That keeps gameplay vision effect-driven while preserving the existing placement and lifecycle model.

## Placement model

Placement is driven by `EffectPlacers`.

| Place method | Target |
| --- | --- |
| `PLACE_ON_TILE` | One tile |
| `PLACE_ON_PLAYERS_TILE` | All tiles owned by a player |
| `PLACE_ON_CITY_TILES` | All tiles owned by a city |
| `PLACE_ON_CITY` | The city object itself |
| `PLACE_ON_PLAYER` | The player object |
| `PLACE_ON_WORLD` | The world object |
| `PLACE_ON_UNIT` | A unit |
| `PLACE_ON_IMPROVEMENT` | An improvement |

The container also backfills the effect's parent-specific fields when possible. For example:

- tile-owned effects get `tile`
- city-owned effects get `city` and `tile`
- player-owned effects get `player`
- improvement-owned effects get `improvement`

This is what makes later callbacks able to reason about their owner without having to recompute the relationship manually.

## Lifecycle

### Creation and attachment

Typical flow:

1. Construct an effect with a base object.
2. Register it if needed.
3. Attach it using `apply()` or `apply_to_entity()`.
4. Let the container wire parent references and trigger `on_effect_applied()` if requested.

The helper `Effect.apply_to_entity()` is the shortest route when you want the system to both place and optionally register the effect in one flow.

### Turn processing

There are two cooperating turn loops:

- `Effects.on_turn_end(turn)` on the container
- `Effect.on_turn_end()` on the effect

The container iterates every attached effect, calls `effect.on_turn_end()`, and removes expired timed effects.

The effect then decides whether it actually does work. It returns early unless:

- `needs_turn_processing` is `True`
- the effect is `active`
- the effect is not already expired

If the effect is timed, `turns_left` is decremented. The effect then routes work to the type-specific callbacks declared in `effect_types`, such as:

- `on_city_turn_end()`
- `on_tile_turn_end()`
- `on_player_turn_end()`
- `on_global_turn_end()`
- `on_improvement_turn_end()`
- `on_unit_turn_end()`

### Expiry and removal

Timed effects expire when `turns_left <= 0`.

The current code path does three important things around expiry/removal:

1. calls the effect expiry/removal hooks
2. unregisters the effect if requested
3. removes it from the parent `Effects` container

If the effect is attached to an improvement, removal also triggers a tile render refresh.

## Persistence behavior

Effects are saved as real entities, not lightweight descriptors.

The `dump()` method stores:

- effect metadata and visibility
- placement method name
- impact yields
- timing flags
- attachment metadata (`attached_entity_type`, `attached_entity_key`)
- direct references like `tile`, `city`, `improvement`, or `unit` as tags where present

`load_state()` then:

- reconstructs enum-backed placement methods from stored names
- restores `Yields`
- resolves attached entity references from `EntityManager`
- reattaches the effect to its owner with `obj_ref.add_effect(self, execute_on_add=False)`

That last step is important: loading an effect is not just deserializing data, it also reconstitutes the parent/container relationship.

## Design guidance

### Prefer effects for persistent modifiers

Use an effect when the behavior should outlive a single click or should participate in save/load, turn progression, or visible status effects.

### Keep effect state focused

The current system supports stateful effects, but the codebase is easier to reason about when effect-local state stays small and most mechanical meaning is expressed through:

- placement
- impact yields
- timing
- explicit callbacks

### Use actions for one-shot behavior

If the behavior is immediate, UI-driven, and not meant to persist, it probably belongs in [Actions](actions.md), not in an effect.

## Practical checklist

When adding a new effect type:

1. Decide what it attaches to.
2. Choose an `EffectPlacers` placement method.
3. Decide whether it is timed.
4. Decide whether it needs per-turn processing.
5. Define what makes it visible or invisible to the player.
6. Confirm how it should load back into the parent object after save/load.

If changing the effect system itself, also review [Turn Processing](turns.md), [Entities and Save/Load](entities.md), and [Update Triggers](update-triggers.md).