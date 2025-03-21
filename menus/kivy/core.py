from typing import Optional

from kivy.uix.screenmanager import ScreenManager
from panda3d_kivy.app import App

from menus.screens.game_config import GameConfigMenu
from menus.screens.game_ui import GameUIScreen
from menus.screens.main_menu import MainMenuScreen
from menus.screens.options_menu import OptionsScreen
from menus.screens.pause_menu import PauseScreen
from menus.screens.save_load import SaveLoadScreen


class SCivGUI(App):
    def __init__(self, panda_app, display_region=None, **kwargs):
        self.screen_manager: Optional[ScreenManager] = None
        self._base = panda_app
        self.is_build: bool = False
        super().__init__(panda_app, display_region, **kwargs)

    def setup(self):
        pass

    def get_screen_manager(self) -> ScreenManager:
        if self.screen_manager is None:
            self.screen_manager = self.build()
        return self.screen_manager  # type: ignore

    def set_screen(self, screen_name: str) -> None:
        self.get_screen_manager().current = screen_name

    def get_screen(self, screen_name: str):
        return self.get_screen_manager().get_screen(screen_name)

    def build(self, default_screen: str = "main_menu"):
        screen_manager = ScreenManager()
        screen_manager.add_widget(MainMenuScreen(name="main_menu"))
        screen_manager.add_widget(GameConfigMenu(name="game_config_screen"))
        screen_manager.add_widget(GameUIScreen(name="game_ui", base=self._base))
        screen_manager.add_widget(OptionsScreen(name="options_screen"))
        screen_manager.add_widget(PauseScreen(name="pause_menu", base=self._base))
        screen_manager.add_widget(SaveLoadScreen(name="save_load_screen", base=self._base))
        screen_manager.current = default_screen
        self.is_build = True
        return screen_manager

    def debug_ui_state(self, stats: bool, actions: bool, debug: bool) -> None:
        screen: GameUIScreen = self.get_screen_manager().get_screen("game_ui")
        screen.toggle_debug_panels(stats, actions, debug)
