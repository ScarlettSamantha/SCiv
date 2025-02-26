from typing import List, Optional, TYPE_CHECKING, Tuple
from direct.showbase.MessengerGlobal import messenger
from data.tiles.tile import Tile
from managers.player import PlayerManager

from mixins.singleton import Singleton
from managers.world import World
from gameplay.units.classes._base import UnitBaseClass

from panda3d.core import PStatClient


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

        self.current_tile: Optional[Tile] = None
        self.previous_tile: Optional[Tile] = None

        self.neighbours_tiles: List[Tile] = []
        self.previous_tiles: List[Tile] = []

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
        self._base.accept("f9", self.show_colors_for_resources)
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
        self.current_tiles[0].set_color((1, 1, 1, 1))
        self.current_tiles = []
        self.previous_tiles = []

        if self.current_unit is not None:
            self.current_unit.set_color((1, 1, 1, 1))
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
        colors: List[Tuple[float, float, float, float]] = [(0, 1, 0, 1), (0, 0, 1, 1), (1, 0, 0, 1)]
        colors_neighbours: List[Tuple[float, float, float, float]] = [(1, 1, 0, 1)] * 3

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
        tile: Tile,
        color: Optional[Tuple[float, float, float, float] | List[Tuple[float, float, float, float]]] = None,
    ):
        if color is None:
            color = (1, 1, 1, 1)

        if tile.owner == PlayerManager.session_player():
            tile.set_color(color if isinstance(color, tuple) else color[0])
        elif tile.owner is PlayerManager.get_nature():
            tile.set_color(color if isinstance(color, tuple) else color[1])
        else:
            tile.set_color(color if isinstance(color, tuple) else color[2])

    def color_neighbors(
        self,
        tile: Tile,
        color: Optional[Tuple[float, float, float, float] | List[Tuple[float, float, float, float]]] = None,
    ):
        from gameplay.repositories.tile import TileRepository

        if color is None:
            color = (1, 1, 1, 1)

        neighbors = TileRepository.get_neighbors(tile)
        for i, _tile in enumerate(neighbors):
            _tile.set_color(color if isinstance(color, tuple) else color[i % len(color)])

        return neighbors

    def restore_tile_colors(self, tile: Tile):
        tile.set_color((1, 1, 1, 1))

    def select_unit(self, unit: List[str] | UnitBaseClass):
        if isinstance(unit, list):
            object = UnitBaseClass.get_unit_by_tag(unit[0])
        else:
            object = unit

        if self.current_tile is not None:
            self.current_tile.set_color((1, 1, 1, 1))
            self.previous_tile = self.current_tile
            self.current_tile = None

        if self.current_unit is not None:
            self.previous_unit = self.current_unit
            if self.previous_unit.model is not None:
                self.previous_unit.set_color((1, 1, 1, 1))

        if object is not None:
            if object.owner == PlayerManager.session_player():
                # Green for player units
                object.set_color((0, 1, 0, 1))
            else:
                # Red for enemy units
                object.set_color((1, 0, 0, 1))
            self.current_unit = object

    def trigger_render_analyze(self):
        self._base.render.analyze()  # type: ignore

    def show_colors_for_resources(self):
        for _, hex in self.map.map.items():
            if hex.resource is not None:
                if self.showing_colors:
                    hex.set_color((1, 1, 1, 1))
                else:
                    hex.set_color((1, 1, 1, 0.01))

                self.showing_colors = not self.showing_colors
