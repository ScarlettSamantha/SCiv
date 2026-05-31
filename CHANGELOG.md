# Changelog

## Unreleased

### Added

- ✨ Added raw world-generation JSON exports, repo-local export settings in Options, and an offline batch helper for generating multiple debug worlds.

### Changed

### Fixed

- 🐛 Fixed the in-game pause-menu options button so it opens settings and returns to the pause menu on Back.
- 🐛 Fixed offline worldgen previews so standalone exports handle shrubland biomes, keep post-conversion terrain labels, synthesize runtime tile dumps for the viewer, render ocean water with waterbody colors instead of desert biome colors, and label ocean/coast hexes by finalized terrain instead of raw climate biome text.
- 🐛 Fixed generator discovery so PyLoad skips conditional helper classes that are present in source but not defined at runtime.

### AI

### UI

- 🐛 Fixed the minimap startup crash by restoring viewport centroid calculation during initial camera-follow bounds setup.
- 💄 Added initial draggable HUD layout-debug settings and persisted positioning for core gameplay widgets.
- 💄 Extended layout debug dragging to debug overlays and modal popups, with an on-drag stats panel for position and size tuning.
- 💄 Added a selectable Dynamic Worlds map generator with generator-specific setup options in game setup.
- 💄 Made the minimap selected-tile marker subtler and easier to read when zoomed in.
- 🐛 Kept the gameplay player list on its native anchored HUD path to avoid the bottom-left layout-debug regression.
- 💄 Defaulted the new-game config screen and debug quick-start path to Dynamic Worlds while keeping Basic selectable.
- 💄 Added a dedicated Rivers overview in the worldgen viewer with stronger channel rendering and hydrology stats.
- 💄 Added Dynamic Worlds controls for river amount, river length bias, and tributary density in both new-game setup and worldgen viewer previews.
- 💄 Added terrain/resource texture and model previews to the worldgen viewer inspector while keeping preview metadata off the Kivy-heavy import path.
- 💄 Expanded the worldgen viewer's river diagnostics with network counts, braid/connector categories, top systems, and richer selected-hex river details.
- 💄 Moved worldgen viewer preview generation onto a background worker with a staged progress bar and added a Random seed button beside the seed field.
- 💄 Cleaned up the standalone worldgen viewer menu bar with shorter grouped View submenus and shorter top-level actions.
- 💄 Added multi-world generation batches to the worldgen viewer with a clickable overview grid and back-to-overview navigation.
- 💄 Added process-backed multi-world generation and a right-panel world switcher to the worldgen viewer batch flow.
- 💄 Made the worldgen viewer batch overview resize preview cards and thumbnails to keep a responsive three-across layout.
- 💄 Made the new-game setup screen keep its right-side options in a scrollable panel so generator-heavy setups no longer spill off the top.
- 🐛 Fixed minimap terrain colors so legacy byte-scale terrain fallback colors no longer clip to white.
- 💄 Fixed the minimap camera-footprint preview so degenerate rotation angles no longer glitch across the full screen.

### Engine

- ⚙️ Biased river source selection farther inland so generated river chains trend longer before falling back to closer sources.
- ⚙️ Bounded Dynamic Worlds river-network branching so braided rivers generate promptly while still producing connector and split/rejoin channels.
- ⚙️ Added a Dynamic Worlds option that can force all main ocean basins to connect through carved straits before rivers and geoforms run.
- ⚙️ Increased the in-game camera zoom-out cap for a wider world view.
- ⚙️ Added a soft camera pan boundary with slight map-edge overscroll to keep the view near the world.
- ⚙️ Smoothed camera pan, zoom, and rotation with more responsive drag controls and zoom-aware movement speed.

### Mechanics

- ✨ Improved Dynamic Worlds start placement scoring and fixed the map generator selector to show only real generators.
- ✨ Extracted reusable settlement tile scoring for Dynamic Worlds, settler recommendations, and future settler AI while adding script-aware coastline polish.
- ✨ Expanded Dynamic Worlds with named landmasses, biome styles, named biome regions and rivers, plus improved river source spacing.
- ✨ Reworked Dynamic Worlds to use its own heightmap-shaped generation path with stronger landmass and biome profile differences.
- ✨ Added Dynamic Worlds channel carving, inland seas, tributary river growth, river valleys, and stronger biome-belt shaping.
- 🎮 Smoothed Dynamic Worlds landmass shaping, reduced mountain-heavy maps, and shared the runtime conversion prep path between Basic and Dynamic.
- 🎮 Rebalanced Dynamic Worlds peak compression so inland scripts generate fewer mountains without changing hill thresholds.

### Content

### Docs

- 📝 Documented sparse comment guidance for Python authoring and agent workflow.
- 📝 Documented readability spacing and small focused change preferences in Python conventions.
- 📝 Documented category defaults, version sync, and unreleased/status helper workflow.
- 📝 Documented modularity and practical file-splitting preferences in Python conventions.
- 📝 Documented the project-index helper for users and agents and updated docs-refresh/docs-check guidance to the unified CLI.
- 📝 Documented the shared Kivy stub workflow, local ../Stubs vs repo ./stubs usage, and required typing validation for agent routing.

### Tooling

- 🔧 Added a typed changelog helper and documented the Python 3.14, Pyright, and minimap coordinate workflow rules.
- 🔧 Extended the changelog helper with gitmoji, ticket refs, and release/tag commands.
- 👷 Renamed the helper to changelog.py, added category presets and utility commands, and synced version metadata.
- 🔧 Unified the project-index tooling under scripts/index.py with generate, browse, query, stats, and doctor commands.
- 🔧 Added a standalone-safe PyQt6 worldgen viewer with flat-top odd-q rendering, a dynamic legend, top menu/toolbar actions, and direct in-app generator previews.
- 🔧 Extracted shared pure-Python terrain conversion helpers so live and offline worldgen reuse the same classification and cleanup rules without requiring Kivy.
- 👷 Added overlay coverage percentages, runtime-scope breakdowns, and inspector jump/copy helpers to the PyQt6 worldgen viewer.
- 👷 Added legend-hover map highlighting to matching categories in the PyQt6 worldgen viewer.
- 👷 Added View-menu sidebar section toggles and a scrollable left rail to the PyQt6 worldgen viewer.
- 🔧 Made the worldgen viewer legend derive biome and runtime terrain entries from the loaded dump so variants like Hills Tundra appear correctly.
- 👷 Added offline resource allocation and a Resources overlay to the standalone worldgen viewer.
- 👷 Raised the standalone worldgen viewer preview size cap to 500 × 500 for oversized inspection runs.

