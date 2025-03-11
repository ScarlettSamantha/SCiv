from typing import TYPE_CHECKING, Any, Dict, Optional

from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from panda3d.core import GraphicsWindow, WindowProperties

from camera import CivCamera
from managers.entity import EntityManager

if TYPE_CHECKING:
    from direct.showbase.ShowBase import ShowBase

    from main import Openciv


class StatsPanel(FloatLayout):
    def __init__(self, base: "Openciv | ShowBase", **kwargs):
        super().__init__(**kwargs)
        self.base: "Openciv | ShowBase" = base
        self.camera: CivCamera = CivCamera.get_instance()

        self.frame: Optional[FloatLayout] = None
        self.label: Optional[Label] = None
        self.rect: Optional[Rectangle] = None

        self.entity_manager: EntityManager = EntityManager.get_instance()

        # These are just for type hinting
        self.window: "GraphicsWindow" = self.base.win
        self.window_properties: WindowProperties = self.window.properties

        self._periodicals: Dict[str, Any] = {
            "window_size": f"{self.window.getXSize()},{self.base.win.getYSize()}",
            "window_pos": f"{self.window_properties.getXOrigin()},{self.window_properties.getYOrigin()}",
            "entity_manager_entities_total": 0,
            "entity_manager_entities_orphans": 0,
            "entity_manager_total_players": 0,
            "entity_manager_total_units": 0,
            "entity_manager_total_tiles": 0,
        }

        self.register()

    def get_frame(self) -> FloatLayout:
        if self.frame is None:
            self.frame = self.build()
        return self.frame

    def register(self):
        def clocks():
            Clock.schedule_interval(self.on_update, 0.25)
            Clock.schedule_interval(self.periodicals, 1)

        clocks()

    def hide(self):
        if self.frame is not None:
            self.frame.opacity = 0

    def periodicals(self, dt):
        self._periodicals["window_size"] = (f"{self.base.win.getXSize()},{self.base.win.getYSize()}",)
        self._periodicals["window_pos"] = (
            f"{self.base.win.properties.getXOrigin()},{self.base.win.properties.getYOrigin()}",
        )

        self.entity_manager.calculate_stats()
        entity_stats = self.entity_manager.stats

        self._periodicals["entity_manager_entities_total"] = entity_stats["total_entities"]
        self._periodicals["entity_manager_entities_orphans"] = entity_stats["total_orphan_entities"]

        self._periodicals["entity_manager_total_players"] = entity_stats["total_players"]
        self._periodicals["entity_manager_total_units"] = entity_stats["total_units"]
        self._periodicals["entity_manager_total_tiles"] = entity_stats["total_tiles"]

    def build(self) -> FloatLayout:
        # --- Camera Panel (Top-Right Corner) ---
        self.frame = FloatLayout(
            size_hint=(None, None),
            width=200,
            height=300,
            pos_hint={"right": 1, "top": 0.975},
        )

        with self.frame.canvas.before:  # type: ignore
            Color(0, 0, 0, 0.8)
            self.rect = Rectangle(size=self.frame.size, pos=self.frame.pos)

        def update_camera_rect(instance, value):
            if self.rect is None:
                return

            self.rect.size = instance.size
            self.rect.pos = instance.pos

        self.frame.bind(size=update_camera_rect, pos=update_camera_rect)

        self.label = Label(
            text="Camera Info:\nZoom: 1.0\nAngle: 45°",
            size_hint=(None, None),
            width=200,
            height=300,
            font_size="11sp",
            valign="top",
            halign="right",
            text_size=(200, 300),
            pos_hint={"right": 1, "top": 1},
            color=(1, 1, 1, 1),
            padding=10,
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
            "--Entity Info:--",
            f"Entities: {str(self._periodicals['entity_manager_entities_total'])}",
            f"Orphans: {str(self._periodicals['entity_manager_entities_orphans'])}",
            f"Players: {str(self._periodicals['entity_manager_total_players'])}",
            f"Units: {str(self._periodicals['entity_manager_total_units'])}",
            f"Tiles: {str(self._periodicals['entity_manager_total_tiles'])}",
        )
        self.label.text = "\n".join(text)  # type: ignore # We know it exists because it's initialized in build_screen
