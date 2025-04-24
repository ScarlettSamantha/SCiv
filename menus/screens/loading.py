from typing import Any, Optional

from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen

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

    def register(self):
        self.accept("ui.loading.next_step", self.next_stage)

    def next_stage(self, message: str):
        self.loading_screen.next_step(message)  # type: ignore
        MessengerGlobal.messenger.send("ui.refresh.frame_insert")

    def on_done(self):
        self.manager.current = "game_ui"
        self.hide()

    def build_screen(self):
        pass

    def hide(self, _: Optional[Button] = None):
        self.visible = False  # type: ignore

    def show(self):
        self.loading_screen = LoadingScreen(total_steps=6, show_continue=True, on_complete=self.on_done)
        self.add_widget(self.loading_screen)
        self.visible = True  # type: ignore
