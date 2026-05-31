---
name: "SCiv Entities and Save Routing"
description: "Use when editing entity registration, BaseEntity behavior, serialization, save/load logic, entity keys, weak references, or state-manager boundaries in SCiv. Routes persistence work to the required docs first."
applyTo: "{sciv/system/entity.py,sciv/system/save_file.py,sciv/managers/entity.py,sciv/managers/state.py}"
---

# SCiv Entities and Save Routing

- Read [`meta/technical/entities.md`](../../meta/technical/entities.md) before changing entity identity, registration, serializer behavior, or persistence boundaries.
- If the task specifically touches `managers/state.py` or non-entity state boundaries, also read [`meta/technical/state.md`](../../meta/technical/state.md).
- Preserve entity keys, registry ownership, and weak-reference semantics unless the change is deliberate and documented.
- If save/load flow changes, inspect the live code path across `BaseEntity`, `EntityManager`, and the save-file helpers before editing.
- Update the persistence docs in the same change and review [`meta/technical/update-triggers.md`](../../meta/technical/update-triggers.md) for related pages that may also need edits.
