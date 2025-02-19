from typing import Any, Optional, Union, List
from mixins.singleton import Singleton
from direct.showbase.MessengerGlobal import messenger

from managers.ui import ui
from managers.world import World
from managers.input import Input
from camera import CivCamera


class GameSettings:
    def __init__(
        self,
        width: int,
        height: int,
        player: Any,
        enemies: Optional[List[Any]],
        generator: Any,
    ):
        self.width: int = width
        self.height: int = height
        self.player: Any = player
        self.enemies: Optional[List[Any]] = enemies
        self.generator: Any = generator


class Game(Singleton):
    def __init__(self, base, camera: CivCamera):
        self.game_active: bool = False
        self.game_over: bool = False
        self.game_won: bool = False
        self.base: Any = base

        self.ui: ui = ui.get_instance()
        self.world: World = World.get_instance()
        self.input: Input = Input.get_instance()
        self.camera: CivCamera = camera

        self.properties: Optional[GameSettings] = None

    def __setup__(self, base, *args: Any, **kwargs: Any) -> None:
        super().__setup__(*args, **kwargs)
        self.base = base
        self.base.accept("system.input.user.tile_clicked", self.process_game_click)
        self.base.accept("system.game.start", self.on_game_start)

    def process_game_click(self, tiles: Union[list[str], str]):
        if isinstance(tiles, str):
            tiles = [tiles]
        messenger.send("ui.update.user.tile_clicked", tiles)
        self.ui.select_tile(tiles)

    def on_game_start(self):
        if not self.properties:
            raise ValueError("Game properties not set")
        self.game_active = True

        # Generate the world
        self.world.generate(self.properties.width, self.properties.height, 0.5, 1.5)
        self.world.delegate_to_generator()

        # Start the game ui
        self.ui.map = self.world

        # Some camera stuff
        self.middle_target = self.base.render.attachNewNode("middle_target")
        self.middle_target.setPos(self.world.middle_x, self.world.middle_y, 0)
        self.camera.active = True

        # Setup input for camera
        self.input.inject_into_camera()
        self.input.activate()

    def on_game_end(self):
        self.game_active = False
        self.game_over = True
        self.ui.cleanup_menu()
        self.ui.get_main_menu()
