from typing import List, Optional
from direct.showbase.MessengerGlobal import messenger
from data.tiles.tile import Tile
from menus.game import Game
from menus.game_escape import PauseMenu
from mixins.singleton import Singleton
from managers.world import World


class ui(Singleton):
    current_menu = None

    def __init__(self, base):
        self.menus = []
        self._base = base
        self.current_menu = None
        self.game: Optional[Game] = None
        self.map: World = World.get_instance()
        self.current_tile: Optional[Tile] = None
        self.previous_tile: Optional[Tile] = None

        self.game_menu_state: Optional[Game] = None
        self.game_pause_state: Optional[PauseMenu] = None
        self.registered = False if not self.registered else self.register

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
        self._base.accept("f7", self.trigger_render_analyze)
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

    def set_current_menu(self, menu):
        self.current_menu = menu

    def get_current_menu(self):
        return self.current_menu

    def get_main_menu(self):
        from menus.primary import Primary

        self.cleanup_menu()
        self.set_current_menu(Primary().show())

    def get_secondary_menu(self):
        from menus.second import Second

        self.cleanup_menu()
        self.set_current_menu(Second().show())

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

    def select_tile(self, tile_coords: List[str]):
        tile = self.map.map.get(tile_coords[0])
        if self.current_tile is not None:
            self.previous_tile = self.current_tile
            self.previous_tile.set_color((1, 1, 1, 1))
        if tile is not None:
            tile.set_color((0, 1, 0, 1))
            self.current_tile = tile

    def trigger_render_analyze(self):
        self._base.render.analyze()
