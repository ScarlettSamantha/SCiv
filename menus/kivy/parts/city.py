from typing import Optional

from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label


class CityUI(BoxLayout):
    def __init__(self, base, name, background_color=(0, 0, 0, 0), border=(0, 0, 0, 0), **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.pos_hint = {"x": 0, "center_y": 0.5}  # Align left & center vertically
        self.size_hint = (0.3, 0.2)  # type: ignore # Ensure fixed width and height
        self.background_color = (0, 0, 0, 1)  # Black background
        self.width = 800  # Explicitly set width
        self.height = 600  # Explicitly set height
        self.background_color = background_color
        self.border = border
        self.background_image = None
        self.base = base
        self.frame: Optional[BoxLayout] = None
        self.hidden: bool = False
        self.city_name = name
        self.add_widget(self.build())

    def build(self) -> BoxLayout:
        self.background_color = (0, 0, 0, 1)  # Black background

        # Main container (background black box)
        self.frame = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            width=400,
            height=600,
            padding=10,
            spacing=10,
            pos_hint={"right": 1, "center_y": 0.5},
        )

        with self.frame.canvas.before:  # type: ignore
            Color(0, 0, 0, 0.7)  # Black background with 70% opacity
            self.rect = Rectangle(size=self.frame.size, pos=self.frame.pos)

        def update_debug_rect(instance, value):
            self.rect.size = instance.size  # type: ignore
            self.rect.pos = instance.pos  # type: ignore

        self.frame.bind(size=update_debug_rect, pos=update_debug_rect)

        # City name label (Top)
        self.city_label = Label(text=self.city_name, size_hint=(1, None), height=50, bold=True, font_size=24)
        self.frame.add_widget(self.city_label)

        # Vertical button stack (Middle section)
        self.button_container = BoxLayout(orientation="vertical", size_hint=(1, 1), spacing=5)
        for i in range(5):  # Dummy buttons
            btn = Button(text=f"Action {i + 1}", size_hint=(1, None), height=50)
            self.button_container.add_widget(btn)

        self.frame.add_widget(self.button_container)

        # Footer (Bottom section)
        self.footer = BoxLayout(orientation="horizontal", size_hint=(1, None), height=80, spacing=10)
        self.frame.add_widget(self.footer)
        return self.frame

    def show(self):
        """Makes the City View visible."""
        if self.frame is None:
            raise AssertionError("City view has not been built yet.")

        self.frame.opacity = 1
        self.frame.disabled = False
        self.hidden = False

    def hide(self):
        """Hides the City View."""
        if self.frame is None:
            raise AssertionError("City view has not been built yet.")

        self.frame.opacity = 0
        self.frame.disabled = True
        self.hidden = True

    def is_hidden(self) -> bool:
        """Returns True if the City View is hidden."""
        return self.hidden
