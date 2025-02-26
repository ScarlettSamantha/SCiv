from typing import Optional
from panda3d_kivy.app import App

from kivy.uix.screenmanager import ScreenManager

from menus.screens.main_menu import MainMenuScreen
from menus.screens.game_config import GameConfigMenu
from menus.screens.pause_menu import PauseScreen
from menus.screens.options_menu import OptionsScreen
from menus.screens.game_ui import GameUIScreen


class SCivGUI(App):
    def __init__(self, panda_app, display_region=None, **kwargs):
        self.screen_manager: Optional[ScreenManager] = None
        self._base = panda_app
        super().__init__(panda_app, display_region, **kwargs)

    def setup(self):
        pass

    def get_screen_manager(self) -> ScreenManager:
        if self.screen_manager is None:
            self.screen_manager = self.build()
        return self.screen_manager

    def build(self):
        screen_manager = ScreenManager()
        screen_manager.add_widget(MainMenuScreen(name="main_menu"))
        screen_manager.add_widget(GameConfigMenu(name="game_config_screen"))
        screen_manager.add_widget(GameUIScreen(name="game_ui", base=self._base))
        screen_manager.add_widget(OptionsScreen(name="options_screen"))
        screen_manager.add_widget(PauseScreen(name="pause_menu"))
        screen_manager.current = "main_menu"
        return screen_manager
