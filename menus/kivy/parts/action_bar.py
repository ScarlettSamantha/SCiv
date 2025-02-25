from typing import Optional, Callable
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button


class ActionBar(BoxLayout):
    def __init__(self, base, background_color=(0, 0, 0, 0), border=(0, 0, 0, 0), **kwargs):
        self.background_color = background_color
        self.border = border
        self.background_image = None
        super().__init__(**kwargs)
        self.base = base
        self.frame: Optional[BoxLayout] = None

    def build(self) -> BoxLayout:
        # --- Action Bar (Bottom Centered) ---
        self.frame = BoxLayout(
            orientation="horizontal",
            size_hint=(None, None),
            width=1000,
            height=80,
            spacing=10,
            pos_hint={"center_x": 0.5, "y": 0},
        )
        return self.frame

    def get_frame(self) -> BoxLayout:
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
