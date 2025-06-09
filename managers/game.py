from logging import Logger
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type, Union

from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from direct.showbase.MessengerGlobal import messenger
from panda3d.core import WindowProperties  # type: ignore

from gameplay.border import Borders
from gameplay.civilization import Civilization
from gameplay.civilizations.rome import Rome
from gameplay.rules import GameRules, SCIVRules, set_game_rules

from gameplay.unit import Unit
from managers.config import ConfigManager
from managers.entity import EntityManager, EntityType
from managers.input import Input
from managers.player import PlayerManager
from managers.turn import Turn
from managers.world import World
from mixins.singleton import Singleton
from system.camera import Camera
from system.game_settings import GameSettings
from system.generators.basic import Basic
from system.mesh import HexGrid
from system.shaders import Shaders

if TYPE_CHECKING:
    from gameplay.player import Player
    from main import SCIV
    from system.generators.base import BaseGenerator
    from gameplay.tile import Tile


class Game(Singleton, DirectObject):
    def __init__(self, base: "SCIV", camera: Camera):
        from managers.ui import ui
        from managers.unit import UnitManager

        self.game_active: bool = False
        self.game_over: bool = False
        self.game_won: bool = False
        self.base: "SCIV" = base
        self.logger: Logger = self.base.logger.engine.getChild("manager.game")  # type: ignore

        self.ui: ui = ui.get_singleton_instance(base=self.base)
        self.world: World = World.get_singleton_instance()
        self.input: Input = Input.get_singleton_instance()
        self.turn: Turn = Turn.get_singleton_instance(base=self.base)
        self.camera: Camera = camera
        self.players: PlayerManager = PlayerManager()
        self.shader: Shaders = Shaders()
        self.border: Borders | None = None
        self.config: ConfigManager = ConfigManager.get_singleton_instance()
        self.entities: EntityManager = EntityManager.get_singleton_instance(base=self.base)
        self.unit: UnitManager = UnitManager.get_singleton_instance(base=self.base)
        self.mesh_grid: Optional[HexGrid] = None
        self.game_settings: GameSettings | None = None

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

        self._is_paused: bool = False
        self.debug: bool = False

        self.configure_environment()
        self.register()

    def register(self):
        def messenger():
            self.accept("window-event", self.config_saveback)
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

    def on_request_load(self, session_name: str) -> None:
        self.load(session_name)

    def load(self, session_name: str):
        MessengerGlobal.messenger.send("game.state.load_start")
        self.reset_game()
        self.entities.session = session_name
        self.entities.load()

        world_tiles: Dict[Any, "Tile"] = self.entities.get_all(EntityType.TILE)  # type: ignore

        players: Dict[str, "Player"] = self.entities.get_all(EntityType.PLAYER)  # type: ignore

        units: Dict[str, "Unit"] = self.entities.get_all(EntityType.UNIT)  # type: ignore

        self.world.load(world_tiles)
        self.players.load(players)
        self.unit.load(units)
        self.ui.map = self.world
        self.camera.recenter()
        self.turn.activate()
        self.border = Borders(self.world.get_size(), self.players, self.shaders, self.base.render)  # type: ignore

        self.accept("ui.request.update.borders", self.border.update_borders)

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
        self.world.reset()
        self.turn.reset()
        self.camera.reset()
        self.entities.reset()
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

        win_size: Tuple[int, int] = self.config.get_by_key("window", "win-size")
        win_origin: Tuple[int, int] = self.config.get_by_key("window", "win-origin")

        props.setSize(win_size[0], win_size[1])  # type: ignore
        props.setOrigin(win_origin[0], win_origin[1])  # type: ignore
        props.setTitle(f"{APPLICATION_NAME}<{VERSION_NAME_STRING}>")  # type: ignore

        self.base.win.requestProperties(props)  # type: ignore

    def environment_writeback(self) -> bool:
        self.logger.info("Writing back window properties to config")
        props: WindowProperties = self.base.win.getProperties()  # type: ignore
        win_size = (props.getXSize(), props.getYSize())  # type: ignore # Get current window size
        win_origin = (props.getXOrigin(), props.getYOrigin())  # type: ignore # Get window position

        old_win_size = tuple(self.config.get_by_key("window", "win-size"))
        old_win_origin = tuple(self.config.get_by_key("window", "win-origin"))

        if old_win_size == win_size and old_win_origin == win_origin:
            self.logger.info("No changes to write back")
            return False

        self.config.set_by_key([win_size[0], win_size[1]], "window", "win-size")
        self.config.set_by_key([win_origin[0], win_origin[1]], "window", "win-origin")
        return True

    def config_saveback(self, *args: Any, **kwargs: Any) -> None:
        if self.environment_writeback() is True:
            self.config.save_config()

    def register_callback_inputs(self):
        self.accept("system.input.user.tile_clicked", self.handle_tile_click)
        self.accept("system.input.user.unit_clicked", self.handle_unit_click)
        self.accept("system.input.user.tile_hovered", self.handle_tile_hover)
        self.accept("system.input.user.tile_unhovered", self.handle_tile_hover_end)
        self.accept("system.game.start_load", self.on_game_start)
        self.accept("game.input.user.quit_game", self.quit_game)
        self.accept("game.input.user.wireframe_toggle", self.toggle_pause_game)

    def __setup__(self, base: "SCIV", *args: Any, **kwargs: Any) -> None:
        super().__setup__(*args, **kwargs)
        self.base = base

        self.register_callback_inputs()

    def toggle_wireframe(self):
        if not self.debug:
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

    def handle_tile_click(self, tiles: Union[List[str], str]):
        if isinstance(tiles, str):
            tiles = [tiles]
        messenger.send("ui.update.user.tile_clicked", tiles)

    def handle_unit_click(self, units: Union[List[str], str]):
        if isinstance(units, str):
            units = [units]
        messenger.send("ui.update.user.unit_clicked", units)
        self.ui.select_unit(units)

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
        # Generate the world
        # 1) Width, 2) Height, 3) Radius stay around scale very minor = very big change, 4) Spacing between hexes
        self.world.generate(
            self.properties.width,  # type: ignore has already been checked on game start if not None
            self.properties.height,  # type: ignore has already been checked on game start if not None
            0.482,
            1.5,
        )
        assert self.properties is not None

        self.active_generator = self.properties.generator(self.properties, self.base)

        self.ui.map = self.world

    def camera_setup(self):
        # Some camera stuff
        self.camera.active = True

        # Setup input for camera
        self.input.inject_into_camera()
        self.input.activate()

    def setup_players(self):
        if self.active_generator is None:
            raise AssertionError("No generator was found, should have been set in generate_world")

        players = self.active_generator.setup_players(self.properties.player)  # type: ignore

        if players is None:
            raise ValueError("No players were setup")

    def on_game_start(self, map_size: str | Tuple[int, int], civilization: str | Type[Civilization], num_players: int):
        if self.properties is None:
            raise AssertionError("Game properties not set")
        self.logger.info("Game start requested")

        self.reset_game()

        self.properties.num_enemies = num_players
        self.properties.player = Civilization.get(civilization) if isinstance(civilization, str) else civilization  # type: ignore
        self.properties.width = int(map_size.split("x")[0]) if isinstance(map_size, str) else map_size[0]
        self.properties.height = int(map_size.split("x")[1]) if isinstance(map_size, str) else map_size[1]

        self.game_active = True
        self.logger.info(f"Game start requested with {self.properties}")
        self._try_game_start()

    def _try_game_start(self):
        self.logger.info("Starting world generation sequence")

        self.active_generator = self.world.get_generator()  # type: ignore
        self.generate_world()

        self.logger.info("World generation complete")

        self.logger.info(f"Setting up players({self.properties.num_enemies})")  # type: ignore
        self.setup_players()
        self.logger.info("Players setup complete")

        if self.active_generator is None:
            raise AssertionError("No generator was found, should have been set in generate_world")

        self.turn = Turn.get_singleton_instance(self.base)
        self.logger.info("Activating turn")
        self.turn.activate()

        self.logger.info("Setting up camera")
        self.camera_setup()

        player: "Player" = PlayerManager.player()
        self.entities.session = f"{player.name}"

        self.logger.info("Starting map generator")
        if not self.active_generator.generate():
            raise ValueError("There is no generator")

        self.logger.info("Setting up field")
        self.render_field()
        self.logger.info("Field setup complete")

        self.logger.info("Post-generation sequence")
        MessengerGlobal.messenger.send("game.state.load_complete")
        MessengerGlobal.messenger.send("game.state.true_game_start")
        MessengerGlobal.messenger.send("game.border.refresh")

        self.ui.post_game_start()
        self.camera.recenter()

        self.logger.info("Setting up borders")
        self.border = Borders(self.world.get_size(), self.shader, self.base.render)  # type: ignore
        self.logger.info("Borders setup complete")

        self.calculate_vision()

        self.mesh_grid: Optional[HexGrid] = self.active_generator.mesh_grid  # type: ignore
        self.players.on_game_start()
        self.border.setup_borders()

        self.accept("ui.request.update.borders", self.border.update_borders)

        self.logger.info("Game start complete")

    def calculate_vision(self):
        tiles = self.world.get_grid().values()
        units = self.unit.get_singleton_instance().all().values()

        for player in self.players.all().values():
            player.vision.mass_set_visible_tiles(tiles=set(tiles))
            for unit in units:
                player.vision.add_visible_unit(unit)

    def process_turn(self):
        self.turn.end_turn()

    def on_game_end(self):
        self.game_active = False
        self.game_over = True

    def render_field(self):
        for tile in self.world.grid.values():
            tile.calculate()
            tile.render()

        from system.scene_optimizer import SceneOptimizer

        SceneOptimizer.flatten_scene(self.base.render)

    def quit_game(self):
        self.base.destroy()

    def get_mesh(self) -> HexGrid:
        if self.mesh_grid is None:
            raise ValueError("Mesh grid has not been generated yet. Call generate_world() first.")
        return self.mesh_grid
