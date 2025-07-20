from typing import Any, Optional

from direct.showbase.DirectObject import DirectObject
from gameplay.civilization import Civilization
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen
from menus.kivy.elements.image_label import ImageLabel
from menus.kivy.elements.loading_screen import LoadingScreen


class Loading(
    Screen,
    DirectObject,
):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

        self.loading_screen: Optional[LoadingScreen] = None
        self.build_screen()
        self.register()
        self.civilization: Optional[Civilization] = None

    def register(self) -> None:
        self.accept("ui.loading.show", self.show)
        self.accept("ui.loading.next_step", self.next_stage)

    def next_stage(self, message: str):
        self.loading_screen.next_step(message)  # type: ignore

    def on_done(self):
        self.manager.current = "game_ui"
        self.hide()

    def build_screen(self):
        pass

    def hide(self, _: Optional[Button] = None):
        self.visible = False  # type: ignore

    def show(self, *args: Any, **kwargs: Any):
        self.loading_screen = LoadingScreen(total_steps=6, show_continue=True, on_complete=self.on_done)
        self.loading_screen.add_to_right_overlay(self.right_text_widget())
        self.add_widget(self.loading_screen)
        self.visible = True  # type: ignore

    def set_civilization(self, civ: Civilization):
        self.civilization = civ

    def right_text_widget(self) -> ImageLabel:
        if self.civilization is None:
            raise ValueError("Civilization not set for Loading screen")

        civ: Civilization = self.civilization

        text_element = ImageLabel(str(civ.icon), str(civ.introduction), text_color=(1, 1, 1, 1), font_size=20, top=1)

        return text_element
