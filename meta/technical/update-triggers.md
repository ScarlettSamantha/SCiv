# Update Triggers

> Back to [Documentation Index](../INDEX.md)

This document maps sensitive code areas to the docs that should be reviewed or updated when those areas change.

## How to use this page

1. Find the code area you are changing.
2. Read the listed docs before editing if the task is risky or cross-cutting.
3. Update the listed docs in the same change if the behavior, ownership, or lifecycle meaningfully changes.

## Trigger matrix

| When code changes in | Read first | Usually update |
| --- | --- | --- |
| `run.py`, `sciv/__main__.py`, `sciv/game.py`, or manager init order | [`startup.md`](startup.md), [`architecture.md`](architecture.md) | `startup.md`, `architecture.md` |
| `sciv/system/generators/**`, `sciv/system/subsystems/hexgen/**`, `sciv/system/game_settings.py`, `sciv/managers/world.py`, or world-generation/generator-selection logic in `sciv/managers/game.py` | [`world-generation.md`](world-generation.md), [`startup.md`](startup.md), [`architecture.md`](architecture.md) | `world-generation.md`, `startup.md`, `architecture.md`, and this file as needed |
| `sciv/managers/world.py` or world-runtime load/reset/ownership flow in `sciv/managers/game.py` | [`world-system.md`](world-system.md), [`tile-system.md`](tile-system.md), [`world-generation.md`](world-generation.md), and [`turns.md`](turns.md) | `world-system.md`, `tile-system.md`, `world-generation.md`, `turns.md`, and this file as needed |
| `sciv/managers/turn.py`, turn-stage order, or `game.turn.*` flow | [`turns.md`](turns.md), [`signals.md`](signals.md) | `turns.md`, `signals.md` |
| `sciv/managers/player.py`, `sciv/gameplay/player.py`, `sciv/gameplay/player_tiles.py`, `sciv/gameplay/repositories/player.py`, `sciv/gameplay/ai/**`, or player-role setup in `sciv/system/generators/base.py` | [`player-system.md`](player-system.md), [`turns.md`](turns.md), [`world-generation.md`](world-generation.md), and [`entities.md`](entities.md) | `player-system.md`, `turns.md`, `world-generation.md`, `entities.md`, and this file as needed |
| `sciv/managers/entity.py`, `sciv/system/entity.py`, or `sciv/system/save_file.py` | [`entities.md`](entities.md) | `entities.md` |
| `sciv/managers/state.py` or other shared non-entity state boundaries | [`entities.md`](entities.md), [`state.md`](state.md) | `entities.md`, `state.md` |
| `sciv/gameplay/tile.py`, `sciv/gameplay/repositories/tile.py`, `sciv/gameplay/tile_slots.py`, or `sciv/managers/world.py` for tile ownership, occupancy, terrain/resource/improvement slots, or tile pathing | [`tile-system.md`](tile-system.md), [`world-generation.md`](world-generation.md), [`entities.md`](entities.md) | `tile-system.md`, `world-generation.md`, `entities.md`, and this file as needed |
| `sciv/managers/input.py`, `sciv/system/camera.py`, `sciv/helpers/input.py`, or `sciv/menus/kivy/mixins/collidable.py` for world picking, input raycaster gating, or camera zoom/input locks | [`architecture.md`](architecture.md), [`signals.md`](signals.md) | `architecture.md`, `signals.md`, and this file as needed |
| `sciv/system/tile_renderer.py`, `sciv/system/renderers/**`, `sciv/system/zoom_visibility.py`, `sciv/system/tile_grid.py`, `sciv/system/unit_renderer.py`, `sciv/system/shaders.py`, `sciv/system/atlas.py`, `sciv/managers/assets.py`, `sciv/gameplay/unit.py`, `assets/shaders/**`, `sciv/gameplay/border.py`, `sciv/gameplay/hover.py`, or `sciv/gameplay/ranged_targeting.py` | [`rendering-system.md`](rendering-system.md), [`architecture.md`](architecture.md), and [`tile-system.md`](tile-system.md) when tile state is involved | `rendering-system.md`, `architecture.md`, `tile-system.md`, and this file as needed |
| `sciv/managers/assets.py`, `sciv/system/asset_archive.py`, `sciv/system/atlas.py`, `sciv/scripts/package_assets.py`, `sciv/helpers/cache.py` for asset cache/archive fields, `sciv/helpers/model.py`, asset bootstrap in `sciv/game.py` or `sciv/managers/game.py`, or archive-backed UI image helpers under `sciv/menus/kivy/**` | [`asset-system.md`](asset-system.md), [`startup.md`](startup.md), [`architecture.md`](architecture.md), and [`rendering-system.md`](rendering-system.md) when world render consumers or atlas-backed overlays are involved | `asset-system.md`, `startup.md`, `architecture.md`, `rendering-system.md`, and this file as needed |
| `sciv/managers/ui.py`, `sciv/menus/**`, `sciv/menus/kivy/core.py`, manager-side screen/input handoff in `sciv/managers/game.py`, or `system.main.ready` flow | [`startup.md`](startup.md), [`architecture.md`](architecture.md), [`ui-runtime.md`](ui-runtime.md), [`signals.md`](signals.md) | `startup.md`, `architecture.md`, `ui-runtime.md`, `signals.md` |
| `sciv/system/effects.py`, `sciv/gameplay/effect.py`, or concrete effect implementations | [`effects.md`](effects.md), [`turns.md`](turns.md), [`entities.md`](entities.md) | `effects.md`, `turns.md`, `entities.md` as needed |
| `sciv/system/actions.py` or action-driven targeting/UI command behavior | [`actions.md`](actions.md), [`signals.md`](signals.md) | `actions.md`, `signals.md` as needed |
| `sciv/gameplay/city.py` or city production/growth/border behavior | [`city-production.md`](city-production.md), [`turns.md`](turns.md), [`signals.md`](signals.md) | `city-production.md`, `turns.md`, `signals.md` as needed |
| `sciv/gameplay/rules.py` or rule-definition behavior | [`rules.md`](rules.md), [`workings.md`](workings.md) | `rules.md`, `workings.md` as needed |
| `sciv/gameplay/**` mechanics that affect turn flow, persistence, or UI contracts more broadly | [`workings.md`](workings.md), plus the relevant focused mechanics doc and [`turns.md`](turns.md), [`entities.md`](entities.md), or [`signals.md`](signals.md) as needed | Matching technical docs for the affected behavior |
| Python source files, `run.py`, `scripts/**/*.py`, `pyproject.toml`, `pyrightconfig.json`, `SCIV.code-workspace`, or shared stub workflow/stub definitions for Python-version, typing, commenting/style, or authoring workflow changes | [`python-conventions.md`](python-conventions.md), [`agent-workflow.md`](agent-workflow.md) | `python-conventions.md`, `agent-workflow.md`, and this file as needed |
| `CHANGELOG.md`, `changelog.py`, version-setting workflow, or changelog-related make/workflow updates | [`changelog-workflow.md`](changelog-workflow.md), [`agent-workflow.md`](agent-workflow.md) | `changelog-workflow.md`, `agent-workflow.md`, `meta/INDEX.md`, and this file as needed |
| `meta/**`, `scripts/index.py`, `scripts/generate_project_index.py`, `scripts/query_project_index.py`, `.github/**`, `.gitlab-ci.yml`, or `makefile` for docs/indexing/routing/agent-workflow work | [`../INDEX.md`](../INDEX.md), [`../structure.md`](../structure.md), [`project-index-helper.md`](project-index-helper.md), [`agent-workflow.md`](agent-workflow.md) | `meta/INDEX.md`, `project-index-helper.md`, this file, `agent-workflow.md`, and any affected routing or generated docs |

## Maintenance rules

- If a new guarded subsystem appears, add it to this matrix in the same change.
- If generated docs stop matching the repo, regenerate them rather than hand-editing generated output.
- If a routing rule changes, update both this file and the skill routing matrix.
- When in doubt, prefer updating the relevant technical doc instead of leaving behavior implied only in code.