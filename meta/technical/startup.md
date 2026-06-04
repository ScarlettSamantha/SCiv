# Startup Flow

> Back to [Documentation Index](../INDEX.md)
>
> Related: [Architecture](architecture.md) | [Asset System](asset-system.md) | [UI Runtime](ui-runtime.md) | [World Generation](world-generation.md)

This document follows the application startup path from the repository root launcher to the point where the UI is ready and the main menu becomes visible.

## Boot path

```mermaid
flowchart TD
    Run[run.py] --> Bootstrap[sciv/__main__.py bootstrap()]
    Bootstrap --> OpenCiv[sciv/game.py OpenCiv.__init__()]
    OpenCiv --> Loading[Loading screen stages]
    Loading --> Continue[OpenCiv.on_loading_screen_continue()]
    Continue --> Kivy[ui.kivy_setup()]
    Kivy --> Ready[system.main.ready]
    Ready --> MainMenu[ui.on_main_ready() -> main_menu]
```

## Step-by-step sequence

| Step | File / symbol | What happens |
| --- | --- | --- |
| 1 | [`run.py`](../../run.py) | Thin root launcher that imports `bootstrap` from `sciv.__main__` and calls it. |
| 2 | [`sciv/__main__.py`](../../sciv/__main__.py) → `bootstrap()` | Adjusts working directory to the package root, imports `OpenCiv` from `game`, instantiates the app, and calls `run()`. |
| 3 | [`sciv/game.py`](../../sciv/game.py) → `OpenCiv.__init__()` | Configures Kivy, loads Panda3D config, creates the application host, and initializes the manager stack. |
| 4 | [`sciv/game.py`](../../sciv/game.py) → loading screen stages | Shows incremental loading progress while managers, assets, and engine systems are prepared. |
| 5 | [`sciv/game.py`](../../sciv/game.py) → `on_loading_screen_continue()` | Starts the Kivy UI and emits `system.main.ready`. |
| 6 | [`sciv/managers/ui.py`](../../sciv/managers/ui.py) → `on_main_ready()` | Receives `system.main.ready` and switches the screen manager to `main_menu`. |

## `OpenCiv.__init__()` in practice

The `OpenCiv` constructor is the real startup orchestrator. In order, it does the following broad pieces of work:

1. Configures Kivy and patches it into the Panda3D window.
2. Loads `config.prc` and initializes `ShowBase`.
3. Sets up logging, configuration, and debug helpers.
4. Initializes world, input, camera, UI, entity, and game managers.
5. Mounts the packaged `assets.mf` archive through the game manager.
6. Creates and configures the asset manager.
7. Generates non-static assets such as icon atlases when required.
8. Sets up lighting and the unit manager.
9. Either waits on the loading screen or skips directly into `on_loading_screen_continue()` when configured to skip the intro.

## Important startup responsibilities

### Kivy/Panda3D bridge

The Kivy bridge is established early in [`sciv/game.py`](../../sciv/game.py) through `panda3d_kivy.monkey.patch_kivy()`. This is what allows the Kivy app to render into the Panda3D-managed window instead of running as a separate top-level application.

### Manager construction order matters

The startup order is meaningful because many managers assume that earlier systems already exist. A useful mental model is:

1. configuration and logging
2. world and input/camera foundations
3. UI and entity registries
4. game manager
5. assets, rendering support, and units

If startup fails mysteriously, check whether a manager is trying to access another singleton before it has been created or registered.

### Windowed geometry writeback waits for the window to settle

`Game.register()` listens to Panda3D `window-event` updates so SCiv can persist the live window size and origin back into the user config.

That writeback intentionally saves only after the windowed geometry has settled for a short quiet period and only when the final size/origin differs materially from the config. This filters out the transient property churn Panda3D can emit while the user is resizing the window, dragging it between monitors, or flipping between temporary intermediate window states.

Fullscreen, borderless, minimized, and invalid-size states are skipped on purpose. The saved geometry contract is specifically for stable windowed-mode restoration on the next launch.

### Asset bootstrap depends on that order

The asset pipeline relies on a specific startup sequence:

1. `Game.__init__()` mounts `assets.mf` and stores the archive in `Cache`.
2. `OpenCiv` creates `AssetManager` and gives it the live `ShowBase`.
3. `OpenCiv.generate_non_static_assets()` creates `AtlasGenerator`.
4. `AtlasGenerator.pre_run()` calls `AssetManager.generate_static_assets()`, which reads source bytes from `Cache.get_asset_archive()` before writing derived PNGs and building the shared icon atlas.

That means the archive mount must happen before atlas generation. See [Asset System](asset-system.md) for the detailed contract.

### `system.main.ready` is the UI handoff signal

The loading screen does not directly switch to the main menu. Instead, `OpenCiv.on_loading_screen_continue()` calls `ui_manager.kivy_setup()` and then emits `system.main.ready`. The UI manager listens for that message and performs the actual screen change.

This signal is the clean boundary between engine/bootstrap work and the live Kivy UI state.

## What happens after startup?

Startup only prepares the runtime. A real playable session begins later when the game manager receives a request to start or load a game.

- New game path: `Game.on_game_start()` → `_try_game_start()` → [World Generation](world-generation.md)
- Load path: `Game.load()`

Both paths eventually create or restore world state, activate the turn manager, and refresh the main game UI.

## Files to inspect when changing startup

- [`run.py`](../../run.py)
- [`sciv/__main__.py`](../../sciv/__main__.py)
- [`sciv/game.py`](../../sciv/game.py)
- [`sciv/managers/ui.py`](../../sciv/managers/ui.py)
- [`sciv/menus/kivy/core.py`](../../sciv/menus/kivy/core.py)

If a change affects the order of manager creation, Kivy bootstrapping, loading-screen continuation, or the `system.main.ready` signal, update this file in the same commit.