from typing import List, Optional, TYPE_CHECKING, Tuple
from direct.showbase.MessengerGlobal import messenger
from data.tiles.base_tile import BaseTile
from managers.player import PlayerManager
from managers.entity import EntityManager, EntityType
from mixins.singleton import Singleton
from managers.world import World
from gameplay.units.unit_base import UnitBaseClass
from system.vars import Colors
from panda3d.core import PStatClient
from system.entity import BaseEntity


if TYPE_CHECKING:
    from main import Openciv
    from menus.kivy.core import SCivGUI
    from managers.game import Game


class ui(Singleton):
    current_menu = None

    def __init__(self, base):
        from managers.game import Game

        self.menus = []
        self._base: Openciv = base
        self.current_menu = None
        self.game: Optional["Game"] = Game.get_instance()
        self.map: World = World.get_instance()

        self.current_tile: Optional[BaseTile] = None
        self.previous_tile: Optional[BaseTile] = None

        self.neighbours_tiles: List[BaseTile] = []
        self.previous_tiles: List[BaseTile] = []

        self.current_unit: Optional[UnitBaseClass] = None
        self.previous_unit: Optional[UnitBaseClass] = None

        self.game_menu_state: Optional[Game] = None
        self.registered = False if not self.registered else self.register

        self.game_gui: Optional[SCivGUI] = None

        self.showing_colors = False

    def __setup__(self, base, *args, **kwargs):
        super().__setup__(*args, **kwargs)
        self._base = base
        self.registered = False
        if not self.registered:
            self.register()
            self.registered = True

    def get_gui(self) -> "SCivGUI":
        if self.game_gui is None:
            raise ValueError("GUI not initialized")
        return self.game_gui

    def get_entities(self) -> EntityManager:
        if self.game is None:
            raise AssertionError("Game not initialized")

        return self.game.entities

    def get_game(self) -> "Game":
        if self.game is None:
            raise ValueError("Game not initialized")
        return self.game

    def kivy_setup(self):
        from menus.kivy.core import SCivGUI

        self.game_gui = SCivGUI(self._base)
        self.game_gui.run()

    def register(self) -> bool:
        self._base.accept("ui.update.user.tile_clicked", self.select_tile)
        self._base.accept("game.input.user.escape_pressed", self.get_escape_menu)
        self._base.accept("f7", self.trigger_render_analyze)
        self._base.accept("p", self.activate_pstat)
        self._base.accept("l", self.deactivate_pstat)
        self._base.accept("n", self.show_colors_for_resources)
        self._base.accept("m", self.show_colors_for_water)
        self._base.accept("b", self.show_colors_for_units)
        return True

    def activate_pstat(self):
        PStatClient.connect("127.0.0.1", 5185)

    def deactivate_pstat(self):
        PStatClient.disconnect()

    def get_game_ui(self):
        # If we don't have an active Game, create one
        if self.game is None:
            messenger.send("system.game.start")
        else:
            # If we do, we're just resuming it
            messenger.send("system.game.resume")

    def get_escape_menu(self):
        self.get_gui().get_screen_manager().current = "game_ui" if self.get_game().is_paused else "pause_menu"
        self.get_game().is_paused = not self.get_game().is_paused

    def clear_selection(self):
        self.current_tiles[0].set_color(Colors.RESTORE)
        self.current_tiles = []
        self.previous_tiles = []

        if self.current_unit is not None:
            self.current_unit.set_color(Colors.RESTORE)
        self.current_unit = None
        self.previous_unit = None

    def select_tile(self, tile_coords: List[str]):
        from gameplay.repositories.tile import TileRepository

        tile = self.map.map.get(tile_coords[0])

        if tile is None:
            return

        self.previous_tile = self.current_tile
        self.current_tile = tile
        self.neighbours_tiles = []

        # Colors for selected tile and neighbors
        colors: List[Tuple[float, float, float, float]] = [Colors.GREEN, Colors.BLUE, Colors.RED]
        colors_neighbours: List[Tuple[float, float, float, float]] = [Colors.PURPLE] * 3

        self.color_tile(tile, colors)
        self.color_neighbors(tile, colors_neighbours)

        self.neighbours_tiles = TileRepository.get_neighbors(tile)

        # Restore colors of previously selected tile and neighbors
        if self.previous_tile:
            self.restore_tile_colors(self.previous_tile)
        for neighbor in self.neighbours_tiles:
            self.restore_tile_colors(neighbor)

    def color_tile(
        self,
        tile: BaseTile,
        color: Optional[Tuple[float, float, float, float] | List[Tuple[float, float, float, float]]] = None,
    ):
        if color is None:
            color = Colors.RESTORE

        if tile.owner == PlayerManager.session_player():
            tile.set_color(color if isinstance(color, tuple) else color[0])
        elif tile.owner is PlayerManager.get_nature():
            tile.set_color(color if isinstance(color, tuple) else color[1])
        else:
            tile.set_color(color if isinstance(color, tuple) else color[2])

    def color_neighbors(
        self,
        tile: BaseTile,
        color: Optional[Tuple[float, float, float, float] | List[Tuple[float, float, float, float]]] = None,
    ):
        from gameplay.repositories.tile import TileRepository

        if color is None:
            color = Colors.RESTORE

        neighbors = TileRepository.get_neighbors(tile)
        for i, _tile in enumerate(neighbors):
            _tile.set_color(color if isinstance(color, tuple) else color[i % len(color)])

        return neighbors

    def restore_tile_colors(self, tile: BaseTile):
        tile.set_color(Colors.RESTORE)

    def select_unit(self, unit: List[str] | UnitBaseClass):
        if isinstance(unit, list):
            result = self.get_entities().get(EntityType.UNIT, unit[0])
            if result is None:
                return
            object: BaseEntity | UnitBaseClass = result
        else:
            object: BaseEntity | UnitBaseClass = unit

        if self.current_tile is not None:
            self.current_tile.set_color(Colors.RESTORE)
            self.previous_tile = self.current_tile
            self.current_tile = None

        if self.current_unit is not None:
            self.previous_unit = self.current_unit
            if self.previous_unit.model is not None:
                self.previous_unit.set_color(Colors.RESTORE)

        if object is not None and isinstance(object, UnitBaseClass):
            if object.owner == PlayerManager.session_player():
                # Green for player units
                object.set_color(Colors.GREEN)
            else:
                # Red for enemy units
                object.set_color(Colors.RED)
            self.current_unit = object

    def trigger_render_analyze(self):
        self._base.render.analyze()  # type: ignore

    def show_colors_for_water(self):
        for _, hex in self.map.map.items():
            if self.showing_colors:
                hex.set_color(Colors.RESTORE)
                continue

            if hex.is_coast and hex.is_water:
                hex.set_color(Colors.TIEL)
            elif hex.is_water:
                hex.set_color(Colors.BLUE)
            elif not hex.is_water:
                hex.set_color(Colors.RED)
            else:
                hex.set_color(Colors.RESTORE)

        self.showing_colors = not self.showing_colors

    def show_colors_for_resources(self):
        for _, hex in self.map.map.items():
            if len(hex.resources) > 0:
                hex.set_color(Colors.GREEN if self.showing_colors else Colors.RESTORE)
            else:
                hex.set_color(Colors.RED if self.showing_colors else Colors.RESTORE)
        self.showing_colors = not self.showing_colors

    def show_colors_for_units(self):
        for _, hex in self.map.map.items():
            if len(hex.units) > 0:
                hex.set_color(Colors.BLUE if self.showing_colors else Colors.RESTORE)
            else:
                hex.set_color(Colors.RED if self.showing_colors else Colors.RESTORE)
        self.showing_colors = not self.showing_colors
