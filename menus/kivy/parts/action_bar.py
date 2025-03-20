from typing import Optional

from direct.showbase.DirectObject import DirectObject
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout


class ActionBar(BoxLayout, DirectObject):
    def __init__(self, *args, **kwargs):
        self.background_color = (0, 0, 0, 1)
        self.border = (1, 1, 1, 1)
        self.background_image = ""
        super().__init__(*args, **kwargs)  # type: ignore # This is a false positive
        self.frame: Optional[GridLayout] = None

    def build(self) -> GridLayout:
        self.frame = GridLayout(  # noqa: F821
            orientation="lr-tb",
            size_hint=(None, None),
            width=1000,
            height=80,
            spacing=10,
            pos_hint={"center_x": 0.5, "y": 0},
            cols=12,
            rows=1,
        )
        return self.frame

    def get_frame(self) -> GridLayout:
        if not self.frame:
            raise ValueError("Action Bar frame has not been built yet.")
        return self.frame

    def add_button(self, button: Button):
        self.get_frame().add_widget(button)
        return button

    def remove_button(self, button: Button):
        self.get_frame().remove_widget(button)
        return button

    def clear_buttons(self):
        self.get_frame().clear_widgets()
        return self.frame
