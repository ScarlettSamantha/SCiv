from datetime import datetime
from logging import Logger
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type, Union

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
from helpers.optimizations import debounce
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
from system.camera import Camera
from system.game_settings import GameSettings
from system.generators.basic import Basic
from system.mesh import HexGrid
from system.scene_optimizer import SceneOptimizer
from system.shaders import Shaders
from system.tile_grid import TileModelGrid

if TYPE_CHECKING:
    from gameplay.age import Age
    from gameplay.effect import Effect
    from gameplay.player import Player
    from gameplay.tile import Tile
    from gameplay.unit import Unit
    from managers.entity import Property
    from system.generators.base import BaseGenerator

    from sciv.game import OpenCiv


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
        self.mesh_grid: Optional[HexGrid] = None
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

        self.configure_environment()
        self.register()

        self.register_callback_inputs()

    def register(self):
        def messenger():
            # self.accept("window-event", self.config_saveback)
            self.accept("game.turn.request_end", self.process_turn)
            self.accept("game.state.request_load", self.on_request_load)
            self.accept("game.state.main_menu", self.on_main_menu)

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
        self.mesh_grid = self.entities.get_all(EntityType.WORLD).get("world_grid")  # type: ignore
        Cache.set_showbase_instance(self.base)
        if self.mesh_grid is None:
            raise ValueError("Mesh grid has not been generated yet")
        self.mesh_grid.load_state()

        TileRepository.grid = {(tile.x, tile.y): tile for _, tile in world_tiles.items()}

        self.players.load(players)
        self.unit.load(units)
        self.world.load(world_tiles)
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

        self.ui.set_screen("game_ui")
        self.input.activate()
        self.register_callback_inputs()

        self.game_active = True
        self.ui.post_game_start()
        self.ui.reset_game_ui()
        MessengerGlobal.messenger.send("game.state.load_finished")

    def reset_game(self):
        MessengerGlobal.messenger.send("game.state.reset_start")

        self.game_active = False
        self.game_over = False
        self.game_won = False

        self.ui.reset()

        if self.mesh_grid is not None:
            self.mesh_grid.reset()

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

    def environment_writeback(self) -> bool:
        props: WindowProperties = self.base.win.getProperties()  # type: ignore
        win_size: Tuple[int, int] = (props.getXSize(), props.getYSize())  # type: ignore # Get current window size
        win_origin: Tuple[int, int] = (props.get_x_origin(), props.get_y_origin())  # type: ignore # Get window position

        old_win_size: Tuple[int, int] = tuple(self.config.get_by_key(("window", "win-size")))
        old_win_origin: Tuple[int, int] = tuple(self.config.get_by_key(("window", "win-origin")))

        size_diff = abs(old_win_size[0] - win_size[0]) > 2 or abs(old_win_size[1] - win_size[1]) > 2
        origin_diff = abs(old_win_origin[0] - win_origin[0]) > 2 or abs(old_win_origin[1] - win_origin[1]) > 2

        if not size_diff and not origin_diff:
            self.logger.info("No significant changes to write back")
            return False

        self.config.set_by_key([win_size[0], win_size[1]], "window", "win-size")
        if win_origin[0] == 0 and win_origin[1] == 0:
            self.logger.info("Window origin is at (0, 0), not writing back, this is a bug in Panda3D")
        else:
            self.config.set_by_key([win_origin[0], win_origin[1]], "window", "win-origin")

        return True

    @debounce(0.5)
    def config_saveback(self, *args: Any, **kwargs: Any) -> None:
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
            generator_cls: Type["BaseGenerator"] | List[Type["BaseGenerator"]] = GeneratorRepository.random(
                1
            )  # returns a class
        else:
            generators_cls: List[Type["BaseGenerator"]] = GeneratorRepository.all()

            if len(generators_cls) == 0:
                raise AssertionError("No generators found")

            # Default to the first generator if no name is specified
            for candidate in generators_cls:
                if candidate.NAME == name:
                    generator_cls = candidate
                    break

        try:
            if generator_cls is None or not issubclass(generator_cls, "BaseGenerator"):  # type: ignore
                raise AssertionError("No valid generator found")
        except NameError:
            raise AssertionError("No valid generator found")

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

        if self.mesh_grid is not None:
            self.mesh_grid.reset()

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

    def on_game_start(self, map_size: str | Tuple[int, int], civilization: Type[Civilization], num_players: int):
        if self.properties is None:
            raise AssertionError("Game properties not set")
        self.logger.info("Game start requested")

        self.properties.num_enemies = num_players
        self.properties.player = civilization
        self.properties.width = int(map_size.split("x")[0]) if isinstance(map_size, str) else map_size[0]
        self.properties.height = int(map_size.split("x")[1]) if isinstance(map_size, str) else map_size[1]

        self.game_active = True
        self.logger.info(f"Game start requested with {self.properties}")
        messenger.send("ui.request.loading_screen", [civilization])

        def delay_start(*args: Any):
            self.logger.info("Delaying game start to allow loading screen to show")
            self._try_game_start()

        # Start the game after a short delay to allow the loading screen to show
        self.base.taskMgr.doMethodLater(0.5, delay_start, "delayedGameStart")

    def _try_game_start(self):
        self.logger.info("Starting world generation sequence")
        Cache.set_showbase_instance(self.base)

        self.active_generator = self.world.get_generator()  # type: ignore

        if self.ui is None:  # type: ignore
            self.ui = self.base.ui_manager

        self.debug = DebugManager()
        DebugManager.set_singleton_instance(self.debug)
        self.debug_enabled = self.config.get_by_key(("debug", "enable_debug"))

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

        if Debug.world_generation():
            Debug.dump_map_generation_data(generator=self.active_generator, tiles=list(self.world.map.values()))

        self.logger.info("Game start complete")

    def calculate_vision(self):
        tiles = self.world.get_grid().values()
        units = self.unit.get_singleton_instance().all().values()

        for player in self.players.all().values():
            player.vision.mass_set_visible_tiles(tiles=set(tiles))
            for unit in units:
                player.vision.add_visible_unit(unit)

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

    def quit_game(self):
        self.base.destroy()

    def get_mesh(self) -> HexGrid:
        if self.mesh_grid is None:
            raise ValueError("Mesh grid has not been generated yet. Call generate_world() first.")
        return self.mesh_grid

    def get_world_grid(self) -> TileModelGrid:
        if self.world_tile_grid is None:
            raise ValueError("World tile grid has not been generated yet. Call generate_world() first.")
        return self.world_tile_grid
