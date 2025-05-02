from typing import TYPE_CHECKING, Any, Dict, Optional, List

from kivy.app import Widget
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from panda3d.core import GraphicsWindow, WindowProperties
from direct.task.Task import Task
from direct.showbase.DirectObject import DirectObject
from managers.entity import EntityManager
from menus.kivy.elements.scrolling_graph import ScrollingGraph
from system.camera import Camera

if TYPE_CHECKING:
    from direct.showbase.ShowBase import ShowBase

    from main import SCIV


class StatsPanel(FloatLayout, DirectObject):  # type: ignore
    def __init__(self, base: "SCIV | ShowBase", **kwargs: Any):
        FloatLayout.__init__(self, **kwargs)
        DirectObject.__init__(self, **kwargs)  # type: ignore
        self.base: "SCIV | ShowBase" = base
        self.camera: Camera = Camera.get_singleton_instance()

        self.frame: Optional[FloatLayout] = None
        self.label: Optional[Label] = None
        self.rect: Optional[Rectangle] = None
        self.fps_graph: Optional[ScrollingGraph] = None

        # Buffer for per-frame dt samples
        self.frame_times: List[float] = []

        self.entity_manager: EntityManager = EntityManager.get_singleton_instance()

        # These are just for type hinting
        self.window: "GraphicsWindow" = self.base.win  # type: ignore
        self.window_properties: WindowProperties = self.window.properties  # type: ignore

        self._periodicals: Dict[str, Any] = {
            "window_size": f"{self.window.getXSize()},{self.base.win.getYSize()}",  # type: ignore
            "window_pos": f"{self.window_properties.getXOrigin()},{self.window_properties.getYOrigin()}",  # type: ignore
            "entity_manager_entities_total": 0,
            "entity_manager_entities_orphans": 0,
            "entity_manager_total_players": 0,
            "entity_manager_total_units": 0,
            "entity_manager_total_tiles": 0,
            "entity_manager_total_effects": 0,
        }

        self.register()

    def get_frame(self) -> FloatLayout:
        if self.frame is None:
            self.frame = self.build()
        return self.frame

    def start_graph(self):
        if self.fps_graph is None:
            return
        Clock.schedule_once(lambda _: self.fps_graph.start(), 0.1)  # type: ignore we start the graph after a short delay so it does not include the time it takes to load the game

    def stop_graph(self):
        if self.fps_graph is None:
            return
        self.fps_graph.stop()  # type: ignore

    def reset_graph(self):
        if self.fps_graph is None:
            return
        self.stop_graph()
        self.fps_graph.clear_widgets()

    def register(self):
        # Schedule updates and sampling
        Clock.schedule_interval(self.on_update, 1 / 5)
        Clock.schedule_interval(self.periodicals, 1)
        self.accept("game.state.true_game_start", self.start_graph)
        self.accept("game.state.reset_start", self.reset_graph)
        # Sample every rendered frame for dt
        if hasattr(self.base, "taskMgr"):
            self.base.taskMgr.add(self._sample_frame_time, "StatsPanelFrameTimeSampler")

    def _sample_frame_time(self, task: Task) -> Any:
        # Called once per frame by Panda3D
        dt: float = self.base.clock.getDt()  # type: ignore
        self.frame_times.append(dt)  # type: ignore
        # Keep history bounded (e.g. 5x graph points)
        if self.fps_graph:
            max_samples = self.fps_graph.max_points * 5
        else:
            max_samples = 1000
        if len(self.frame_times) > max_samples:
            self.frame_times = self.frame_times[-max_samples:]
        return task.cont

    def hide(self):
        if self.frame is not None:
            self.frame.opacity = 0

    def periodicals(self, dt: float):
        self._periodicals["window_size"] = (f"{self.base.win.getXSize()},{self.base.win.getYSize()}",)  # type: ignore
        self._periodicals["window_pos"] = (
            f"{self.base.win.properties.getXOrigin()},{self.base.win.properties.getYOrigin()}",  # type: ignore
        )

        self.entity_manager.calculate_stats()
        entity_stats = self.entity_manager.stats

        self._periodicals["entity_manager_entities_total"] = entity_stats["total_entities"]
        self._periodicals["entity_manager_entities_orphans"] = entity_stats["total_orphan_entities"]

        self._periodicals["entity_manager_total_players"] = entity_stats["total_players"]
        self._periodicals["entity_manager_total_units"] = entity_stats["total_units"]
        self._periodicals["entity_manager_total_tiles"] = entity_stats["total_tiles"]
        self._periodicals["entity_manager_total_effects"] = entity_stats["total_effects"]

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
            self.rect = Rectangle(size=self.frame.size, pos=self.frame.pos)  # type: ignore

        def update_camera_rect(instance: Widget, value: Any):
            if self.rect is None:
                return

            self.rect.size = instance.size
            self.rect.pos = instance.pos  # type: ignore

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
            markup=True,
        )

        self.fps_graph = ScrollingGraph(
            size_hint=(None, None),
            size=(300, 150),
            pos_hint={"right": 0.0, "top": 0.95},
            max_points=300,
            y_max=70.0,
        )

        self.frame.add_widget(self.label)
        self.frame.add_widget(self.fps_graph)
        return self.frame

    def on_update(self, dt: float) -> None:
        # Compute FPS and 1% low
        fps = float(self.base.clock.getAverageFrameRate())  # type: ignore
        fps_low1 = 0.0
        if self.frame_times:
            sorted_dt = sorted(self.frame_times)
            idx = max(0, int(len(sorted_dt) * 0.99) - 1)
            dt99 = sorted_dt[idx]
            fps_low1 = (1.0 / dt99) if dt99 > 0 else 0.0

        # Compute true per-frame ms from samples
        if self.frame_times:
            avg_dt = sum(self.frame_times) / len(self.frame_times)
            frame_ms = avg_dt * 1000.0
            self.frame_times.clear()
        else:
            frame_ms = dt * 1000.0

        # Update graph and label
        if self.fps_graph:
            self.fps_graph.update_graph(fps, 0.0, fps_low1, frame_ms)

        # Refresh text info
        parts = [
            f"[color=00ff00]FPS: {fps:.2f}[/color]",
            f"[color=ffff00]1% Low FPS: {fps_low1:.2f}[/color]",
            f"[color=0000ff]Frame Time: {frame_ms:.2f} ms[/color]",
            f"Yaw: {self.camera.yaw}",
            f"POS: {self.camera.getPos()}",
            f"HPR: {self.camera.getHpr()}",
            "--Periodicals:--",
            f"Window_size(x,y): {self._periodicals['window_size']}",
            f"Window_Pos(top-left): {self._periodicals['window_pos']}",
            "--Entity Info:--",
            f"Entities: {self._periodicals['entity_manager_entities_total']}",
            f"Orphans: {self._periodicals['entity_manager_entities_orphans']}",
            f"Players: {self._periodicals['entity_manager_total_players']}",
            f"Units: {self._periodicals['entity_manager_total_units']}",
            f"Tiles: {self._periodicals['entity_manager_total_tiles']}",
            f"Effects: {self._periodicals['entity_manager_total_effects']}",
        ]
        if self.label:
            self.label.text = "\n".join(parts)
