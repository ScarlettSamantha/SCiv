# Asset System

> Back to [Documentation Index](../INDEX.md)
>
> Related: [Architecture](architecture.md) | [Startup Flow](startup.md) | [Rendering System](rendering-system.md) | [UI Runtime](ui-runtime.md)

This document explains how SCiv packages assets into `assets.mf`, mounts that archive into Panda3D's virtual filesystem, generates derived icon assets on disk, builds the shared icon atlas, and exposes those surfaces to renderers, helpers, and Kivy widgets.

## Scope and boundaries

- This page covers asset packaging, archive mounting, loader caches, generated asset outputs, and atlas generation.
- It does **not** replace [Rendering System](rendering-system.md); that page documents how world renderers consume the archive and atlas at draw time.
- It does **not** cover general save/load or gameplay ownership. Those remain in [Entities and Save/Load](entities.md) and the focused gameplay docs.

## Ownership snapshot

| File | Responsibility |
| --- | --- |
| [`sciv/scripts/package_assets.py`](../../sciv/scripts/package_assets.py) | Build-time CLI for packaging one or more asset directories into a Panda3D multifile archive. |
| [`sciv/system/asset_archive.py`](../../sciv/system/asset_archive.py) | `P3DAssetArchive`: multifile builder, runtime VFS wrapper, byte reader, and archive-backed helpers for models, textures, images, fonts, and shaders. |
| [`sciv/managers/game.py`](../../sciv/managers/game.py) | Mounts the live `assets.mf` archive early in startup and stores it in `Cache`. |
| [`sciv/managers/assets.py`](../../sciv/managers/assets.py) | `AssetManager`: cache layer around Panda3D, Kivy, and PIL loaders, plus generation of numbered/static icon variants on disk. |
| [`sciv/system/atlas.py`](../../sciv/system/atlas.py) | `AtlasGenerator`: scans PNG sources, writes `atlas.png` and `mapping.json`, and caches Panda3D textures in `.txo` files. |
| [`sciv/game.py`](../../sciv/game.py) | Creates the `AssetManager`, runs or loads the icon atlas during startup, and registers the live atlas in `Cache`. |
| [`sciv/helpers/cache.py`](../../sciv/helpers/cache.py) | Global bridge used by renderers, helpers, and UI code to fetch the mounted archive and shared atlases. |
| [`sciv/helpers/model.py`](../../sciv/helpers/model.py) | Thin helper that routes model loads through `AssetManager` when callers want cached model access. |
| [`sciv/menus/kivy/elements/image.py`](../../sciv/menus/kivy/elements/image.py) and [`sciv/menus/kivy/elements/loading_screen.py`](../../sciv/menus/kivy/elements/loading_screen.py) | Archive-backed Kivy image helpers and widgets that read textures directly from the mounted archive. |

## End-to-end flow

```mermaid
flowchart TD
    Source[repo assets/] --> Package[package_assets.py / P3DAssetArchive.build()]
    Package --> Multifile[sciv/assets.mf]
    Multifile --> Mount[Game.__init__()<br/>mount_only() + Cache.set_asset_archive()]
    Mount --> AssetMgr[OpenCiv creates AssetManager]
    AssetMgr --> StaticGen[AssetManager.generate_static_assets()]
    StaticGen --> Generated[assets/generated/**/*.png on disk]
    Multifile --> AtlasScan[AtlasGenerator scans PNG inputs]
    Generated --> AtlasScan
    AtlasScan --> AtlasFiles[atlas.png + mapping.json + cache/*.txo]
    AtlasFiles --> IconCache[Cache.set_icon_atlas()]
    Mount --> RuntimeConsumers[Renderers, helpers, and Kivy widgets]
    IconCache --> RuntimeConsumers
```

## Packaged archive layer

### Build-time packaging: `P3DAssetArchive` and `package_assets.py`

[`sciv/scripts/package_assets.py`](../../sciv/scripts/package_assets.py) is the build-time entrypoint for the packaged archive. It wraps `P3DAssetArchive` and, by default, packages the top-level `assets/` directory into `assets.mf` with the archive prefix `assets`.

Key packaging behaviors:

- hidden files can be skipped
- extension allowlists and exclude globs can narrow what gets packaged
- files without extensions can be skipped
- text and binary extensions are registered with Panda3D so VFS reads use the correct mode

At build time, `P3DAssetArchive._gather_files()` turns real files into archive subfile names such as `assets/icons/...`, `assets/models/...`, or `assets/fonts/...`. That prefixed virtual-path convention is what most runtime callers use later.

### Runtime mounting and virtual paths

The live archive is mounted in [`Game.__init__()`](../../sciv/managers/game.py) before the `AssetManager` is created:

1. `Game` calls `P3DAssetArchive.mount_only(self.base.base_path / "assets.mf", ...)`
2. the wrapper mounts the archive into Panda3D's global `VirtualFileSystem`
3. `Game` stores that wrapper in `Cache.set_asset_archive(...)`

From that point on, code can resolve archive-backed files by virtual path, usually with the archive-internal `assets/` prefix still attached.

Current implementation note: the wrapper stores `mount_point` and `prefix`, but runtime reads still depend primarily on the prefixed subfile names written into the archive and a VFS mount at `.`. In other words, the archive's internal path layout does most of the real work.

## `AssetManager`: cache layer, not a universal gateway

`AssetManager` is the main convenience cache around common asset-loading paths, but it is **not** the only way SCiv accesses assets. Some systems load directly through Panda3D once the archive is mounted.

### Loader and cache behavior

| Method | Backing source | Cache behavior | Notes |
| --- | --- | --- | --- |
| `load_texture()` | Panda3D loader | caches `Texture` by CRC32 of the path | normalizes paths on Windows before calling Panda3D |
| `load_font()` | Panda3D loader | caches `TextFont` by CRC32 of the path | same Windows path normalization |
| `load_model()` | Panda3D loader | caches a template `NodePath`; cache hits return `copyTo(NodePath())` clones | later callers get detached copies instead of shared transforms |
| `load_image()` | Panda3D texture loader | reuses cached texture but returns a fresh `OnscreenImage` node each call | useful for 2D Panda UI/image nodes |
| `load_kivy_image()` | filesystem path resolved by `kivy.resources.resource_find()` | caches `CoreImage`; returns a fresh `KivyImage` widget each call | disk-oriented, not archive-backed |
| `load_pil_image()` / `load_pil_font()` | direct filesystem reads | caches PIL image/font objects | also disk-oriented, not archive-backed |

`AssetManager` only works after `OpenCiv` sets its `base` reference with `AssetManager.set_base(self)`. If `base` is missing, the loader-backed methods fail fast.

### Not every model load goes through `AssetManager`

The mounted archive lets Panda3D resolve virtual paths directly, so some runtime code bypasses `AssetManager` entirely:

- `TileModelGrid` loads terrain models through `base.loader.load_model(...)`
- the active runtime path in [`sciv/gameplay/unit.py`](../../sciv/gameplay/unit.py) loads unit models through `base.loader.loadModel(...)`
- archive-backed Kivy helpers often read bytes straight from `P3DAssetArchive`

Treat `AssetManager` as a cache and convenience surface, not as a mandatory facade for every asset access in the project.

## Generated assets and atlas build flow

### Step 1: derived PNGs are written to disk

`AssetManager.generate_static_assets()` is the first stage of the derived-asset pipeline.

It reads source bytes from the mounted archive via `Cache.get_asset_archive()` and writes generated PNGs under the data directory, notably:

- stacked resource icons for `Gold`, `Production`, `Food`, `Faith`, `Science`, and `Culture`
- numbered population icons built from the base population icon plus overlaid text

Those outputs live under `assets/generated/...` on disk rather than being written back into `assets.mf`.

This is why the archive must already be mounted before atlas generation starts.

### Step 2: `AtlasGenerator` merges archive PNGs and generated PNGs

`OpenCiv.generate_non_static_assets()` creates an `AtlasGenerator` configured around `sciv/assets.mf`, startup-configured icon dimensions, and the output files for the shared icon atlas.

`AtlasGenerator.pre_run()` then:

1. calls `AssetManager.generate_static_assets()`
2. records `assets/generated` as an extra filesystem source tree
3. mounts its **own** archive wrapper in multifile mode for PNG enumeration and byte reads

`AtlasGenerator.run()` merges PNG inputs from three places:

- PNG files inside `assets.mf`
- generated PNGs under `assets/generated/**`
- direct filesystem PNGs from real input directories when the generator is pointed at folders instead of a multifile archive

It then writes:

- the atlas image
- a JSON manifest keyed by virtual path
- a cached Panda3D atlas texture as `.txo`
- individual `.txo` sub-textures for per-icon access

The manifest is keyed by virtual path, which is why renderers and UI code can later ask for atlas entries by archive-like paths such as `assets/icons/...`.

### Step 3: startup either runs generation or trusts caches

`OpenCiv.generate_non_static_assets()` has two distinct startup paths:

- if generation is forced or the atlas files do not exist, it calls `icon_generator.run(...)`
- otherwise it calls `icon_generator.load_caches()` directly and skips generation

That means the freshness check inside `AtlasGenerator.run()` is only exercised on the generation path. During normal startup, an existing atlas cache is reused as-is.

If icon outputs become stale, the practical refresh paths are to force regeneration or remove the cached atlas outputs.

## Global cache bridge

[`helpers/cache.py`](../../sciv/helpers/cache.py) is the cross-subsystem handoff point for asset surfaces.

The asset-related cache entries are:

- `Cache.set_asset_archive()` / `Cache.get_asset_archive()`
- `Cache.set_icon_atlas()` / `Cache.get_icon_atlas()`
- `Cache.set_terrain_atlas()` / `Cache.get_terrain_atlas()`

In the current startup path:

- `asset_archive` is set by `Game.__init__()`
- `icon_atlas` is set by `OpenCiv.generate_non_static_assets()`
- `terrain_atlas` has storage in `Cache` but is not populated by the live startup sequence

Renderers and widgets generally pull these objects from `Cache` instead of having them threaded through constructors. That keeps bootstrap simpler, but it also makes startup order part of the system contract.

## Runtime consumers

### Rendering-side consumers

The main world renderers use the mounted archive and icon atlas as shared read surfaces:

- tile and terrain renderers load models and textures from archive-backed virtual paths
- `TileRendererSystem` uses the shared icon atlas manifest and textures for instanced tile-top icons
- border, selector, and other shader-backed overlays rely on the mounted VFS path layout for shader access

See [Rendering System](rendering-system.md) for the render-node and shader side of those consumers.

### UI and helper consumers

Kivy-facing code uses two distinct patterns:

- archive-backed helpers like [`image_widget_from_vfs()`](../../sciv/menus/kivy/elements/image.py) or `P3DAssetArchive.get_kivy_image_object()` read encoded bytes from the mounted archive and build Kivy textures from memory
- disk-backed helper paths such as `AssetManager.load_kivy_image()` rely on `resource_find()` and real files on disk

That split is intentional: generated atlas and archive assets can stay in VFS land, while some Kivy/PIL helpers still operate on normal filesystem paths.

## Current contracts and caveats

- `Game` mounts `assets.mf` **before** `OpenCiv` creates the `AssetManager`; this ordering is required because atlas pre-generation reads from `Cache.get_asset_archive()`.
- `AtlasGenerator` uses a private archive wrapper in multifile mode even though `Game` has already mounted the global archive wrapper.
- `AssetManager.generate_static_assets()` writes derived PNGs to disk under `assets/generated/**`; it does not mutate `assets.mf`.
- Existing atlas caches are loaded directly during normal startup, so cache reuse can hide source-asset changes until regeneration is forced.
- `AssetManager.load_kivy_image()`, `load_pil_image()`, and `load_pil_font()` are filesystem-oriented; use `P3DAssetArchive` helpers when the source only exists as archive bytes.
- `Cache._terrain_atlas` exists, but the current startup path only wires the icon atlas into live runtime consumers.
- `package_assets.py` is the packaging surface; runtime mounting and cache registration happen inside application startup, not inside the packaging script.