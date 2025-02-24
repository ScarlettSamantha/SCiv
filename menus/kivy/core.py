from typing import Optional
from panda3d_kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager

from menus.screens.main_menu import MainMenuScreen
from menus.screens.game_config import GameConfigScreen
from menus.screens.pause_menu import PauseMenu
from menus.screens.options_menu import OptionsScreen


class SCivGUI(App):
    def __init__(self, panda_app, display_region=None, **kwargs):
        self.screen_manager: Optional[ScreenManager] = None
        self._base = panda_app
        super().__init__(panda_app, display_region, **kwargs)

    def setup(self):
        pass

    def get_screen_manager(self) -> Optional[ScreenManager]:
        return self.screen_manager or None

    def build(self):
        screen_manager = ScreenManager()
        screen_manager.add_widget(MainMenuScreen(name="main_menu"))
        screen_manager.add_widget(GameConfigScreen(name="game_config_screen"))
        screen_manager.add_widget(OptionsScreen(name="options_screen"))
        screen_manager.add_widget(PauseMenu(name="pause_menu"))
        screen_manager.current = "main_menu"
        return screen_manager
