from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle


class DebugPanel(FloatLayout):
    def __init__(self, base, **kwargs):
        super().__init__(**kwargs)
        self.base = base

        self.frame = None
        self.panel = None
        self.rect = None

    def get_frame(self) -> FloatLayout:
        if self.frame is None:
            self.frame = self.build_debug_frame()
        return self.frame

    def build_debug_frame(self) -> FloatLayout:
        # --- Debug Panel (Top-Left Corner) ---
        self.frame = FloatLayout(
            size_hint=(None, None),
            width=300,
            height=500,
            pos_hint={"x": 0, "top": 1},
        )

        with self.frame.canvas.before:  # type: ignore
            Color(0, 0, 0, 0.7)  # Black background with 70% opacity
            self.rect = Rectangle(size=self.frame.size, pos=self.frame.pos)

        def update_debug_rect(instance, value):
            self.rect.size = instance.size  # type: ignore
            self.rect.pos = instance.pos  # type: ignore

        self.frame.bind(size=update_debug_rect, pos=update_debug_rect)  # type: ignore

        self.panel = Label(
            text="Debug Info: None Yet",
            size_hint=(None, None),
            width=300,
            height=500,
            font_size="11sp",
            valign="top",
            halign="left",
            text_size=(300, 500),
            pos_hint={"x": 0, "top": 1},
            color=(1, 1, 1, 1),
        )

        self.frame.add_widget(self.panel)
        return self.frame

    def update_debug_info(self, text: str):
        self.panel.text = text  # type: ignore
