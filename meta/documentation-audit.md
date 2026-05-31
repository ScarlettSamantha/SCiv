# Documentation Audit

> Back to [Documentation Index](INDEX.md)
>
> Captured on `2026-05-30` from a reconnaissance pass that compared curated docs against the generated project index and then spot-checked the highest-signal modules.

## What this note is

This file is a prioritized list of likely under-documented runtime surfaces and explicit open questions.

It does **not** mean the flagged systems are broken, unused, or safe to delete. It only means the code currently carries behavior or design intent that is not yet captured clearly in the curated documentation set.

## Indexers used in this pass

- **Coverage indexer**: compared `meta/technical/*.md`, `README.md`, and `known_bugs.md` against `meta/generated/project-index.json`.
- **Marker indexer**: scanned Python sources for `TODO`, `FIXME`, `HACK`, and similar uncertainty markers.
- **Sample indexer**: manually reviewed representative files from the highest-signal areas.

## Coverage pattern seen right now

Curated docs are strongest for:

- bootstrap and startup flow
- entity registration and save/load boundaries
- turn processing and signals
- rules, effects, actions, and city production
- shared non-entity state

The weakest documented runtime surfaces from this pass were:

| Area | Indexed modules | Generic inventory summaries | What that usually means |
| --- | ---: | ---: | --- |
| `sciv/menus` | `53` | `51` | Large UI surface is present, but most of it only appears in the generated inventory. |
| `sciv/system` | `38` | `29` | Engine-facing subsystems exist beyond the currently curated docs. |
| `sciv/helpers` | `18` | `18` | Helpers are relied on heavily but have no curated map yet. |
| `sciv/managers` | `24` | `14` | Several orchestration managers still only have auto-generated descriptions. |
| `sciv/gameplay` | `637` | `0` | The gameplay layer is broad; curated docs cover selected mechanics, not specialized subsystems like pathing, targeting, vision, or civilization data. |

## Highest-priority unknowns

| Priority | Surface | Evidence from spot check | Why it needs docs |
| --- | --- | --- | --- |
| High | World generation / hexgen | `sciv/system/subsystems/hexgen/mapgen.py` is a full pipeline: heightmap -> grid -> distances -> rivers -> territories -> geoforms -> moisture -> integrity checks. The folder also contains `hex.py`, `grid.py`, `territory.py`, `river.py`, and related support code. | This looks like a first-class subsystem, not a helper. Right now it is easy to miss or misread as implementation detail. |
| High | Runtime UI screen contracts | `sciv/menus/screens/game_ui.py` is the real runtime UI hub. It stages actions, manages target panels, opens/closes city/research/civics/log/inspect popups, and locks/unlocks camera and world input. `sciv/menus/screens/game_config.py` builds the pregame player/rules config and emits `system.game.start_load`. | Startup docs mention the UI bridge, but not the screen contracts that gameplay flow actually depends on. |
| High | Rendering and asset pipeline split | `sciv/system/renderers/tile_renderer.py` owns per-tile scene nodes, city UI bits, and scene-side models. `sciv/system/tile_renderer.py` owns the instanced icon overlay system. `sciv/system/asset_archive.py` mounts/serves assets for Panda3D and Kivy. | Current docs mention rendering and assets only at a high level. The actual division of responsibility is hidden in code. |
| Medium | Targeting, path preview, and combat UI | `GameUIScreen` builds a `MovementPathBlocksRenderer` from `sciv/gameplay/unit_path.py`. The scan also flagged `sciv/gameplay/ranged_targeting.py`, `sciv/managers/combat.py`, and `sciv/managers/combat_log.py` as under-documented. | Player interaction and combat feedback span gameplay, UI, and manager layers, so gaps here make future work riskier. |
| Medium | Localization and rules-at-game-start | `sciv/managers/i18n.py` loads nested JSON translations and caches lookups. `GameConfigMenu` edits values defined by `GameRules` before game start. | These systems affect UI text, startup behavior, and the contract for pregame configuration. |
| Low / clarify | `sciv/world/*` extension points | `sciv/world/features/_base_feature.py` and `sciv/world/weather/_base_weather.py` are effectively stubs. The `world/` package currently looks more like a placeholder or future extension seam than an active subsystem. | Without a note, future contributors or agents may assume this package already owns real runtime behavior. |

## Concrete open questions worth resolving

- Is `sciv/system/subsystems/hexgen/*` the authoritative map-generation stack, or is it sharing responsibility with `sciv/system/generators/*` in a way that should be documented explicitly?
- Which renderer should future contributors treat as the primary tile-render entry point: `sciv/system/renderers/tile_renderer.py` or `sciv/system/tile_renderer.py`?
- Which screen or manager owns the final say on input-lock policy when multiple popups or full-screen panels are open?
- Is `sciv/world/*` an intentional future design surface, a compatibility shell, or leftover scaffolding?

## Explicit code-level unknowns and placeholders

These are not all bugs, but they are places where the code itself signals uncertainty:

- `sciv/gameplay/player.py`
  - `focus`, `commitment`, and `goal` are still TODO placeholders.
  - The file also notes that citizens may need to become a separate system.
- `sciv/gameplay/actions/debug/set_terrain_type.py`
  - Contains a comment equivalent to “I do not know why this happens” when the terrain list is unexpectedly empty.
- `sciv/gameplay/tile.py`
  - Carries a TODO about a possible mountain-spawn bug.
- `sciv/menus/screens/pause_menu.py`
  - The options-opening path is still marked as not implemented.
- `meta/todo.md`
  - Already notes that the hexgen `Hex` / `Edge` model still carries full object references and should eventually move toward a tile-native model.

Normal abstract-base `NotImplementedError` contracts were **not** treated as backlog items by this pass unless they were paired with a TODO or obviously incomplete runtime behavior.

## Recommended documentation passes

`meta/technical/world-generation.md` and `meta/technical/ui-runtime.md` have now been added, along with matching routing updates.

1. Add `meta/technical/rendering-assets.md` for atlas generation, asset archive mounting, per-tile renderers, and instanced icon overlays.
2. Decide whether `sciv/world/*` is placeholder or active roadmap, and document whichever is true.
3. Consider a focused targeting/combat UI note if future work starts in `sciv/gameplay/unit_path.py`, `sciv/gameplay/ranged_targeting.py`, `sciv/managers/combat.py`, or `sciv/managers/combat_log.py`.

If only one follow-up doc gets written next, `rendering-assets.md` is the highest-value pick.

## How to use this file

Use this note as a reconnaissance map:

- when deciding which subsystem docs should be written next
- when an agent or contributor needs to know where the curated docs currently stop
- when triaging whether a code-reading session surfaced a durable new learning that belongs in `meta/technical/`
