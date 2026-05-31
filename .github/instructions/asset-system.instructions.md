---
name: "SCiv Asset System Routing"
description: "Use when editing SCiv asset packaging, archive mounting, asset-manager caches, atlas generation, or archive-backed asset consumers. Routes asset-system work to the right docs first."
applyTo: "{sciv/managers/assets.py,sciv/system/asset_archive.py,sciv/system/atlas.py,sciv/scripts/package_assets.py,sciv/helpers/cache.py,sciv/helpers/model.py,sciv/menus/kivy/elements/image.py,sciv/menus/kivy/elements/loading_screen.py,sciv/menus/kivy/parts/civics.py}"
---

# SCiv Asset System Routing

- Read [`meta/technical/asset-system.md`](../../meta/technical/asset-system.md) first for the packaged `assets.mf` lifecycle, `AssetManager` cache semantics, generated icon flow, atlas caching, and `Cache` handoff points.
- Also read [`meta/technical/startup.md`](../../meta/technical/startup.md) and [`meta/technical/architecture.md`](../../meta/technical/architecture.md) because archive mounting and atlas generation depend on startup order and cross-subsystem ownership.
- If the change affects world-render consumers, icon-atlas lookups, or shader-backed overlays, also read [`meta/technical/rendering-system.md`](../../meta/technical/rendering-system.md).
- Remember that `AssetManager` is a convenience cache layer, not the only asset entrypoint; some runtime code reads directly from the mounted archive or Panda3D loader.
- When asset routing or ownership changes, update [`meta/technical/asset-system.md`](../../meta/technical/asset-system.md), [`meta/technical/update-triggers.md`](../../meta/technical/update-triggers.md), and the orientation routing matrix in the same change.
