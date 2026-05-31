# State Store

> Back to [Documentation Index](../INDEX.md)
>
> Related: [Entities and Save/Load](entities.md) | [Mechanics Overview](workings.md)

This document explains the lightweight non-entity state store in SCiv.

## Core file

| File | Responsibility |
| --- | --- |
| [`sciv/managers/state.py`](../../sciv/managers/state.py) | Defines the `State` class used as a class-level store for simple flags and arbitrary non-entity state. |

## Mental model

`State` is a **shared class-level bucket** for runtime data that does not naturally belong on a persistent gameplay entity.

It is much lighter than `EntityManager`:

- no entity registration
- no ownership graph
- no built-in serialization logic in this file itself
- no eventing or lifecycle management

In other words, this module is a storage helper, not a full subsystem by itself.

## Two storage lanes

### Flags

Flags live in `State._flags` and are intended for simpler, frequently changed values.

Allowed value types are:

- `str`
- `int`
- `bool`
- `float`

The API is:

- `set_flag()`
- `get_flag()`
- `remove_flag()`
- `clear_flags()`
- `get_flags()`
- `has_flag()`
- `load_flags()`

### Internal state

Arbitrary non-flag state lives in `State._state`.

The API is:

- `set_state()`
- `get_state()`
- `remove_state()`
- `clear_state()`
- `get_states()`
- `has_state()`
- `load_state()`

The in-file comment notes that lambdas are a poor fit because pickle-based flows do not reconstruct them sensibly.

## When to use `State`

Use `State` when the data is:

- not a saveable gameplay entity
- best modeled as manager-level or mechanic-level shared runtime state
- small enough that a lightweight global bucket is acceptable

## When not to use `State`

Do **not** use `State` when the data should instead be:

- a persistent gameplay object in `EntityManager`
- a durable property/value in the property system
- a one-shot operation better modeled as an action
- a modifier/effect attached to a tile, city, player, or unit

## Practical caveats

### Class-level storage means global lifetime

Because `State` stores data on the class, not an instance, it behaves like global process state. That makes it convenient, but also means:

- accidental key collisions are possible
- reset behavior must be deliberate
- documentation matters if multiple systems start depending on shared keys

### Persistence depends on outside wiring

`managers/state.py` exposes `load_state()` and `load_flags()`, but it does not define how saves are written or restored. Persistence depends on whatever higher-level save/load flow chooses to serialize and restore those dictionaries.

If the state store becomes a more central part of the game, the save/load contract should be documented and tested explicitly.

## Guidance for future use

If you introduce new `State` keys:

1. namespace them consistently
2. document what owns them
3. document who clears or reloads them
4. verify whether they must survive save/load or only live for one runtime session

If `State` grows beyond a small helper role, consider promoting the calling pattern into a more explicit manager or property-based model.