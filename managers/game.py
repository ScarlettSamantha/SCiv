from random import choice
from typing import Any, Optional, Type, Union, List, Dict

from data.tiles.tile import Tile
from gameplay.civilization import Civilization
from gameplay.civilizations.rome import Rome
from gameplay.leader import Leader
from gameplay.leaders.augustus import Augustus
from gameplay.personality import Personality
from gameplay.player import Player
from gameplay.units.classes._base import UnitBaseClass
from managers.i18n import T_TranslationOrStr
from managers.player import PlayerManager
from managers.turn import Turn
from mixins.singleton import Singleton
from direct.showbase.MessengerGlobal import messenger

from gameplay.repositories.player import PlayerRepository

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
        num_enemies: int,
        generator: Any,
        victory_conditions: Optional[List[Any]] = None,
        enemies: Optional[List[Any]] = None,
        difficulty: int = 0,
    ):
        self.width: int = width
        self.height: int = height
        self.player: Any = player
        self.enemies: Optional[List[Any]] = enemies
        self.generator: Any = generator
        self.difficulty: int = difficulty
        self.num_enemies: int = num_enemies


class Game(Singleton):
    def __init__(self, base, camera: CivCamera):
        self.game_active: bool = False
        self.game_over: bool = False
        self.game_won: bool = False
        self.base: Any = base

        self.ui: ui = ui.get_instance()
        self.world: World = World.get_instance()
        self.input: Input = Input.get_instance()
        self.turn: Optional[Turn] = None
        self.camera: CivCamera = camera
        self.players: PlayerManager = PlayerManager()

        self.properties: Optional[GameSettings] = None

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

    def on_game_start(self):
        if (
            not self.properties
            or not self.properties.width
            or not self.properties.height
        ):
            raise ValueError("Game properties not set")
        self.game_active = True
        self.turn = Turn.get_instance(self.base)
        self.turn.activate()

        def generate_world():
            # Generate the world
            # 1) Width, 2) Height, 3) Radius stay around scale very minor = very big change, 4) Spacing between hexes
            self.world.generate(
                self.properties.width,  # type: ignore has already been checked on gmae start if not None
                self.properties.height,  # type: ignore has already been checked on gmae start if not None
                0.482,
                1.5,
            )
            self.world.delegate_to_generator()
            self.ui.map = self.world

        def camera_setup():
            # Some camera stuff
            self.camera.active = True

            # Setup input for camera
            self.input.inject_into_camera()
            self.input.activate()

        def setup_players(index=0) -> List[Player] | None:
            if self.properties is None:
                raise ValueError("Game properties not set")

            if self.properties.num_enemies is None:
                raise ValueError("Number of enemies not set")

            players = []

            # Setup player
            def generate_player(
                name: T_TranslationOrStr,
                personality: Personality,
                civilization: Civilization,
                turn_order=index,
                leader: Optional[Leader] = None,
            ):
                if leader is None:
                    leader = civilization.random_leader()
                player = Player(
                    str(name), turn_order, personality, civilization, leader
                )
                return player

            # For testing @todo remove
            personalities: List[Type[Personality]] = [Personality]
            civilizations: Dict[str, Type[Civilization]] = (
                PlayerRepository.load_all_civilizations()
            )
            leaders: Dict[str, Type[Leader | Augustus]] = (
                PlayerRepository.load_all_leaders()
            )

            for i in range(
                self.properties.num_enemies + 1  # +1 for the player
                if self.properties is not None
                or self.properties.num_enemies is not None
                else 2
            ):
                personality: Personality = choice(personalities)()
                civilization: Civilization | Rome = choice(
                    list(civilizations.values())
                )()
                leader: Augustus | Leader = choice(list(leaders.values()))()  # type: ignore
                name = f"Player {i} - {civilization.name}"

                player = generate_player(name, personality, civilization, i, leader)
                if i == 0:
                    player.is_human = True
                    player.is_being_controlled = True
                players.append(player)
                self.players.add(player, i == 0)
            return players

        def place_starting_units():
            from gameplay.units.core.classes.civilian.settler import Settler

            units: List[UnitBaseClass] = []
            for player in self.players.players().values():
                unit: Settler = Settler(base=self.base)
                unit.owner = player
                spawn_tile: Optional[Tile] = None
                # We need to find a tile to spawn the unit on
                while True:
                    _spawn_tile: Optional[Tile] = self.world.random_tile()
                    if _spawn_tile.walkable is False or _spawn_tile.is_occupied():
                        continue
                    spawn_tile = _spawn_tile
                    break
                units.append(unit)
                player.units.add_unit(unit)
                spawn_tile.add_unit(unit)
                unit.spawn()
            return len(units) > 0

        generate_world()
        camera_setup()

        if setup_players() is None:
            raise ValueError("No players were setup")

        if not place_starting_units():
            raise ValueError("No units were placed")

    def on_game_end(self):
        self.game_active = False
        self.game_over = True
        self.ui.cleanup_menu()
        self.ui.get_main_menu()
