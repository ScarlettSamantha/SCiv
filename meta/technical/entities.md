# Entities and Save/Load

> Back to [Documentation Index](../INDEX.md)

This document explains how SCiv models persistent runtime objects, how those objects are registered, and how save/load reconstructs them.

## Persistence boundary at a glance

```mermaid
flowchart TD
    Create[Create gameplay object] --> Register[EntityManager.register()]
    Register --> Runtime[Runtime references + gameplay updates]
    Runtime --> Dump[EntityManager.dump()]
    Dump --> Serializer[JSONEntityManagerSerializer]
    Serializer --> SaveFile[SaveJsonFile]
    SaveFile --> Load[EntityManager.load()]
    Load --> Resolve[Reference resolution]
    Resolve --> Restore[World / city / tile / effect load_state()]
```

## Core types

| Type | File | Role |
| --- | --- | --- |
| `BaseEntity` | [`sciv/system/entity.py`](../../sciv/system/entity.py) | Base class for persistent gameplay objects such as tiles, cities, units, and effects. |
| `EntityType` | [`sciv/managers/entity.py`](../../sciv/managers/entity.py) | Enum that defines registry buckets and the storage keys used during serialization. |
| `EntityManager` | [`sciv/managers/entity.py`](../../sciv/managers/entity.py) | Registry, serializer coordinator, metadata store, and save/load entrypoint. |
| `JSONEntityManagerSerializer` | [`sciv/managers/entity.py`](../../sciv/managers/entity.py) | Converts entity state into JSON-safe structures and rebuilds them during load. |
| `State` | [`sciv/managers/state.py`](../../sciv/managers/state.py) | Stores non-entity flags and arbitrary state for mechanics/managers that are not `BaseEntity` instances. |

## What makes something an entity?

`BaseEntity` provides the shared persistence-facing behavior used by most gameplay objects:

- generated identity (`id`, `tag`)
- registry bookkeeping (`entity_key`, `entity_type_ref`, `is_registered`)
- tile and owner references
- inspection hooks
- save/load helpers via `__getstate__()` and `__setstate__()`

In practice, entities are the long-lived gameplay objects that should survive a save/load round trip.

## `EntityManager` responsibilities

`EntityManager` is more than a dictionary of objects. It is responsible for:

- registering and unregistering persistent objects
- grouping them by `EntityType`
- tracking metadata and basic stats
- delegating serialization to the configured serializer
- delegating file I/O to the configured save-file handler
- restoring saved state back into live runtime objects

It also manages a small registry of `Property` values and `GameSettings`, which are persistent but are not standard gameplay `BaseEntity` subclasses.

## Serialization model

### Phase 1: collect state

During `EntityManager.dump()`:

1. the current registry is copied
2. the serializer converts each object into a JSON-safe state payload
3. metadata such as version, commit, stats, and save size are attached
4. the configured save handler writes the payload to disk

### Phase 2: normalize references

`JSONEntityManagerSerializer` converts object relationships into reference-friendly structures. Important behaviors include:

- `BaseEntity` instances become `__ref__` records keyed by `entity_key`
- weak references to entities are converted into entity references as well
- external helper objects can be stored via `__objref__`
- registered handlers normalize special types such as `datetime`

This is why entity identity matters so much: references are rebuilt from keys after the raw payload is read back.

### Phase 3: rebuild live objects

During `EntityManager.load()`:

1. the save handler reads raw serialized data
2. the serializer rebuilds objects from `_cls` metadata
3. entity references are resolved back to live objects or weak references
4. the runtime-specific managers take ownership again

The game manager's load flow then restores higher-level runtime state by handing loaded data back into world, player, unit, and property managers.

## `BaseEntity` save/load behavior

`BaseEntity.__getstate__()` deliberately strips runtime-only fields such as:

- `base`
- `_logger`
- direct owner/tile references

Instead, it stores tag-based references like `owner_tag` and `tile_tag`. On load, `__setstate__()` uses `EntityManager` to resolve those tags back into live references.

This keeps saved payloads independent of in-memory object identity.

When updating `BaseEntity.__setstate__()` or similar persistence helpers:

- resolve owner/tile weak references before replaying the rest of the raw state payload
- prefer assigning restored keys with `setattr(...)` rather than `self.__dict__.update(...)` in strict-typed code so the reference-rebuild phase stays explicit and Pyright can type-check the method cleanly

## Entity state versus non-entity state

| Kind of state | Where it lives | Notes |
| --- | --- | --- |
| Persistent gameplay objects | `EntityManager` | Tiles, units, cities, players, effects, properties, and game settings. |
| Simple frequently changing values | `State._flags` | Limited to `str`, `int`, `bool`, and `float`. |
| Complex non-entity runtime state | `State._state` | Can store arbitrary objects except for things that pickle cannot sensibly rebuild, such as lambdas. |
| Stateless one-off actions | [`sciv/system/actions.py`](../../sciv/system/actions.py) | Actions are intentionally not persistent. They execute and disappear. |

## Load-time second phase: `load_state()`

Entity reconstruction does not fully finish at raw deserialization. After the registry is restored, higher-level systems run their own state restoration passes.

Examples in the current code path:

- `World.load()` rebuilds world maps and dimensions
- improvements call `load_state()`
- cities call `load_state()`
- effects call `load_state()`
- tiles call `load_state()`

This second phase is where many runtime relationships become usable again after raw objects exist.

## Design implications

### Prefer stable identity over direct object capture

If a gameplay object needs to survive save/load, prefer storing stable identifiers and resolvable references instead of embedding opaque runtime objects.

### Keep transient behavior transient

If a system is fundamentally a one-shot behavior, it probably belongs in the action/effect layer rather than as saved entity state.

### Weak references are intentional

Weak references are widely used to reduce accidental circular ownership. If you replace them with strong references, review save/load and destruction behavior carefully.

## Files to inspect when changing persistence

- [`sciv/system/entity.py`](../../sciv/system/entity.py)
- [`sciv/managers/entity.py`](../../sciv/managers/entity.py)
- [`sciv/managers/state.py`](../../sciv/managers/state.py)
- [`sciv/system/save_file.py`](../../sciv/system/save_file.py)
- [`sciv/managers/game.py`](../../sciv/managers/game.py) for the higher-level load orchestration