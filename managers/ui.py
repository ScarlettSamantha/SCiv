from typing import List, Optional, TYPE_CHECKING
from direct.showbase.MessengerGlobal import messenger
from data.tiles.tile import Tile
from managers.player import PlayerManager
from menus.game import Game
from menus.game_escape import PauseMenu
from mixins.singleton import Singleton
from managers.world import World
from gameplay.units.classes._base import UnitBaseClass
from panda3d_kivy.app import App


if TYPE_CHECKING:
    from main import Openciv


class ui(Singleton):
    current_menu = None

    def __init__(self, base):
        self.menus = []
        self._base: Openciv = base
        self.current_menu = None
        self.game: Optional[Game] = None
        self.map: World = World.get_instance()

        self.current_tile: Optional[Tile] = None
        self.previous_tile: Optional[Tile] = None

        self.current_unit: Optional[UnitBaseClass] = None
        self.previous_unit: Optional[UnitBaseClass] = None

        self.game_menu_state: Optional[Game] = None
        self.game_pause_state: Optional[PauseMenu] = None
        self.registered = False if not self.registered else self.register
        self.kivy: Optional[App] = None

        self.showing_colors = False

    def __setup__(self, base, *args, **kwargs):
        super().__setup__(*args, **kwargs)
        self._base = base
        self.registered = False
        if not self.registered:
            self.register()
            self.registered = True

    def register(self) -> bool:
        self._base.accept("ui.update.user.tile_clicked", self.select_tile)
        self._base.accept("game.input.user.escape_pressed", self.get_escape_menu)
        self._base.accept("system.game.start", self.on_game_start)
        self._base.accept("f7", self.trigger_render_analyze)
        self._base.accept("f9", self.show_colors_for_resources)
        return True

    def cleanup_menu(self):
        # Only destroy if it's not the Game object.
        # For the game, we simply hide it instead, preserving state.
        if self.current_menu:
            if isinstance(self.current_menu, PauseMenu):
                # Hide the game menu instead of destroying it, so state is preserved
                self.current_menu.hide()
            else:
                self.current_menu.destroy()
            self.current_menu = None

    def on_game_start(self):
        self.game_menu_show()

    def game_menu_show(self):
        from menus.game_ui import GameUI

        display_region = self._base.win.make_display_region(0, 1, 0, 1)
        self.kivy = GameUI(self._base, display_region, game_manager=self)
        self.kivy.run()

    def set_current_menu(self, menu):
        self.current_menu = menu

    def get_current_menu(self):
        return self.current_menu

    def get_main_menu(self):
        from menus.primary import Primary

        self.cleanup_menu()
        self.set_current_menu(Primary(self._base).show())

    def get_secondary_menu(self):
        from menus.second import Second

        self.cleanup_menu()
        self.set_current_menu(Second(self._base).show())

    def get_game_ui(self):
        from menus.game import Game

        # If we don't have an active Game, create one
        if self.game is None:
            self.game = Game(self._base)
            self.game.register()
            messenger.send("system.game.start")
        else:
            # If we do, we're just resuming it
            messenger.send("system.game.resume")

        # Show the (existing or new) game UI
        self.cleanup_menu()  # This will hide any previous menu but won't destroy the game
        self.set_current_menu(self.game.show())

    def get_escape_menu(self):
        from menus.game_escape import PauseMenu

        if self.game_pause_state is None:
            self.game_pause_state = PauseMenu(self._base)
            self.game_pause_state.show()
        elif self.game_pause_state is not None and self.game_pause_state.is_hidden():
            self.game_pause_state.show()
        else:
            self.game_pause_state.hide()

    def hide_escape_menu(self):
        if self.game_pause_state:
            self.game_pause_state.hide()

    def clear_selection(self):
        if self.current_tile is not None:
            self.current_tile.set_color((1, 1, 1, 1))
        self.current_tile = None
        self.previous_tile = None

        if self.current_unit is not None:
            self.current_unit.set_color((1, 1, 1, 1))
        self.current_unit = None
        self.previous_unit = None

    def select_tile(self, tile_coords: List[str]):
        tile = self.map.map.get(tile_coords[0])

        if self.current_unit is not None:
            self.current_unit.set_color((1, 1, 1, 1))
            self.previous_unit = self.current_unit
            self.current_unit = None

        if self.current_tile is not None:
            self.previous_tile = self.current_tile
            self.previous_tile.set_color((1, 1, 1, 1))

        if tile is not None:
            if tile.owner == PlayerManager.session_player():
                # Own Tile
                tile.set_color((0, 1, 0, 0.01))
            elif tile.owner is PlayerManager.get_nature():
                # Nature tile
                tile.set_color((0, 0, 1, 0.01))
            else:
                # Enemy tile
                tile.set_color((1, 0, 0, 0.01))
            self.current_tile = tile

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
