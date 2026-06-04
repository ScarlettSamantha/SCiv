# SCiv Documentation Index

> Start here for project orientation. This index is intended for both human contributors and future coding agents.

## Recommended reading order

1. [README](../README.md) — project status, platform notes, and how to run the game.
2. [Project Structure](structure.md) — generated, human-readable project map.
3. [Project Index JSON](generated/project-index.json) — generated, machine-readable inventory for tooling and AI navigation.
4. [Doc Routing JSON](generated/doc-routing.json) — generated, machine-readable map of guarded areas to must-read docs.
5. [Project Index Helper](technical/project-index-helper.md) — canonical CLI for generating, browsing, querying, and validating the project index.
6. [Architecture](technical/architecture.md) — subsystem boundaries and the main runtime layers.
7. [Startup Flow](technical/startup.md) — boot path from `run.py` to `system.main.ready`.
8. [Asset System](technical/asset-system.md) — packaged archive flow, `AssetManager` caches, generated assets, and icon atlas lifecycle.
9. [World System](technical/world-system.md) — runtime world container ownership, tile collections, ownership transfer, and world-stage turn work.
10. [Tile System](technical/tile-system.md) — gameplay tile ownership, occupancy, terrain state, lookup, and render handoff.
11. [Player System](technical/player-system.md) — player registry roles, empire entity ownership, AI assignment, and player turn lifecycle.
12. [Rendering System](technical/rendering-system.md) — terrain model grid, tile-local renderers, icon atlas use, and picking tags.
13. [UI Runtime](technical/ui-runtime.md) — screen contracts, runtime HUD ownership, overlays, and input-lock policy.
14. [World Generation](technical/world-generation.md) — new-game generation flow, generator ownership, and the hexgen pipeline.
15. [Entities and Save/Load](technical/entities.md) — entity lifecycle, serialization, and state ownership.
16. [Turn Processing](technical/turns.md) — turn stages, signal timing, and where per-turn work happens.
17. [Mechanics Overview](technical/workings.md) — high-level guide to gameplay behavior docs and how the systems fit together.
18. [Agent Workflow](technical/agent-workflow.md) — repo-local workflow for SCiv-specialized coding agents.
19. [Python Conventions](technical/python-conventions.md) — Python 3.14 baseline, typing expectations, and Pyright-first authoring rules.
20. [Changelog Workflow](technical/changelog-workflow.md) — how SCiv maintains `CHANGELOG.md`, uses category defaults/gitmoji/ticket refs, syncs versions, and cuts release tags.

## Orientation map

### Start here

| File | Purpose |
| --- | --- |
| [README](../README.md) | High-level project overview and local run instructions. |
| [Project Structure](structure.md) | Generated navigation map for the workspace layout and key Python areas. |
| [Project Index JSON](generated/project-index.json) | Stable, machine-readable manifest of indexed modules, docs, entry points, and areas. |
| [Doc Routing JSON](generated/doc-routing.json) | Stable, machine-readable routing map for guarded subsystems and must-read docs. |
| [Project Index Helper](technical/project-index-helper.md) | Canonical CLI for generating, browsing, querying, and validating the project index. |

### Runtime docs

| File | Purpose |
| --- | --- |
| [Architecture](technical/architecture.md) | Explains how bootstrap, managers, gameplay, systems, and UI fit together. |
| [Startup Flow](technical/startup.md) | Documents initialization order and the handoff from loading screen to UI. |
| [Asset System](technical/asset-system.md) | Documents `assets.mf` packaging, archive mounting, loader caches, generated icons, and icon atlas generation. |
| [World System](technical/world-system.md) | Documents the runtime world container, authoritative tile collections, ownership transfer, and world-stage turn work. |
| [Tile System](technical/tile-system.md) | Documents tile entity ownership, occupancy, terrain state, and the gameplay-to-render handoff. |
| [Player System](technical/player-system.md) | Documents player-role storage, player entity ownership, AI assignment, and player startup/turn/save-load behavior. |
| [Rendering System](technical/rendering-system.md) | Documents terrain model placement, tile-local renderers, atlas-backed icon overlays, and picking contracts. |
| [UI Runtime](technical/ui-runtime.md) | Documents screen registration, `GameUIScreen`, menu handoff, and popup/input-lock behavior. |
| [World Generation](technical/world-generation.md) | Documents the new-game generation pipeline, generator contracts, and hexgen-to-gameplay conversion. |
| [Entities and Save/Load](technical/entities.md) | Covers `BaseEntity`, `EntityManager`, serializer behavior, and non-entity state. |
| [Turn Processing](technical/turns.md) | Documents `Turn.process()`, `TurnStage`, and turn-related signal timing. |
| [Signals](technical/signals.md) | Curated signal catalog. |
| [Rules](technical/rules.md) | Rule registry and customizable rule values. |
| [Workings](technical/workings.md) | Mechanics-focused notes that complement the lifecycle/runtime docs. |
| [Update Triggers](technical/update-triggers.md) | Maps guarded code areas to the docs that should be reviewed or updated with them. |
| [Python Conventions](technical/python-conventions.md) | Python 3.14 baseline, typing discipline, and Pyright-first authoring workflow. |
| [Changelog Workflow](technical/changelog-workflow.md) | Canonical `CHANGELOG.md` maintenance workflow, category/gitmoji convention, version sync, and release/tag helper usage. |

### Mechanics docs

| File | Purpose |
| --- | --- |
| [Mechanics Overview](technical/workings.md) | Hub for the focused gameplay/mechanics documentation. |
| [Tile System](technical/tile-system.md) | Tile ownership, occupancy, terrain/resource/improvement state, and pathing-oriented behavior. |
| [Vision and Fog of War](technical/vision-fog.md) | Gameplay-owned visibility emitters, lingering fog state, and player vision aggregation. |
| [Effects](technical/effects.md) | Persistent modifiers, placement, timing, and load behavior. |
| [Actions](technical/actions.md) | One-shot runtime actions, targeting, and callback flow. |
| [City Production and Growth](technical/city-production.md) | Food, production, border growth, and city-side turn processing. |
| [State Store](technical/state.md) | Shared non-entity runtime state and when to use it. |
| [Rules](technical/rules.md) | Rule registry and customizable rule values. |

### Contributor workflow docs

| File | Purpose |
| --- | --- |
| [Project Index Helper](technical/project-index-helper.md) | Canonical commands and freshness workflow for generating, browsing, querying, and validating the project index. |
| [Agent Workflow](technical/agent-workflow.md) | Preferred workflow for SCiv-specialized coding agents: read first, stay focused, make small changes, and write back durable learnings. |
| [Python Conventions](technical/python-conventions.md) | Python version, typing, and style expectations for SCiv code changes. |
| [Changelog Workflow](technical/changelog-workflow.md) | How to add and maintain changelog entries, category mappings, and version/release workflow with the helper. |

### Project tracking

| File | Purpose |
| --- | --- |
| [Documentation Audit](documentation-audit.md) | Reconnaissance report highlighting under-documented subsystems and explicit open questions found in code. |
| [Dynamic Worlds Plan](plans/dynamic_worlds.md) | Research-backed roadmap for evolving `Dynamic Worlds` with Civ-inspired pipeline, climate, and balance phases. |
| [Todo](todo.md) | Backlog and planned improvements. |
| [Known Bugs](../known_bugs.md) | Known rough edges and currently tracked issues. |
| [Changelog](../CHANGELOG.md) | Project changelog maintained through the root helper-driven workflow. |

## Maintenance rules

- Treat Git-tracked docs as the durable source of project knowledge.
- Regenerate the project map after structural changes with `python scripts/index.py generate` or `make docs-refresh`.
- Verify generated docs are current with `python scripts/index.py check` or `make docs-check`.
- When changing startup, world generation, turn flow, entities/save-load, or the Panda3D/Kivy bridge, update the corresponding file in `meta/technical/` in the same change.
- Use [Update Triggers](technical/update-triggers.md) when a change crosses subsystem boundaries or touches a guarded area.
- The generated inventory is authoritative for file layout. Curated technical docs explain behavior and intent.

## Notes for future AI sessions

- Start with this file, then the generated index, then the most relevant technical page.
- For tile or world-rendering work, jump straight to [Tile System](technical/tile-system.md) and [Rendering System](technical/rendering-system.md) after architecture/startup orientation.
- For player-registry, player-role, or empire-state work, read [Player System](technical/player-system.md) and [Turn Processing](technical/turns.md) after architecture/startup orientation.
- For vision, fog-of-war, or visibility refresh work, read [Vision and Fog of War](technical/vision-fog.md), then follow into [Player System](technical/player-system.md), [World System](technical/world-system.md), and [Effects](technical/effects.md) as needed.
- For world-container, tile-ownership, or world-turn work, read [World System](technical/world-system.md) and then follow into [Tile System](technical/tile-system.md) or [World Generation](technical/world-generation.md) as needed.
- For asset/archive/atlas work, read [Asset System](technical/asset-system.md) after architecture/startup orientation and then follow into [Rendering System](technical/rendering-system.md) when the change affects world consumers.
- For targeted lookups against the generated manifest, use the `sciv-project-index` skill or `python3 scripts/index.py search "<topic>"` before reading the full JSON.
- For Python authoring or typing-heavy tasks, read [Python Conventions](technical/python-conventions.md) early so code changes follow the 3.14 and Pyright rules from the start.
- For contributor-visible or workflow-visible changes, read [Changelog Workflow](technical/changelog-workflow.md) before finishing so `CHANGELOG.md`, gitmoji entry style, and release/tag flow stay current.
- Prefer repo docs over chat memory when they disagree.
- If the code changes in a way that invalidates these docs, update the docs rather than relying on memory alone.