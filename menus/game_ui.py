from typing import Any, Callable, Dict, Optional
from functools import partial

from panda3d_kivy.app import App
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.core.window import Window

from camera import CivCamera
from gameplay.units.classes._base import UnitBaseClass

from data.tiles.tile import Tile
from managers.ui import ui
from managers.input import Input
from managers.unit import Unit
from managers.world import World
from system.actions import Action


class HoverBehavior:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Register custom events
        self.register_event_type("on_enter")  # type: ignore
        self.register_event_type("on_leave")  # type: ignore
        self._hovered = False
        # Bind to mouse movement
        Window.bind(mouse_pos=self.on_mouse_move)

    def on_mouse_move(self, window, pos):
        if not self.get_root_window():  # type: ignore
            return
        # Check if the mouse is over the widget
        inside = self.collide_point(*self.to_widget(*pos))  # type: ignore
        if inside and not self._hovered:
            self._hovered = True
            self.dispatch("on_enter")  # type: ignore
        elif not inside and self._hovered:
            self._hovered = False
            self.dispatch("on_leave")  # type: ignore

    def on_enter(self):
        """Override to define behavior on hover enter."""
        pass

    def on_leave(self):
        """Override to define behavior on hover leave."""
        pass


class FloatLayoutWithHover(FloatLayout, HoverBehavior):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_enter(self):
        app = App.get_running_app()
        if app and hasattr(app, "disable_raycaster"):
            app.disable_raycaster()

    def on_leave(self):
        app = App.get_running_app()
        if app and hasattr(app, "enable_raycaster"):
            app.enable_raycaster()


class HoverBoxLayout(BoxLayout, HoverBehavior):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_enter(self):
        app = App.get_running_app()
        if app and hasattr(app, "disable_raycaster"):
            app.disable_raycaster()

    def on_leave(self):
        app = App.get_running_app()
        if app and hasattr(app, "enable_raycaster"):
            app.enable_raycaster()


# --- KV Layout with HoverFrames for UI Panels ---
KV = r"""
FloatLayout:
    # Action Bar at the Bottom
    HoverBoxLayout:
        id: action_bar
        orientation: 'horizontal'
        size_hint: None, None
        width: 1000
        height: 80
        spacing: 10
        pos_hint: {'center_x': 0.5, 'y': 0}  # Centered at the bottom

    # Debug Panel (Top-Left Corner) wrapped in a HoverFrame
    FloatLayoutWithHover:
        id: debug_frame
        size_hint: None, None
        width: 300
        height: 500
        pos_hint: {'x': 0, 'top': 1}  # Position at top-left

        canvas.before:
            Color:
                rgba: (0, 0, 0, 0.7)  # Black background with 70% opacity
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            id: debug_panel
            text: "Debug Info:\nFPS: 60\nPlayer Pos: (0,0,0)"
            size_hint_x: 1
            size_hint_y: None
            font_size: '11sp'
            height: self.texture_size[1]
            valign: 'top'
            halign: 'left'
            text_size: self.width, None
            pos_hint: {'top': 1}
            color: (1, 1, 1, 1)

    # Camera Panel (Top-Right Corner) wrapped in a HoverFrame
    FloatLayoutWithHover:
        id: camera_frame
        size_hint: None, None
        width: 200
        height: 200
        pos_hint: {'right': 1, 'top': 1}  # Position at top-right

        canvas.before:
            Color:
                rgba: (0, 0, 0, 0.5)  # Black background with 50% opacity
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            id: camera_panel
            text: "Debug Info:\nFPS: 60\nPlayer Pos: (0,0,0)"
            size_hint_x: 1
            size_hint_y: None
            font_size: '11sp'
            height: self.texture_size[1]
            valign: 'top'
            halign: 'right'
            text_size: self.width, None
            pos_hint: {'top': 1, 'right': 1}
            color: (1, 1, 1, 1)
"""


class GameUI(App):
    debug_data: Dict[str, str] = {
        "state": "Playing",
    }

    def __init__(self, panda_app, display_region=None, **kwargs):
        self.game_manager: "ui" = kwargs.get("game_manager")  # type: ignore
        self._base = panda_app
        self.world_manager = World.get_instance()
        self.camera: CivCamera = CivCamera.get_instance()
        self.unit_manager = Unit.get_instance()
        self.input = Input.get_instance()
        self.waiting_for_world_input: bool = False

        del kwargs["game_manager"]

        self._base.accept("ui.update.user.tile_clicked", self.process_tile_click)
        self._base.accept("ui.update.user.unit_clicked", self.process_unit_click)

        super().__init__(panda_app, display_region, **kwargs)

    def build(self):
        # Set the mask for UI elements
        # Load the UI and keep references to the ids
        self.data = Builder.load_string(KV)
        self.ids: Any = self.data.ids  # type: ignore

        # Get references from the layout
        self.action_bar = self.ids.action_bar
        self.debug_panel = self.ids.debug_panel  # This is the label inside the debug frame
        self.camera_panel = self.ids.camera_panel  # This is the label inside the camera frame

        self.wait_for_next_input_of_user: bool = False
        self.wait_for_action_of_user: Optional[Callable] = None
        self.unit_waiting_for_action: Optional[UnitBaseClass] = None

        # Add skill buttons to the action bar
        for i in range(10):
            button = Button(text=f"Skill {i + 1}", size_hint=(None, None), width=100, height=75)
            self.action_bar.add_widget(button)

        # Schedule updates for the stats displayed on the camera panel
        Clock.schedule_interval(self.update_stats_bar, 1.0)  # Update every second

        return self.data

    def update_stats_bar(self, dt):
        fps = self._base.clock.getAverageFrameRate()
        text = f"FPS: {fps:.2f}\nYaw: {self.camera.yaw}\nPOS: {self.camera.getPos()} \nHPR: {self.camera.getHpr()} \n"
        self.camera_panel.text = text

    def process_tile_click(self, tile: str):
        _tile: Optional[Tile] = self.world_manager.lookup_on_tag(tile)

        if _tile is not None:
            self.debug_panel.text = "\n".join(f"{key}: {value}" for key, value in _tile.to_gui().items())

            # If we are waiting for an action, execute it now
            if self.wait_for_next_input_of_user and self.wait_for_action_of_user:
                self.wait_for_action_of_user(_tile)  # Call the stored action with the tile
                self.wait_for_next_input_of_user = False
                self.wait_for_action_of_user = None  # Reset state

    def process_unit_click(self, unit: str):
        _unit: Optional[UnitBaseClass] = self.unit_manager.find_unit(unit)
        if _unit is not None:
            self.debug_panel.text = "\n".join(f"{key}: {value}" for key, value in _unit.to_gui().items())
        self.generate_buttons_for_unit_actions(unit)

    def generate_buttons_for_unit_actions(self, unit: str):
        _unit: Optional[UnitBaseClass] = self.unit_manager.find_unit(unit)
        if _unit is not None:
            self.action_bar.clear_widgets()

            for action in _unit.get_actions():
                button = Button(
                    text=str(action.name),
                    size_hint=(None, None),
                    width=100,
                    height=75,
                    on_press=partial(self.prepare_action, action, _unit),
                )
                self.action_bar.add_widget(button)

    def prepare_action(self, action: Action, unit: UnitBaseClass, _instance):
        """Prepares an action and waits for the next tile click before executing."""
        self.wait_for_next_input_of_user = True
        self.wait_for_action_of_user = partial(self.execute_action, action, unit)
        self.unit_waiting_for_action = unit
        self.waiting_for_world_input = True
        self.debug_panel.text = "Waiting for tile selection..."

    def execute_action(self, action: Action, unit: UnitBaseClass, tile: Optional[Tile]):
        """Executes the action after tile selection (if required)."""
        action.action_kwargs["unit"] = unit

        if tile is not None:
            action.action_kwargs["tile"] = tile  # Assign the selected tile

        if action.run() is False:
            self.debug_panel.text = "Action failed!"

        # Reset waiting state
        self.wait_for_next_input_of_user = False
        self.wait_for_action_of_user = None
        self.unit_waiting_for_action = None
        self.game_manager.select_unit(unit)

    # --- Raycaster Control Methods ---
    def disable_raycaster(self):
        """Disable the raycaster when hovering over UI elements."""
        self.input.active = False

    def enable_raycaster(self):
        """Enable the raycaster when not hovering over UI elements."""
        self.input.active = True
