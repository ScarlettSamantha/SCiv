from typing import Any, Optional, Tuple, Type, Union, List

from gameplay.civilization import Civilization
from gameplay.repositories.generators import GeneratorRepository
from managers.player import PlayerManager
from managers.turn import Turn
from mixins.singleton import Singleton
from direct.showbase.MessengerGlobal import messenger

from managers.ui import ui
from managers.world import World
from managers.input import Input
from camera import CivCamera
from system.generators.base import BaseGenerator
from gameplay.civilizations.rome import Rome
from system.generators.basic import Basic
from system.game_settings import GameSettings
from gameplay.civilization import Civilization as BaseCivilization


class Game(Singleton):
    def __init__(self, base, camera: CivCamera):
        self.game_active: bool = False
        self.game_over: bool = False
        self.game_won: bool = False
        self.base: Any = base

        self.ui: ui = ui.get_instance(base=self.base)
        self.world: World = World.get_instance()
        self.input: Input = Input.get_instance()
        self.turn: Optional[Turn] = None
        self.camera: CivCamera = camera
        self.players: PlayerManager = PlayerManager()

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

        self.is_paused: bool = False

    def __setup__(self, base, *args: Any, **kwargs: Any) -> None:
        super().__setup__(*args, **kwargs)
        self.base = base
        self.base.accept("system.input.user.tile_clicked", self.handle_tile_click)
        self.base.accept("system.input.user.unit_clicked", self.handle_unit_click)
        self.base.accept("system.game.start", self.on_game_start)

    def handle_tile_click(self, tiles: Union[list[str], str]):
        if isinstance(tiles, str):
            tiles = [tiles]
        messenger.send("ui.update.user.tile_clicked", tiles)
        self.ui.select_tile(tiles)

    def handle_unit_click(self, units: Union[list[str], str]):
        if isinstance(units, str):
            units = [units]
        messenger.send("ui.update.user.unit_clicked", units)
        self.ui.select_unit(units)

    def choose_generator(self, random: bool = False, name: Optional[str] = None):
        if random:
            generator_cls: Type[BaseGenerator] | List[Type[BaseGenerator]] = GeneratorRepository.random(
                1
            )  # returns a class
        else:
            generators_cls: List[Type[BaseGenerator]] = GeneratorRepository.all()

            if len(generators_cls) == 0:
                raise AssertionError("No generators found")

            # Default to the first generator if no name is specified
            for candidate in generators_cls:
                if candidate.NAME == name:
                    generator_cls = candidate
                    break

        try:
            if generator_cls is None or not issubclass(generator_cls, BaseGenerator):  # type: ignore
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
            self.properties.width,  # type: ignore has already been checked on gmae start if not None
            self.properties.height,  # type: ignore has already been checked on gmae start if not None
            0.482,
            1.5,
        )
        assert self.properties is not None

        self.active_generator = self.properties.generator(self.properties, self.base)

        if self.active_generator is None:
            raise AssertionError("No generator was found, should have been set in generate_world")

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

    def on_game_start(self, map_size: str | Tuple[int, int], civilization: str | Civilization, num_players):
        from managers.ui import ui

        if self.properties is None:
            raise AssertionError("Game properties not set")

        self.properties.num_enemies = num_players
        self.properties.player = Civilization.get(civilization) if isinstance(civilization, str) else civilization  # type: ignore
        self.properties.width = int(map_size.split("x")[0]) if isinstance(map_size, str) else map_size[0]
        self.properties.height = int(map_size.split("x")[1]) if isinstance(map_size, str) else map_size[1]

        self.game_active = True

        self.active_generator = self.world.get_generator()  # type: ignore
        self.generate_world()
        self.setup_players()

        if self.active_generator is None:
            raise AssertionError("No generator was found, should have been set in generate_world")

        self.turn = Turn.get_instance(self.base)
        self.turn.activate()

        self.camera_setup()

        if not self.active_generator.generate():
            raise ValueError("There is no generator")

    def on_game_end(self):
        self.game_active = False
        self.game_over = True
