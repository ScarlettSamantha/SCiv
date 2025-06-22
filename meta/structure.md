# SCIV - Structure

> Back to main [Main](README.md)

> For bugs go here [Bugs](meta/known_bugs.md)

> For improvements go here [Todo](meta/todo.md)

## Folder Structure

| Folder Path                                     | Description                                                                                     |
|-------------------------------------------------|-------------------------------------------------------------------------------------------------|
| [./.vscode](./.vscode)                           | Contains project files for VSCode configuration.                                               |
| [./assets](./assets)                             | Contains assets like models, textures, sounds, and other resources.                             |
| [./exceptions](./exceptions)                     | Houses the exceptions used in the project.                                                     |
| [./gameplay](./gameplay)                         | Contains all gameplay logic and related data files.                                            |
| [./gameplay/actions](./gameplay/actions)         | Contains actions for timed events and unit operations.                                         |
| [./gameplay/civilizations](./gameplay/civilizations) | Contains all civilizations data.                                                               |
| [./gameplay/events](./gameplay/events)           | Contains events that can trigger actions (to be implemented later).                             |
| [./gameplay/exceptions](./gameplay/exceptions)   | Contains exceptions thrown during gameplay that should be handled.                              |
| [./gameplay/greats](./gameplay/greats)           | Houses data objects for great people.                                                          |
| [./gameplay/improvements](./gameplay/improvements) | Contains tile improvements.                                                                    |
| [./gameplay/items](./gameplay/items)             | Currently an idea; not heavily used.                                                           |
| [./gameplay/leaders](./gameplay/leaders)         | Contains data for leaders.                                                                     |
| [./gameplay/personalities](./gameplay/personalities) | Contains personalities and personality tags (fixed, logic-based, random, or stately).            |
| [./gameplay/planes](./gameplay/planes)           | Contains layer data for different planes (Space, Ground, Air, Water). May be refactored later.    |
| [./gameplay/repositories](./gameplay/repositories) | Houses repositories for entities with query and load options (might be moved to root).          |
| [./gameplay/resources](./gameplay/resources)     | Contains data files for spawnable resources.                                                   |
| [./gameplay/techs](./gameplay/techs)             | Contains tech data files.                                                                      |
| [./gameplay/terrain](./gameplay/terrain)         | Contains terrain data files (moved from data/).                                                 |
| [./gameplay/tiles](./gameplay/tiles)             | Contains all tile data.                                                                        |
| [./gameplay/units](./gameplay/units)             | Contains unit data and the base unit class.                                                    |
| [./helpers](./helpers)                           | Houses stateless helper classes (e.g., color utilities).                                       |
| [./i18n](./i18n)                                 | Contains language translation files; filename identifies the language.                         |
| [./logs](./logs)                                 | Contains generated log files.                                                                  |
| [./managers](./managers)                         | Contains game managers with singleton-like behavior for save/load logic.                       |
| [./menus](./menus)                               | Contains UI elements, classes, frames, screens, and the main Kivy application.                 |
| [./menus/kivy/elements](./menus/kivy/elements)                               | Contains UI elements, that are custom or needed extra functionality from kivy |
| [./menus/screens](./menus/screens)                               | Houses all the UI "screens" that will be used by the application|
| [./mixins](./mixins)                             | Contains mixin classes for singletons and callback enhancements.                               |
| [./scripts](./scripts)                           | Contains scripts (e.g., log cleaner) not intended for runtime game execution.                  |
| [./stubs](./stubs)                               | Contains type hinting stubs for development; may be removed in production builds.              |
| [./system](./system)                             | Houses backend logic and engine extensions unrelated directly to gameplay.                     |
| [./system/generators](./system/generators)       | Contains world generators, with the main one named "Basic".                                    |
| [./system/subsystems](./system/subsystems)       | Contains hexgen and integrated libraries used by the basic generator.                          |

## File/Register Structure

| File Path                                                 | Description                                                                                   |
|-----------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| [./system/entity.py](./system/entity.py)                  | Registers all saveable non-manager entities present in the game world.                        |
| [./managers/action.py](./managers/action.py)              | Contains the generic action system for triggering actions without custom integration.         |
| [./managers/entity.py](./managers/entity.py)              | Main entity manager responsible for managing, registering/de-registering entities and saving.    |
| [./managers/game.py](./managers/game.py)                  | Main game controller; acts as the Game Master after initialization.                         |
| [./managers/input.py](./managers/input.py)                | Parses and generates events processed by the game.                                            |
| [./managers/log.py](./managers/log.py)                    | Contains the logging system for the project.                                                  |
| [./managers/player.py](./managers/player.py)              | Manages player state, event processing, and player handling.                                  |
| [./managers/turn.py](./managers/turn.py)                  | Controls the game turn state and processing.                                                  |
| [./managers/ui.py](./managers/ui.py)                      | Controls the UI; bridges Panda3D/game UI and the Kivy application.                            |
| [./managers/unit.py](./managers/unit.py)                  | Manages unit registration; all units must register here.                                      |
| [./managers/world.py](./managers/world.py)                | Wraps tile-related functionalities; intended for world-changing operations.                   |
| [./mixins/singleton.py](./mixins/singleton.py)            | Provides a singleton mixin used by managers and other classes |
| [./menus/kivy/core.py](./menus/kivy/core.py)                    | Contains the kivy app and the registrations for the screens, handles switching UI screens |
| [./i18n/en_EN.json](./i18n/en_EN.json)                    | Contains the base game language data; English acts as the fallback language.                  |
| [./gameplay/units/unit_base.py](./gameplay/units/unit_base.py) | Base class for units, containing the generic unit logic (UnitBaseClass).                       |
| [./gameplay/tiles/base_tile.py](./gameplay/tiles/base_tile.py) | Base class for tiles, including core tile logic and data management.                           |
| [./gameplay/rules.py](./gameplay/rules.py)                | Contains the base rule class and the sciv rule definitions                                    |
| [./gameplay/terrain/_base_terrain.py](./gameplay/terrain/_base_terrain.py) | Contains BaseTerrain, the parent class for all terrains, managing generic terrain logic.       |
| [./system/generators/basic.py](./system/generators/basic.py)   | Implements the main world generator using a modified hexgen.                                  |
| [./system/pyload.py](./system/pyload.py)                  | Dynamic loader for repositories; loads classes dynamically from given paths |
| [./system/actions.py](./system/actions.py)                | Contains the action systems base class and executor |
| [./main.py](./main.py)                                    | Entry point; boots managers, sets up the application, and provides a lean showbase.             |
| [./camera.py](./camera.py)                                | Contains the camera object; a generic civ-like camera (planned to be moved).                    |
| [./lights.py](./lights.py)                                | Contains the main game light; simple lighting setup (planned to be moved).                      |
| [./config.prc](./config.prc)                              | Panda config file loaded at startup for bootstrap and engine configuration.                   |
