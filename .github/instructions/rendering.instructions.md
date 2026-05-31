---
name: "SCiv Rendering Routing"
description: "Use when editing SCiv world rendering, tile/unit renderers, shader-driven overlays, icon atlas generation, terrain model-grid code, or render-node tagging surfaces. Routes rendering work to the right docs first."
applyTo: "{sciv/system/renderers/**,sciv/system/tile_renderer.py,sciv/system/tile_grid.py,sciv/system/tile_layers.py,sciv/system/unit_renderer.py,sciv/system/atlas.py,sciv/system/shaders.py,sciv/managers/assets.py,sciv/gameplay/unit.py,sciv/gameplay/border.py,sciv/gameplay/hover.py,sciv/gameplay/ranged_targeting.py,assets/shaders/**}"
---

# SCiv Rendering Routing

- Read [`meta/technical/rendering-system.md`](../../meta/technical/rendering-system.md) first for the world render stack: terrain model placement, tile-local renderers, active unit rendering, instanced icon overlays, atlas use, and picking tags.
- If the change touches archive mounting, atlas generation, or `AssetManager` cache behavior, also read [`meta/technical/asset-system.md`](../../meta/technical/asset-system.md).
- Also read [`meta/technical/architecture.md`](../../meta/technical/architecture.md) for ownership boundaries between gameplay state and Panda3D-facing systems.
- If the rendering change depends on tile state, city conversion, slot layouts, or generator-time terrain metadata, also read [`meta/technical/tile-system.md`](../../meta/technical/tile-system.md).
- If the change touches units, prefer the live render path in [`sciv/gameplay/unit.py`](../../sciv/gameplay/unit.py) first; treat [`sciv/system/unit_renderer.py`](../../sciv/system/unit_renderer.py) as an alternate path unless runtime wiring changes.
- If the change touches generator-side terrain-model creation or the handoff from world generation into the live scene, also read [`meta/technical/world-generation.md`](../../meta/technical/world-generation.md).
- When render-node contracts or routing change, update [`meta/technical/rendering-system.md`](../../meta/technical/rendering-system.md), [`meta/technical/update-triggers.md`](../../meta/technical/update-triggers.md), and the orientation routing matrix in the same change.
