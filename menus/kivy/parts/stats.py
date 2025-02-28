from typing import Any, Dict, Optional, TYPE_CHECKING
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle

from kivy.clock import Clock
from camera import CivCamera
from panda3d.core import GraphicsWindow, WindowProperties

if TYPE_CHECKING:
    from main import Openciv
    from direct.showbase.ShowBase import ShowBase


class StatsPanel(FloatLayout):
    def __init__(self, base: "Openciv | ShowBase", **kwargs):
        super().__init__(**kwargs)
        self.base: "Openciv | ShowBase" = base
        self.camera: CivCamera = CivCamera.get_instance()

        self.frame: Optional[FloatLayout] = None
        self.label: Optional[Label] = None
        self.rect: Optional[Rectangle] = None

        # These are just for type hinting
        self.window: "GraphicsWindow" = self.base.win
        self.window_properties: WindowProperties = self.window.properties

        self._periodicals: Dict[str, Any] = {
            "window_size": f"{self.window.getXSize()},{self.base.win.getYSize()}",
            "window_pos": f"{self.window_properties.getXOrigin()},{self.window_properties.getYOrigin()}",
        }

        self.register()

    def register(self):
        def clocks():
            Clock.schedule_interval(self.on_update, 0.25)
            Clock.schedule_interval(self.periodicals, 1)

        clocks()

    def periodicals(self, dt):
        self._periodicals["window_size"] = (f"{self.base.win.getXSize()},{self.base.win.getYSize()}",)
        self._periodicals["window_pos"] = (
            f"{self.base.win.properties.getXOrigin()},{self.base.win.properties.getYOrigin()}",
        )

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
            height=150,
            font_size="11sp",
            valign="top",
            halign="right",
            text_size=(200, 150),
            pos_hint={"right": 1, "top": 1},
            color=(1, 1, 1, 1),
        )

        self.frame.add_widget(self.label)
        return self.frame

    def on_update(self, dt):
        fps = self.base.clock.getAverageFrameRate()
        text = (
            f"FPS: {fps:.2f}",
            f"Yaw: {self.camera.yaw}",
            f"POS: {self.camera.getPos()}",
            f"HPR: {self.camera.getHpr()}",
            "--Periodicals:--",
            f"Window_size(x,y): {self._periodicals['window_size'][0]}",
            f"Window_Pos(top-left): {self._periodicals['window_pos'][0]}",
        )
        self.label.text = "\n".join(text)  # type: ignore # We know it exists because it's initialized in build_screen
