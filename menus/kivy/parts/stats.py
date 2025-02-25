from typing import Optional
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle

from kivy.clock import Clock
from camera import CivCamera


class StatsPanel(FloatLayout):
    def __init__(self, base, **kwargs):
        super().__init__(**kwargs)
        self.base = base
        self.camera: CivCamera = CivCamera.get_instance()

        self.frame: Optional[FloatLayout] = None
        self.label: Optional[Label] = None
        self.rect: Optional[Rectangle] = None

        self.register()

    def register(self):
        Clock.schedule_interval(self.on_update, 0.25)

    def build(self) -> FloatLayout:
        # --- Camera Panel (Top-Right Corner) ---
        self.frame = FloatLayout(
            size_hint=(None, None),
            width=200,
            height=200,
            pos_hint={"right": 1, "top": 1},
        )

        with self.frame.canvas.before:  # type: ignore
            Color(0, 0, 0, 0.5)  # Black background with 50% opacity
            self.rect = Rectangle(size=self.frame.size, pos=self.frame.pos)

        def update_camera_rect(instance, value):
            self.rect.size = instance.size  # type: ignore
            self.rect.pos = instance.pos  # type: ignore

        self.frame.bind(size=update_camera_rect, pos=update_camera_rect)  # type: ignore

        self.label = Label(
            text="Camera Info:\nZoom: 1.0\nAngle: 45°",
            size_hint=(None, None),
            width=200,
            height=100,
            font_size="11sp",
            valign="top",
            halign="right",
            text_size=(200, 100),
            pos_hint={"right": 1, "top": 1},
            color=(1, 1, 1, 1),
        )

        self.frame.add_widget(self.label)
        return self.frame

    def on_update(self, dt):
        fps = self.base.clock.getAverageFrameRate()
        text = f"FPS: {fps:.2f}\nYaw: {self.camera.yaw}\nPOS: {self.camera.getPos()} \nHPR: {self.camera.getHpr()} \n"
        self.label.text = text  # type: ignore # We know it exists because it's initialized in build_screen
