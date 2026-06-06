from datetime import datetime
from logging import Logger
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Set, Tuple, Type, Union, cast

from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from direct.showbase.MessengerGlobal import messenger
from gameplay.border import Borders
from gameplay.civilization import Civilization
from gameplay.civilizations.rome import Rome
from gameplay.lose import Lose, LoseConditions
from gameplay.repositories.tile import TileRepository
from gameplay.rules import GameRules, SCIVRules, set_game_rules
from helpers.cache import Cache
from helpers.debug import Debug, PerformanceLogger
from helpers.window_state import WindowState, window_state_differs, window_state_is_valid
from managers.ages import AgesManager
from managers.config import ConfigManager
from managers.debug import DebugManager
from managers.entity import EntityManager, EntityType
from managers.input import Input
from managers.player import PlayerManager
from managers.property import PropertiesManager, Property
from managers.turn import Turn
from managers.world import World
from mixins.singleton import Singleton
from panda3d.core import WindowProperties  # type: ignore
from sciv.gameplay.unit import Unit
from system.asset_archive import P3DAssetArchive
from system.camera import Camera
from system.game_settings import GameSettings
from system.generators.base import BaseGenerator
from system.generators.basic import Basic
from system.renderers.fog_of_war import FogBlobOverlay, FogOfWarController
from system.renderers.landmass_label_overlay import LandmassLabelOverlay
from system.scene_optimizer import SceneOptimizer
from system.shaders import Shaders
from system.tile_grid import TileModelGrid
from system.tile_renderer import TileRendererSystem

if TYPE_CHECKING:
    from gameplay.age import Age
    from gameplay.effect import Effect
    from gameplay.player import Player
    from gameplay.tile import Tile
    from gameplay.unit import Unit
    from managers.entity import Property
    from sciv.game import OpenCiv


WINDOW_SAVEBACK_SETTLE_DELAY_SECONDS = 0.75


class Game(Singleton, DirectObject):
    def __init__(self, base: "OpenCiv", camera: Camera):
        from managers.ui import ui
        from managers.unit import UnitManager

        self.game_active: bool = False
        self.game_over: bool = False
        self.game_won: bool = False
        self.base: "OpenCiv" = base
        self.base.set_background_color(0.050, 0.050, 0.050, 1.0)
        self.logger: Logger = self.base.logger.engine.getChild("manager.game")  # type: ignore

        self.ages: AgesManager | None = None

        self.asset_archive: P3DAssetArchive = P3DAssetArchive.mount_only(
            self.base.base_path / "assets.mf", mount_point="/", prefix="assets", priority=0
        )

        Cache.set_asset_archive(self.asset_archive)

        self.ui: ui = ui.get_singleton_instance()
        self.world: World = World.get_singleton_instance()
        self.input: Input = Input.get_singleton_instance()
        self.camera: Camera = camera
        self.players: PlayerManager = PlayerManager()
        PlayerManager.set_singleton_instance(self.players)
        self.debug: DebugManager = DebugManager.get_singleton_instance()
        self.shader: Shaders = Shaders()
        self.border: Borders | None = None
        self.config: ConfigManager = ConfigManager.get_singleton_instance()
        self.entities: EntityManager = EntityManager.get_singleton_instance()
        self.world_tile_grid: Optional[TileModelGrid] = None

        self.properties_manager: PropertiesManager = PropertiesManager()
        PropertiesManager.set_singleton_instance(self.properties_manager)

        self.unit: UnitManager = UnitManager(base=self.base)
        UnitManager.set_instance(self.unit)
        self.tile_hex_grid: Optional[TileModelGrid] = None
        self.game_settings: GameSettings | None = None

        self.performance_logger: Optional[PerformanceLogger] = (
            PerformanceLogger(
                active_on_init=False,
                location=f"/performance_logs/performance_log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json",
            )
            if Debug.system_performance_logging()
            else None
        )

        self._rules: Optional[Type[GameRules]] = SCIVRules
        self.rules: GameRules = self._rules()

        set_game_rules(self.rules)

        self.active_generator: BaseGenerator | None = None
        self.fog_of_war: FogOfWarController = FogOfWarController()
        self.fog_blob_overlay: FogBlobOverlay | None = None

        self.properties: Optional[GameSettings] = GameSettings(
            width=5,
            height=5,
            num_enemies=2,
            generator=Basic,
            player=Rome,
            victory_conditions=None,
            enemies=None,
            difficulty=1,
        )
        Cache.set_game_settings(self.properties)
        self.game_settings = self.properties

        self._is_paused: bool = False
        self.debug_enabled: bool = False

        self._window_event_task_name: str = f"game-window-saveback-{id(self)}"
        self._pending_window_state: WindowState | None = None
        self._fog_unit_sync_task_name: str = f"game-fog-unit-sync-{id(self)}"
        self._vision_refresh_task_name: str = f"game-vision-refresh-{id(self)}"
        self._pending_fog_unit_sync_tile_tags: Set[str] = set()
        self._pending_fog_unit_sync_units: Dict[str, "Unit"] = {}

        self.configure_environment()
        self.register()

        self.register_callback_inputs()

    def register(self):
        def messenger():
            self.accept("window-event", self.on_window_event)
            self.accept("game.turn.request_end", self.process_turn)
            self.accept("game.state.request_load", self.on_request_load)
            self.accept("game.state.main_menu", self.on_main_menu)
            self.accept("game.gameplay.vision.updated", self.on_vision_updated)

        messenger()

    def save(self, session_name: str):
        MessengerGlobal.messenger.send("game.state.save_start")
        self.entities.add_meta_data("turn", self.turn.get_turn())
        self.entities.dump(session_name)
        MessengerGlobal.messenger.send("game.state.save_finished")

    def reroll(self):
        if self.properties is None:
            raise AssertionError("Game properties not set")

        self.reset_game()
        self.on_game_start(
            map_size=f"{self.properties.width}x{self.properties.height}",
            civilization=self.properties.player,
            num_players=self.properties.num_enemies,
        )

    def get_game_settings(self) -> GameSettings:
        if self.game_settings is None:
            raise ValueError("Game settings not initialized")

        return self.game_settings

    def on_main_menu(self):
        self.reset_game()
        self.ui.set_screen("main_menu")

    def on_request_load(self, session_name: str) -> None:
        self.load(session_name)

    def load(self, session_name: str):
        MessengerGlobal.messenger.send("game.state.load_start")

        self.ui = self.base.ui_manager
        self.turn = Turn(base=self.base)
        Turn.set_instance(self.turn)

        self.reset_game()
        self.entities.session = session_name
        self.entities.load()
        EntityManager.set_singleton_instance(self.entities)

        world_tiles: Dict[Any, "Tile"] = self.entities.get_all(EntityType.TILE)  # type: ignore
        players: Dict[str, "Player"] = self.entities.get_all(EntityType.PLAYER)  # type: ignore
        units: Dict[str, "Unit"] = self.entities.get_all(EntityType.UNIT)  # type: ignore
        effects: Dict[str, "Effect"] = self.entities.get_all(EntityType.EFFECT)  # type: ignore
        properties: Dict[str, "Property"] = self.entities.get_all(EntityType.PROPERTY)  # type: ignore

        size_x = max(tile.x for tile in world_tiles.values()) + 1
        size_y = max(tile.y for tile in world_tiles.values()) + 1

        Cache.set_showbase_instance(self.base)

        TileRepository.grid = {(tile.x, tile.y): tile for _, tile in world_tiles.items()}

        self.players.load(players)
        self.unit.load(units)
        self.world.load(world_tiles)

        self.tile_hex_grid = TileModelGrid(tiles=list(world_tiles.values()), radius=1.0, cols=size_x, rows=size_y)
        self.tile_hex_grid.load_state()
        self.tile_hex_grid.attach_to_render()
        self.tile_hex_grid.collect()
        self.world_tile_grid = self.tile_hex_grid

        TileRendererSystem.get().register_tiles(list(world_tiles.values()))

        [tile.render() for tile in world_tiles.values()]
        LandmassLabelOverlay.get().rebuild(self.world.grid.values())

        self.ui.map = self.world
        self.camera.recenter()
        self.turn.activate()

        self.properties_manager = PropertiesManager()
        PropertiesManager.set_singleton_instance(self.properties_manager)
        self.properties_manager.load(properties)  # type: ignore

        self.ages = AgesManager()
        AgesManager.set_instance(self.ages)
        self.ages.load_ages()
        _property: Property = self.properties_manager.get_singleton_instance().get_property("game.current_age")
        self.ages.set_age(_property)  # type: ignore

        self.border = Borders(self.world.get_size(), self.shader, self.base.render)  # type: ignore
        turn = self.entities.get_meta_data("turn")
        if turn is None:
            raise ValueError("No turn data found")

        self.turn.set_turn(turn)

        self.calculate_vision()

        self.ui.set_screen("game_ui")
        self.input.activate()
        self.register_callback_inputs()

        self.game_active = True
        self.ui.post_game_start()
        self.ui.reset_game_ui()
        self.base.get_camera().unlock_camera()
        self.base.get_camera().enable_zoom()
        MessengerGlobal.messenger.send("game.state.load_finished")

    def reset_game(self):
        MessengerGlobal.messenger.send("game.state.reset_start")

        self.game_active = False
        self.game_over = False
        self.game_won = False

        self.ui.reset()
        self.fog_of_war.reset()
        self._dispose_fog_blob_overlay()
        self._clear_pending_fog_sync_tasks()

        LandmassLabelOverlay.get().clear()

        if self.tile_hex_grid is not None:
            self.tile_hex_grid.reset()

        if self.world_tile_grid is not None and self.world_tile_grid is not self.tile_hex_grid:
            self.world_tile_grid.reset()

        self.tile_hex_grid = None
        self.world_tile_grid = None

        self.world.reset()
        self.turn.reset()
        self.camera.reset()
        self.entities.reset()
        EntityManager.set_singleton_instance(self.entities)
        self.players.reset()
        self.input.reset()
        self.unit.reset()
        MessengerGlobal.messenger.send("game.state.reset_finished")

    def is_paused(self) -> bool:
        return self._is_paused

    def configure_environment(self):
        self.base.disableMouse()
        from system.vars import APPLICATION_NAME, VERSION_NAME_STRING

        props = WindowProperties()  # type: ignore

        win_size: Tuple[int, int] = self.config.get_by_key(("window", "win-size"))
        win_origin: Tuple[int, int] = self.config.get_by_key(("window", "win-origin"))

        props.setSize(win_size[0], win_size[1])  # type: ignore
        props.setOrigin(win_origin[0], win_origin[1])  # type: ignore
        props.setTitle(f"{APPLICATION_NAME}<{VERSION_NAME_STRING}>")  # type: ignore

        self.base.win.requestProperties(props)  # type: ignore

    def _configured_window_state(self) -> WindowState:
        win_size_data: Any = self.config.get_by_key(("window", "win-size"), [1920, 1080])
        win_origin_data: Any = self.config.get_by_key(("window", "win-origin"), [0, 0])

        win_size: tuple[int, int] = (int(win_size_data[0]), int(win_size_data[1]))
        win_origin: tuple[int, int] = (int(win_origin_data[0]), int(win_origin_data[1]))
        return WindowState(origin=win_origin, size=win_size)

    def _window_saveback_enabled(self) -> bool:
        window = cast(Any, self.base.win)
        if window is None:
            return False

        if self.config.get_screen_mode() != "windowed":
            return False

        props = window.getProperties()
        if not props.getOpen() or props.getMinimized():
            return False

        return props.hasOrigin() and props.hasSize()

    def _read_window_state(self) -> WindowState | None:
        if not self._window_saveback_enabled():
            return None

        window = cast(Any, self.base.win)
        props = window.getProperties()
        state = WindowState(
            origin=(int(props.getXOrigin()), int(props.getYOrigin())),
            size=(int(props.getXSize()), int(props.getYSize())),
        )

        if not window_state_is_valid(state):
            return None

        return state

    def _write_window_state(self, state: WindowState) -> None:
        self.config.set_by_key([state.size[0], state.size[1]], "window", "win-size")
        self.config.set_by_key([state.origin[0], state.origin[1]], "window", "win-origin")

    def _clear_window_event_task(self) -> None:
        self.base.taskMgr.remove(self._window_event_task_name)

    def on_window_event(self, *args: Any) -> None:
        del args

        state = self._read_window_state()
        if state is None:
            self._pending_window_state = None
            self._clear_window_event_task()
            return

        if not window_state_differs(state, self._configured_window_state()):
            self._pending_window_state = None
            self._clear_window_event_task()
            return

        self._pending_window_state = state
        self._clear_window_event_task()
        self.base.taskMgr.doMethodLater(
            WINDOW_SAVEBACK_SETTLE_DELAY_SECONDS,
            self._flush_window_state_saveback,
            self._window_event_task_name,
        )

    def _flush_window_state_saveback(self, task: Any) -> Any:
        current_state = self._read_window_state()
        pending_state = self._pending_window_state

        if current_state is None or pending_state is None:
            self._pending_window_state = None
            return task.done

        if window_state_differs(current_state, pending_state):
            self._pending_window_state = current_state
            return task.again

        if not window_state_differs(current_state, self._configured_window_state()):
            self._pending_window_state = None
            return task.done

        self._write_window_state(current_state)
        self.config.save_config()
        self._pending_window_state = None
        return task.done

    def environment_writeback(self) -> bool:
        state = self._read_window_state()
        if state is None:
            return False

        configured_state = self._configured_window_state()
        if not window_state_differs(state, configured_state):
            return False

        self._write_window_state(state)

        return True

    def config_saveback(self, *args: Any, **kwargs: Any) -> None:
        del args, kwargs

        if self.environment_writeback() is True:
            self.config.save_config()

    def register_callback_inputs(self):
        self.accept("system.input.user.tile_hovered", self.handle_tile_hover)
        self.accept("system.input.user.tile_unhovered", self.handle_tile_hover_end)
        self.accept("system.game.player_game_over", self.on_game_end)
        self.accept("system.game.start_load", self.on_game_start)
        self.accept("game.input.user.quit_game", self.quit_game)
        self.accept("game.input.user.wireframe_toggle", self.toggle_pause_game)
        self.accept("game.era.progressing", self.on_age_progressing)
        self.accept("game.gameplay.unit.spawned", self.on_unit_visibility_candidate_changed)
        self.accept("game.gameplay.unit.moved", self.on_unit_visibility_candidate_changed)
        self.accept("game.gameplay.unit.destroyed.context", self.on_unit_destroyed)
        self.accept("system.unit.destroyed.context", self.on_unit_destroyed)

    def on_age_progressing(self, new_age: "Age"):
        if self.properties is None:
            raise AssertionError("Game properties not set")
        self.properties.set_age(new_age)
        self.entities.add_property("game.current_age", new_age)

    def toggle_wireframe(self):
        if not self.debug_enabled:
            return

    def toggle_pause_game(self) -> None:
        self._is_paused = not self._is_paused

    def pause(self):
        self._is_paused = True

    def unpause(self):
        self._is_paused = False

    def handle_tile_hover(self, tile: Union[List[str], str]):
        if isinstance(tile, str):
            tile = [tile]
        messenger.send("ui.update.user.tile_hover", tile)

    def handle_tile_hover_end(self, tile: Union[List[str], str]):
        if isinstance(tile, str):
            tile = [tile]
        messenger.send("ui.update.user.tile_unhovered", tile)

    def handle_tile_click(self, tiles: Union[str, "Tile"]) -> bool:
        forward: Optional[Union["Tile", str]] = None
        if isinstance(tiles, str):
            forward = tiles
        else:
            forward = tiles

        messenger.send("ui.update.user.tile_clicked", [forward])
        return self.ui.get_main_game_ui().process_tile_click(forward)  # type: ignore # @todo this is correct but mypy doesn't understand it

    def handle_unit_click(self, units: Union[str, "Unit"], select_unit: bool = True) -> bool:
        forward: Optional[Union["Unit", str]] = None
        if isinstance(units, str):
            forward = units
        else:
            forward = units
        messenger.send("ui.update.user.unit_clicked", [forward])
        return self.ui.get_main_game_ui().process_unit_click(forward)  # type: ignore # @todo this is correct but mypy doesn't understand it

    def choose_generator(self, random: bool = False, name: Optional[str] = None):
        from gameplay.repositories.generators import GeneratorRepository

        if random:
            generator_candidate: Type["BaseGenerator"] | List[Type["BaseGenerator"]] = GeneratorRepository.random(
                1
            )  # returns a class
        else:
            generators_cls: List[Type["BaseGenerator"]] = GeneratorRepository.all()

            if len(generators_cls) == 0:
                raise AssertionError("No generators found")

            if name is None:
                generator_candidate = generators_cls[0]
            else:
                generator_candidate = GeneratorRepository.get(name)

        generator_cls: Type[BaseGenerator] = generator_candidate[0] if isinstance(generator_candidate, list) else generator_candidate

        if self.properties is None:
            raise AssertionError("Game properties not set")

        # Instantiate the generator, thereby checking that it’s not an unbound type.
        self.active_generator = generator_cls(self.properties, self.base)  # Now self.generator is an instance.

    def generate_world(self):
        self.world.reset()
        self.world.generate(
            self.properties.width,  # type: ignore has already been checked on game start if not None
            self.properties.height,  # type: ignore has already been checked on game start if not None
            0.482,
            1.5,
        )
        assert self.properties is not None

        self.active_generator = self.properties.generator(self.properties, self.base)

        if self.tile_hex_grid is not None:
            self.tile_hex_grid.reset()

        self.ui.map = self.world

    def camera_setup(self):
        self.camera.active = True

        self.input.inject_into_camera()
        self.input.activate()

    def setup_players(self):
        if self.active_generator is None:
            raise AssertionError("No generator was found, should have been set in generate_world")

        players = self.active_generator.setup_players(self.properties.player)  # type: ignore

        if players is None:
            raise ValueError("No players were setup")

    def on_game_start(
        self,
        map_size: str | Tuple[int, int],
        civilization: Type[Civilization],
        num_players: int,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        if self.properties is None:
            raise AssertionError("Game properties not set")
        self.logger.info("Game start requested")

        self.properties.num_enemies = num_players
        self.properties.player = civilization
        self.properties.width = int(map_size.split("x")[0]) if isinstance(map_size, str) else map_size[0]
        self.properties.height = int(map_size.split("x")[1]) if isinstance(map_size, str) else map_size[1]

        generator_cls: Type[BaseGenerator] = self.properties.generator
        generator_options: Dict[str, Any] = generator_cls.get_default_setup_options()

        self.properties.start_config = config or {}

        if isinstance(config, dict):
            generator_config = config.get("generator")
            if isinstance(generator_config, dict):
                generator_payload = cast(Dict[str, Any], generator_config)

                raw_generator_cls: Any = generator_payload.get("class")
                if isinstance(raw_generator_cls, type) and issubclass(raw_generator_cls, BaseGenerator):
                    generator_cls = raw_generator_cls

                raw_generator_options: Any = generator_payload.get("options")
                if isinstance(raw_generator_options, dict):
                    generator_options_payload = cast(Dict[str, Any], raw_generator_options)
                    generator_options = generator_cls.sanitize_setup_options(generator_options_payload)

        self.properties.generator = generator_cls
        self.properties.generator_options = generator_options

        self.game_active = True
        self.logger.info(f"Game start requested with {self.properties}")
        messenger.send("ui.request.loading_screen", [civilization])

        def delay_start(*args: Any) -> None:
            self.logger.info("Delaying game start to allow loading screen to show")
            self._try_game_start()

        self.base.taskMgr.doMethodLater(0.5, delay_start, "delayedGameStart")

    def _try_game_start(self):
        self.logger.info("Starting world generation sequence")
        Cache.set_showbase_instance(self.base)

        self.active_generator = self.world.get_generator()  # type: ignore

        if self.ui is None:  # type: ignore
            self.ui = self.base.ui_manager

        self.debug = DebugManager()
        DebugManager.set_singleton_instance(self.debug)
        self.debug_enabled = self.config.get_debug_mode()

        self.entities = EntityManager()
        EntityManager.set_singleton_instance(self.entities)

        self.generate_world()
        self.game_settings = self.properties
        self.logger.info("World generation complete")

        self.logger.info(f"Setting up players({self.properties.num_enemies})")  # type: ignore
        self.setup_players()
        self.logger.info("Players setup complete")

        if self.active_generator is None:
            raise AssertionError("No generator was found, should have been set in generate_world")

        self.turn = Turn(base=self.base)
        Turn.set_instance(self.turn)
        self.logger.info("Activating turn")
        self.turn.activate()

        self.logger.info("Setting up camera")
        self.camera_setup()

        self.players = PlayerManager()
        PlayerManager.set_singleton_instance(self.players)

        player: "Player" = PlayerManager.player()

        self.entities.session = f"{player.name}"

        self.logger.info("Starting map generator")
        seed = self.active_generator.randomize_seed()
        self.active_generator.config.seed = seed
        self.properties.seed = seed  # type: ignore

        assert self.properties is not None
        Cache.set_game_settings(self.properties)

        if not self.active_generator.generate():
            raise ValueError("There is no generator")

        self.world_tile_grid = self.active_generator.model_grid

        TileRendererSystem.get().register_tiles(list(self.world.grid.values()))

        self.logger.info("Setting up field")
        self.render_field()
        self.logger.info("Field setup complete")

        if self.ages is None:  # type: ignore
            self.ages = AgesManager()
            AgesManager.set_instance(self.ages)

        self.ages.begin()
        self.entities.add_property("game.current_age", self.ages.get_current_age().dump())
        self.logger.info("Post-generation sequence")
        MessengerGlobal.messenger.send("game.state.load_complete")
        MessengerGlobal.messenger.send("game.state.true_game_start")
        MessengerGlobal.messenger.send("game.border.refresh")

        self.ui.post_game_start()

        TileRepository.grid = self.world.grid
        self.logger.info("Setting up borders")
        self.border = Borders(self.world.get_size(), self.shader, self.base.render)  # type: ignore
        self.logger.info("Borders setup complete")

        self.calculate_vision()

        self.players.on_game_start()
        self.border.setup_borders()
        self.base.get_camera().on_window_resize(None)  # type: ignore
        self.base.get_camera().recenter()

        self.accept("ui.request.update.borders", self.border.update_borders)

        if self.performance_logger is not None:
            self.performance_logger.activate()

        if Debug.should_export_world_generation():
            Debug.dump_map_generation_data(generator=self.active_generator, tiles=list(self.world.map.values()))

        self.logger.info("Game start complete")

    def calculate_vision(self):
        self.world.refresh_all_player_vision()

    def on_vision_updated(self, player: "Player", changed_tiles: set[str]) -> None:
        if not PlayerManager.is_session_player(player):
            return

        self.sync_session_player_fog(player, changed_tiles)

    def get_active_tile_grid(self) -> TileModelGrid | None:
        if self.world_tile_grid is not None:
            return self.world_tile_grid

        return self.tile_hex_grid

    def _ensure_fog_blob_overlay(self, tile_grid: TileModelGrid | None) -> FogBlobOverlay:
        radius = float(getattr(tile_grid, "radius", 1.0)) if tile_grid is not None else 1.0

        if self.fog_blob_overlay is None:
            self.fog_blob_overlay = FogBlobOverlay(parent=self.base.render, radius=radius)
        else:
            self.fog_blob_overlay.set_radius(radius)

        return self.fog_blob_overlay

    def _dispose_fog_blob_overlay(self) -> None:
        if self.fog_blob_overlay is None:
            return

        self.fog_blob_overlay.dispose()
        self.fog_blob_overlay = None

    def sync_session_player_fog(self, player: "Player", changed_tiles: Set[str] | None = None) -> None:
        if not self.world.grid:
            return

        tile_grid: TileModelGrid | None = self.get_active_tile_grid()
        tile_overlay: TileRendererSystem = TileRendererSystem.get()
        label_overlay: LandmassLabelOverlay = LandmassLabelOverlay.get()
        fog_blob_overlay: FogBlobOverlay = self._ensure_fog_blob_overlay(tile_grid)

        if changed_tiles is not None and self.fog_of_war.has_synced_player(player):
            units: List[Unit] = self._collect_units_for_vision_sync(changed_tiles)
            if not changed_tiles and not units:
                return

            self.fog_of_war.apply_changed_tags(
                player,
                changed_tiles,
                tile_grid=tile_grid,
                tile_overlay=tile_overlay,
                units=units,
                all_tiles=self.world.grid.values(),
                label_overlay=label_overlay,
                fog_blob_overlay=fog_blob_overlay,
                total_tiles=len(self.world.grid),
            )
            return

        units = cast(List["Unit"], list(self.entities.get_all(EntityType.UNIT).values()))

        self.fog_of_war.apply(
            player=player,
            tiles=self.world.grid.values(),
            units=units,
            tile_grid=tile_grid,
            tile_overlay=tile_overlay,
            label_overlay=label_overlay,
            fog_blob_overlay=fog_blob_overlay,
            changed_tile_tags=None,
        )

    def _collect_units_for_vision_sync(self, changed_tile_tags: Set[str]) -> List["Unit"]:
        units_by_tag: Dict[str, "Unit"] = {}

        for tile_tag in changed_tile_tags:
            tile = self.world.lookup_on_tag(tile_tag)
            if tile is None:
                continue

            for unit in tile.get_units():
                units_by_tag[unit.get_tag()] = unit

        return list(units_by_tag.values())

    def process_turn(self):
        if not Lose.check_if_game_over():
            self.turn.end_turn()
        else:
            self.logger.info("Game over detected, not processing turn.")

    def on_game_end(self, player: "Player", lose_condition: Union["LoseConditions", bool]) -> None:
        self.game_active = False
        self.game_over = True
        self.quit_game()

    def render_field(self):
        for tile in self.world.grid.values():
            tile.render()

        SceneOptimizer.flatten_scene(self.base.render)
        LandmassLabelOverlay.get().rebuild(self.world.grid.values())

    def quit_game(self):
        self.base.destroy()

    def get_mesh(self) -> TileModelGrid:
        if self.tile_hex_grid is None:
            raise ValueError("Mesh grid has not been generated yet. Call generate_world() first.")
        return self.tile_hex_grid

    def get_world_grid(self) -> TileModelGrid:
        if self.world_tile_grid is None:
            raise ValueError("World tile grid has not been generated yet. Call generate_world() first.")
        return self.world_tile_grid

    def on_unit_visibility_candidate_changed(self, unit: "Unit", *args: Any) -> None:
        if not self.game_active or not self.world.grid:
            return

        player = PlayerManager.player()
        if not PlayerManager.is_session_player(player):
            return

        affected_tile_tags = self._collect_unit_event_tile_tags(unit, args)

        if self._unit_belongs_to_player(unit, player):
            self._schedule_session_player_vision_refresh()
            return

        self._queue_session_player_unit_visibility_sync([unit], affected_tile_tags=affected_tile_tags)

    def on_unit_destroyed(
        self,
        unit: "Unit",
        destroyed_tile: Any = None,
        destroyed_owner: Any = None,
        *args: Any,
    ) -> None:
        if not self.game_active or not self.world.grid:
            return

        player = PlayerManager.player()
        if not PlayerManager.is_session_player(player):
            return

        affected_tile_tags = self._collect_unit_event_tile_tags(unit, (destroyed_tile, *args))
        owner = destroyed_owner if destroyed_owner is not None else self._unit_owner_or_none(unit)

        if self._entity_tag(owner) == self._entity_tag(player):
            self._schedule_session_player_vision_refresh()
            return

        self._queue_session_player_unit_visibility_sync([unit], affected_tile_tags=affected_tile_tags)

    def _schedule_session_player_vision_refresh(self) -> None:
        self.base.taskMgr.remove(self._vision_refresh_task_name)
        self.base.taskMgr.doMethodLater(0.03, self._flush_session_player_vision_refresh, self._vision_refresh_task_name)

    def _flush_session_player_vision_refresh(self, task: Any) -> Any:
        if not self.game_active or not self.world.grid:
            return task.done

        player = PlayerManager.player()
        if not PlayerManager.is_session_player(player):
            return task.done

        self.calculate_vision()

        if not self.fog_of_war.has_synced_player(player):
            self.sync_session_player_fog(player)

        return task.done

    def _queue_session_player_unit_visibility_sync(
        self,
        units: Iterable["Unit"],
        *,
        affected_tile_tags: Set[str] | None = None,
    ) -> None:
        if affected_tile_tags is not None:
            self._pending_fog_unit_sync_tile_tags.update(affected_tile_tags)

        for unit in units:
            unit_key = self._entity_tag(unit) or str(id(unit))
            self._pending_fog_unit_sync_units[unit_key] = unit

        self.base.taskMgr.remove(self._fog_unit_sync_task_name)
        self.base.taskMgr.doMethodLater(0.03, self._flush_session_player_unit_visibility_sync, self._fog_unit_sync_task_name)

    def _flush_session_player_unit_visibility_sync(self, task: Any) -> Any:
        units = list(self._pending_fog_unit_sync_units.values())
        affected_tile_tags = set(self._pending_fog_unit_sync_tile_tags)

        self._pending_fog_unit_sync_units.clear()
        self._pending_fog_unit_sync_tile_tags.clear()

        if units or affected_tile_tags:
            self.sync_session_player_unit_visibility(units, affected_tile_tags=affected_tile_tags)

        return task.done

    def _clear_pending_fog_sync_tasks(self) -> None:
        self.base.taskMgr.remove(self._fog_unit_sync_task_name)
        self.base.taskMgr.remove(self._vision_refresh_task_name)
        self._pending_fog_unit_sync_units.clear()
        self._pending_fog_unit_sync_tile_tags.clear()

    def sync_session_player_unit_visibility(
        self,
        units: Iterable["Unit"],
        *,
        affected_tile_tags: Set[str] | None = None,
    ) -> None:
        cached_units = list(units)
        changed_tile_tags = set(affected_tile_tags or set())

        if not cached_units and not changed_tile_tags:
            return

        player = PlayerManager.player()
        if not self.fog_of_war.has_synced_player(player):
            self.sync_session_player_fog(player)
            return

        tile_grid: TileModelGrid | None = self.get_active_tile_grid()
        tile_overlay: TileRendererSystem = TileRendererSystem.get()
        label_overlay: LandmassLabelOverlay = LandmassLabelOverlay.get()
        fog_blob_overlay: FogBlobOverlay = self._ensure_fog_blob_overlay(tile_grid)

        self.fog_of_war.apply_changed_tags(
            player,
            changed_tile_tags,
            tile_grid=tile_grid,
            tile_overlay=tile_overlay,
            units=cached_units,
            all_tiles=self.world.grid.values(),
            label_overlay=label_overlay,
            fog_blob_overlay=fog_blob_overlay,
            total_tiles=len(self.world.grid),
            rebuild_fog_blob=False,
        )

    def _collect_unit_event_tile_tags(self, unit: "Unit", values: Iterable[Any]) -> Set[str]:
        tile_tags: Set[str] = set()

        try:
            current_tile = unit.get_tile()
        except Exception:
            current_tile = None

        current_tile_tag = self._tile_tag_from_candidate(current_tile)
        if current_tile_tag is not None:
            tile_tags.add(current_tile_tag)

        for value in values:
            tile_tag = self._tile_tag_from_candidate(value)
            if tile_tag is not None:
                tile_tags.add(tile_tag)

        return tile_tags

    def _tile_tag_from_candidate(self, value: Any) -> str | None:
        if value is None:
            return None

        if isinstance(value, str):
            return value

        resolved = value
        if not hasattr(resolved, "get_tag") and not hasattr(resolved, "tag") and callable(value):
            resolved = value()
            if resolved is None:
                return None

        get_tag = getattr(resolved, "get_tag", None)
        if callable(get_tag):
            tile_tag = get_tag()
            if isinstance(tile_tag, str) and tile_tag:
                return tile_tag

        tile_tag = getattr(resolved, "tag", None)
        if isinstance(tile_tag, str) and tile_tag:
            return tile_tag

        return None

    def _unit_owner_or_none(self, unit: "Unit") -> Any:
        try:
            return unit.get_owner()
        except Exception:
            return getattr(unit, "owner", None)

    def _unit_belongs_to_player(self, unit: "Unit", player: "Player") -> bool:
        return self._entity_tag(self._unit_owner_or_none(unit)) == self._entity_tag(player)

    def _entity_tag(self, entity: Any) -> str | None:
        if entity is None:
            return None

        if isinstance(entity, str):
            return entity

        get_tag = getattr(entity, "get_tag", None)
        if callable(get_tag):
            tag = get_tag()
            if isinstance(tag, str) and tag:
                return tag

        tag = getattr(entity, "tag", None)
        if isinstance(tag, str) and tag:
            return tag

        return None
