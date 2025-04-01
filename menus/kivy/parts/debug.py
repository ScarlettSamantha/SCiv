from typing import TYPE_CHECKING, Any

from kivy.app import Widget
from kivy.graphics import Color, Line, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label

if TYPE_CHECKING:
    from main import SCIV


class DebugPanel(FloatLayout):
    def __init__(self, base: "SCIV", offset: int = 10, **kwargs: Any):
        super().__init__(**kwargs)
        self.base = base
        self.offset = offset  # Fixed pixel offset from the top

        self.frame = None
        self.panel = None
        self.rect = None
        self.blue_line = None  # New blue line attribute

    def get_frame(self) -> FloatLayout:
        if self.frame is None:
            self.frame = self.build_debug_frame()
        return self.frame

    def build_debug_frame(self) -> FloatLayout:
        # --- Debug Panel (Top-Left Corner) ---
        self.frame = FloatLayout(
            size_hint=(None, None),
            width=300,
            height=700,
            pos_hint={"left": 1, "top": 0.975},
        )

        # Background rectangle (canvas.before)
        with self.frame.canvas.before:  # type: ignore
            Color(0, 0, 0, 0.7)  # Black background with 70% opacity
            self.rect = Rectangle(size=self.frame.size, pos=self.frame.pos)  # type: ignore

        def update_debug_rect(instance: Widget, value: Any):
            self.rect.size = instance.size  # type: ignore
            self.rect.pos = instance.pos  # type: ignore

        self.frame.bind(size=update_debug_rect, pos=update_debug_rect)  # type: ignore

        # Blue line (canvas.after) to test something
        with self.frame.canvas.after:  # type: ignore
            Color(0, 0, 1, 1)  # Blue color
            # Draw a horizontal line across the center
            self.blue_line = Line(
                points=[self.frame.x, self.frame.center_y, self.frame.right, self.frame.center_y],  # type: ignore
                width=2,
            )

        def update_blue_line(instance: Line, value: Any):
            if self.blue_line is None:
                return

            self.blue_line.points = [  # type: ignore
                instance.x,  # type: ignore
                instance.center_y,  # type: ignore
                instance.right,  # type: ignore
                instance.center_y,  # type: ignore
            ]

        self.frame.bind(size=update_blue_line, pos=update_blue_line)

        # Debug panel label
        self.panel = Label(
            text="Debug Info: None Yet",
            size_hint=(None, None),
            width=300,
            height=700,
            font_size="11sp",
            valign="top",
            halign="left",
            text_size=(300, 700),
            pos_hint={"left": 1, "top": 1},
            color=(1, 1, 1, 1),
            padding=10,
        )

        self.frame.add_widget(self.panel)
        return self.frame

    def update_debug_info(self, text: str):
        if self.panel is None:
            return
        self.panel.text = text
