from typing import TYPE_CHECKING

from kivy.uix.screenmanager import Screen

from menus.kivy.parts.load import LoadPopup
from menus.kivy.parts.save import SavePopup

if TYPE_CHECKING:
    from main import SCIV


class SaveLoadScreen(Screen):
    def __init__(self, base: "SCIV", **kwargs):
        super().__init__(**kwargs)
        self.base: "SCIV" = base

        self.save_menu = SavePopup(base=base)

        self.load_menu = LoadPopup(base=base)

        self.showing_save: bool = False
        self.showing_load: bool = False

    def show_save_menu(self):
        self.showing_save = True
        self.save_menu.open_popup()

    def show_load_menu(self):
        self.showing_load = True
        self.load_menu.open_popup()

    def hide_save_menu(self):
        self.showing_save = False
        self.save_menu.close_popup()

    def hide_load_menu(self):
        self.showing_load = False
        self.load_menu.close_popup()
