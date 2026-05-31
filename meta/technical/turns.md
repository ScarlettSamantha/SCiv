# Turn Processing

> Back to [Documentation Index](../INDEX.md)
>
> Related: [World System](world-system.md) | [Player System](player-system.md) | [Signals](signals.md)

This document explains how SCiv processes a turn, which stages exist, and where signals are emitted during the turn pipeline.

## Turn pipeline overview

The turn loop currently lives in [`sciv/managers/turn.py`](../../sciv/managers/turn.py) inside `Turn.process()`.

```mermaid
flowchart TD
    Request[game.requests.end_turn] --> Start[Turn.process()]
    Start --> SignalStart[game.turn.start_process]
    SignalStart --> World[TURN_WORLD]
    World --> Players[TURN_PLAYERS / TURN_PLAYERS_CITIES]
    Players --> Units[TURN_UNITS]
    Units --> Checks[TURN_CHANGE_END]
    Checks --> Increment[turn += 1]
    Increment --> Timings[game.turn.timings]
    Timings --> EndSignal[game.turn.end_process]
```

## Turn stages

| Stage | Enum value | What happens |
| --- | --- | --- |
| `NO_TURN_CHANGE` | `-1` | Idle state before and after processing. |
| `TURN_CHANGE_BEGIN` | `0` | Declared in the enum but not currently assigned during processing. |
| `TURN_WORLD` | `1` | World-level turn logic runs first. |
| `TURN_PLAYERS` | `2` | Player turn logic runs. |
| `TURN_PLAYERS_CITIES` | `3` | Each player's cities are processed after the player itself. |
| `TURN_PLAYERS_UNITS` | `4` | Declared in the enum but not currently used in `process()`. |
| `TURN_UNITS` | `5` | Registered units receive `on_turn_end()`. |
| `TURN_CHANGE_END` | `6` | Final checks run before the counter advances. |

## What `Turn.process()` actually does

### 1. Emit turn start

`Turn.process()` begins by sending `game.turn.start_process` with the current turn number.

This is the "about to process" signal.

### 2. Process world state

The world stage sets `turn_stage = TURN_WORLD` and calls `World.on_turn_end(self.turn)`.

`World.on_turn_end()` does not blindly process every tile. It filters for tiles that appear active or relevant, then processes world effects afterward. This keeps the stage focused on tiles and systems that actually need work.

See [World System](world-system.md) for the world manager's runtime ownership and filtering contract.

### 3. Process players and their cities

The player stage runs in this order:

1. nature player
2. barbarian player
3. every normal player from `PlayerManager.all()`
4. each city owned by each processed player

The current implementation sets `TURN_PLAYERS_CITIES` during the nested city loop, but it does not explicitly set `TURN_PLAYERS` before ordinary player work begins. If you rely on `turn_stage`, make sure you understand that nuance.

See [Player System](player-system.md) for how player roles and AI ownership feed into this stage.

### 4. Process units

The unit stage sets `turn_stage = TURN_UNITS`, fetches all unit references from `EntityManager`, resolves each weak reference, and calls `unit.on_turn_end(self.turn)`.

This means unit turn work is driven from the entity registry rather than from player ownership lists.

### 5. Run end-of-turn checks

The checks stage sets `TURN_CHANGE_END` and currently delegates to `AgesManager.on_turn_end(self.turn)`.

This is the place to look first when adding cross-cutting systems that should run after world, players, cities, and units have finished their turn work.

### 6. Advance the counter and emit completion signals

After all work finishes:

1. `self.turn` is incremented
2. `turn_stage` is reset to `NO_TURN_CHANGE`
3. `game.turn.timings` is emitted
4. `game.turn.end_process` is emitted

## Important signal timing detail

`game.turn.start_process` is emitted **before** the counter increments, using the turn that is being processed.

`game.turn.timings` and `game.turn.end_process` are emitted **after** `self.turn += 1`, so listeners receive the new current turn number rather than the turn that just finished processing.

That difference is easy to miss and matters when building UI labels, logs, or turn-based effects.

## UI refresh path after a turn

[`sciv/managers/ui.py`](../../sciv/managers/ui.py) listens for `game.turn.end_process` and refreshes several pieces of the main game UI:

- city display
- action bar
- top bar
- player turn control
- basic UI elements
- notifications

So while the turn manager owns the pipeline, the UI manager is responsible for reflecting the results back to the player.

## Extension guidance

When adding new per-turn behavior, decide which layer owns it:

- **world-wide or tile-focused behavior** → world stage
- **player economy / diplomacy / empire logic** → player stage
- **city production / growth** → city sub-stage
- **movement / recovery / per-unit upkeep** → unit stage
- **global checks / age transitions / wrap-up** → checks stage

If a new system also needs UI updates, pair the runtime change with a clear messenger signal or a refresh hook at the end of processing.

## Files to inspect when changing turn logic

- [`sciv/managers/turn.py`](../../sciv/managers/turn.py)
- [`sciv/managers/world.py`](../../sciv/managers/world.py)
- [`sciv/managers/player.py`](../../sciv/managers/player.py)
- [`sciv/managers/ui.py`](../../sciv/managers/ui.py)
- [`sciv/gameplay/city.py`](../../sciv/gameplay/city.py)
- [`sciv/gameplay/unit.py`](../../sciv/gameplay/unit.py)