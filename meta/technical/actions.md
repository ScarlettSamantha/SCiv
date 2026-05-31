# Actions

> Back to [Documentation Index](../INDEX.md)
>
> Related: [Mechanics Overview](workings.md) | [Effects](effects.md) | [Signals](signals.md)

This document explains SCiv's one-shot action system.

## Core file

| File | Responsibility |
| --- | --- |
| [`sciv/system/actions.py`](../../sciv/system/actions.py) | Defines the `Action` class used for immediate, UI-facing, non-persistent operations. |

## Mental model

An action is a **runtime operation wrapper**. It packages together:

- what should happen
- whether it is currently allowed
- what to do on success, failure, or cancel
- how the UI should treat the action while targeting or refreshing

Actions are intentionally different from entities and effects:

- they are **not** registered in `EntityManager`
- they are **not** saved
- they are usually driven by user interaction or immediate game logic

## Main fields and behaviors

### Execution fields

- `action` — the callable that actually does the work
- `condition` — a boolean or callable gate checked before execution
- `success_condition` — optional post-run success evaluator
- `on_success`, `on_failure`, `on_cancel` — lifecycle callbacks
- `action_args`, `action_kwargs` — stored invocation context

### UI and targeting fields

- `on_the_spot_action`
- `targeting_tile_action`
- `targeting_unit_action`
- `keep_targeting_after_use`
- `use_target_arrow`
- `icon`, `description`, `useable`

These fields let the rest of the game and UI treat the action as more than just a raw Python callback.

### Turn/reset behavior

An action can optionally reset itself each turn through `on_turn_end(turn)`.

If `reset_every_turn` is `True`, the action clears:

- `action_result`
- disabled state

Otherwise it recomputes disabled state through `should_be_disabled()`.

## Execution flow

```mermaid
flowchart TD
    Run[Action.run()] --> Condition{Condition passes?}
    Condition -- No --> Failure[on_failure if present]
    Condition -- Yes --> Execute[action(...)]
    Execute --> SuccessCheck{success_condition present?}
    SuccessCheck -- Yes --> Eval{success_condition true?}
    Eval -- Yes --> SuccessCb[on_success]
    Eval -- No --> FailureCb[on_failure]
    SuccessCheck -- No --> Result{action_result is not False?}
    Result -- Yes --> SuccessCb2[on_success]
    Result -- No --> FailureCb2[on_failure]
    SuccessCb --> Refresh[optional UI refresh]
    FailureCb --> Refresh
    SuccessCb2 --> Refresh
    FailureCb2 --> Refresh
```

## Important semantics in `run()`

### Condition handling

`condition` can be either:

- a fixed boolean
- a callable that receives the action instance

If it evaluates to `False`, the action short-circuits into failure handling.

### Success handling nuance

If `success_condition` is provided, it becomes the authoritative success test after the action callable runs.

If `success_condition` is not provided, the current implementation treats any result other than the explicit boolean `False` as success.

That means:

- `False` means failure
- `None` counts as success
- other return values also count as success

This is a subtle but important behavior when designing new actions.

### UI refresh behavior

By default, successful or failed runs can trigger:

- `ui.update.ui.refresh_basic_elements`

through `auto_refresh_basic_elements`.

This makes actions a convenient place to connect runtime behavior back into UI refresh without hardcoding the refresh into every caller.

## Good fits for actions

- immediate unit commands
- temporary targeting flows
- direct UI button actions
- one-off operations that should not survive save/load
- thin wrappers around gameplay methods that need structured success/failure callbacks

## Poor fits for actions

- persistent ongoing bonuses
- anything that should survive save/load as a world-state concept
- mechanics that need to remain attached to a tile, city, player, or unit over time

Those are better modeled as [Effects](effects.md) or as entity state.

## Practical checklist

When adding or refactoring an action:

1. Decide whether the behavior is truly one-shot.
2. Decide whether the condition should be checked before execution or through a success condition after execution.
3. Decide whether the action should target tiles, units, or run immediately.
4. Decide whether it should refresh the UI automatically.
5. Confirm that failure paths are visible enough to the caller or player.

If an action is starting to accumulate persistent state, it is usually a sign that it should be split into an action plus a longer-lived entity/effect model.