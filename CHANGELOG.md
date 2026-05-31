# Changelog

## Unreleased

### Added

### Changed

### Fixed

### AI

### UI

- 🐛 Fixed the minimap startup crash by restoring viewport centroid calculation during initial camera-follow bounds setup.
- 💄 Added initial draggable HUD layout-debug settings and persisted positioning for core gameplay widgets.
- 💄 Extended layout debug dragging to debug overlays and modal popups, with an on-drag stats panel for position and size tuning.

### Engine

### Mechanics

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

