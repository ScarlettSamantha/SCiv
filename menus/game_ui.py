from typing import Any, Dict
from panda3d_kivy.app import App
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock

from camera import CivCamera
from gameplay.units.classes._base import UnitBaseClass

from data.tiles.tile import Tile
from managers.unit import Unit
from managers.world import World


KV = r"""
FloatLayout:
    # Action Bar at the Bottom
    BoxLayout:
        id: action_bar
        orientation: 'horizontal'
        size_hint: None, None
        width: 1000
        height: 80
        spacing: 10
        pos_hint: {'center_x': 0.5, 'y': 0}  # Centered at the bottom

    # Debug Panel (Top-Left Corner)
    FloatLayout:
        size_hint: None, None
        width: 300
        height: 500
        pos_hint: {'x': 0, 'top': 1}  # Position at top-left

        canvas.before:
            Color:
                rgba: (0, 0, 0, 0.7)  # Black background with 50% transparency
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            id: debug_panel
            text: "Debug Info:\\nFPS: 60\\nPlayer Pos: (0,0,0)"
            size_hint_x: 1
            size_hint_y: None
            font_size: '11sp'
            height: self.texture_size[1]  # Adjust height to fit content
            valign: 'top'
            halign: 'left'
            text_size: self.width, None  # Forces wrapping inside width
            pos_hint: {'top': 1}  # <-- Forces text to the top!
            color: (1, 1, 1, 1)  # White text

    # Camera Panel (Top-Right Corner)
    FloatLayout:
        size_hint: None, None
        width: 200
        height: 200
        pos_hint: {'right': 1, 'top': 1}  # Position at top-right


        canvas.before:
            Color:
                rgba: (0, 0, 0, 0.5)  # Black background with 50% transparency
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            id: camera_panel
            text: "Debug Info:\\nFPS: 60\\nPlayer Pos: (0,0,0)"
            size_hint_x: 1
            size_hint_y: None
            font_size: '11sp'
            height: self.texture_size[1]  # Adjust height to fit content
            valign: 'top'
            halign: 'right'
            text_size: self.width, None  # Forces wrapping inside width
            pos_hint: {'top': 1, 'right': 1}  # <-- Forces text to the top!
            color: (1, 1, 1, 1)  # White text
"""


class GameUI(App):
    debug_data: Dict[str, str] = {
        "state": "Playing",
    }

    def __init__(self, panda_app, display_region=None, **kwargs):
        self.game_manager = kwargs.get("game_manager")
        self._base = panda_app
        self.world_manager = World.get_instance()
        self.camera: CivCamera = CivCamera.get_instance()
        self.unit_manager = Unit.get_instance()

        del kwargs["game_manager"]

        self._base.accept("ui.update.user.tile_clicked", self.process_tile_click)
        self._base.accept("ui.update.user.unit_clicked", self.process_unit_click)

        super().__init__(panda_app, display_region, **kwargs)

    def build(self):
        # Load the UI
        self.data = Builder.load_string(KV)
        self.ids: Any = self.data.ids  # type: ignore # Kivy doesn't know about ids

        # Get references
        self.action_bar = self.ids.action_bar
        self.debug_panel = self.ids.debug_panel
        self.camera_panel = self.ids.camera_panel

        # Add skill buttons
        for i in range(10):
            button = Button(text=f"Skill {i + 1}", size_hint=(None, None), width=100, height=75)
            self.action_bar.add_widget(button)

        # Schedule debug panel updates
        Clock.schedule_interval(self.update_stats_bar, 1.0)  # Update every second

        return self.data

    def update_stats_bar(self, df):
        fps = self._base.clock.getAverageFrameRate()
        text = (
            f"FPS: {fps:.2f}\n"
            + f"Yaw: {str(self.camera.yaw)}\n"
            + f"POS: {str(self.camera.getPos())} \n"
            + f"HPR: {str(self.camera.getHpr())} \n"
        )
        self.camera_panel.text = text

    def process_tile_click(self, tile: str):
        _tile: Tile | None = self.world_manager.lookup_on_tag(tile)
        if _tile is not None:
            self.debug_panel.text = "\n".join(f"{key}: {value}" for key, value in _tile.to_gui().items())

    def process_unit_click(self, unit: str):
        _unit: UnitBaseClass | None = self.unit_manager.find_unit(unit)
        if _unit is not None:
            self.debug_panel.text = "\n".join(f"{key}: {value}" for key, value in _unit.to_gui().items())
