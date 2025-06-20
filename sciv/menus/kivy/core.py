from typing import Any, Optional

from direct.showbase.DirectObject import DirectObject
from kivy.uix.screenmanager import ScreenManager
from panda3d_kivy.app import App


from gameplay.civilization import Civilization
from game import SCIV
from menus.screens import loading
from menus.screens.game_config import GameConfigMenu
from menus.screens.game_ui import GameUIScreen
from menus.screens.main_menu import MainMenuScreen
from menus.screens.options_menu import OptionsScreen
from menus.screens.pause_menu import PauseScreen
from menus.screens.save_load import SaveLoadScreen


class SCivGUI(App, DirectObject):
    def __init__(self, panda_app: SCIV, **kwargs: Any):
        self._base: "SCIV" = panda_app
        self.is_build: bool = False
        super().__init__(panda_app, **kwargs)  # type: ignore
        self.screen_manager: Optional[ScreenManager] = None
        self.game_ui_screen: Optional[GameUIScreen] = None

        self.register()

    def register(self):
        self.accept("ui.request.loading_screen", self.activate_loading_screen)

    def get_screen_manager(self) -> ScreenManager:
        if self.screen_manager is None:
            self.build()
        return self.screen_manager  # type: ignore

    def reset(self):
        if self.screen_manager is None:
            return
        self.screen_manager.remove_widget(self.game_ui_screen)  # type: ignore
        self.game_ui_screen.destroy()  # type: ignore
        self.screen_manager.current = "pause_menu"  # type: ignore
        del self.game_ui_screen
        self.game_ui_screen = GameUIScreen(name="game_ui", base=self._base)
        self.screen_manager.add_widget(self.game_ui_screen)  # type: ignore
        self.screen_manager.current = "game_ui"  # type: ignore

    def set_screen(self, screen_name: str) -> None:
        self.get_screen_manager().current = screen_name

    def get_screen(self, screen_name: str) -> Any:
        return self.get_screen_manager().get_screen(screen_name)  # type: ignore

    def load_game_ui(self):
        if self.screen_manager is None:
            self.screen_manager = self.build()
        self.screen_manager.get_screen("save_load_screen").hide_save_menu()  # type: ignore
        self.screen_manager.get_screen("save_load_screen").hide_load_menu()  # type: ignore
        game_ui: GameUIScreen = self.screen_manager.get_screen("game_ui")  # type: ignore
        self.screen_manager.current = "game_ui"

    def load_main_menu(self):
        if self.screen_manager is None:
            self.screen_manager = self.build()
        self.screen_manager.get_screen("main_menu").show()  # type: ignore
        self.screen_manager.current = "main_menu"

    def activate_loading_screen(self, civilization: Optional[Civilization] = None) -> None:
        if self.screen_manager is None:
            self.screen_manager = self.build()

        if civilization is not None:
            self.screen_manager.get_screen("loading_screen").set_civilization(civilization)  # type: ignore

        self.screen_manager.get_screen("loading_screen").show()  # type: ignore
        self.screen_manager.current = "loading_screen"

    def build(self, default_screen: str = "main_menu"):
        screen_manager = ScreenManager()

        self.game_ui_screen = GameUIScreen(name="game_ui", base=self._base)  # type: ignore

        screen_manager.add_widget(MainMenuScreen(name="main_menu"))  # type: ignore
        screen_manager.add_widget(GameConfigMenu(name="game_config_screen"))  # type: ignore
        screen_manager.add_widget(loading.Loading(name="loading_screen"))  # type: ignore
        screen_manager.add_widget(self.game_ui_screen)  # type: ignore
        screen_manager.add_widget(OptionsScreen(name="options_screen"))  # type: ignore
        screen_manager.add_widget(PauseScreen(name="pause_menu", base=self._base))  # type: ignore
        screen_manager.add_widget(SaveLoadScreen(name="save_load_screen", base=self._base))  # type: ignore
        screen_manager.current = default_screen
        self.screen_manager = screen_manager
        self.is_build = True
        return screen_manager

    def debug_ui_state(self, stats: bool, actions: bool, debug: bool) -> None:
        screen: GameUIScreen = self.get_screen_manager().get_screen("game_ui")  # type: ignore
        screen.toggle_debug_panels(stats, actions, debug)  # type: ignore
