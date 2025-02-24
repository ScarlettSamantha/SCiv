from typing import Any, Callable, Dict, Optional
from functools import partial

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.clock import Clock
from camera import CivCamera
from gameplay.units.classes._base import UnitBaseClass

from data.tiles.tile import Tile
from managers.ui import ui
from managers.input import Input
from managers.unit import Unit
from managers.world import World
from system.actions import Action


# --- KV Layout with HoverFrames for UI Panels ---
KV = r"""
<GameUIScreen>:
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
        FloatLayout:
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
        FloatLayout:
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


class GameUIScreen(Screen):
    debug_data: Dict[str, str] = {
        "state": "Playing",
    }

    def __init__(self, **kwargs):
        self.game_manager: "ui" = kwargs.get("game_manager")
        self._base: Any = kwargs.get("base")
        del kwargs["game_manager"]
        del kwargs["base"]
        super().__init__(**kwargs)
        self.world_manager = World.get_instance()
        self.camera: CivCamera = CivCamera.get_instance()
        self.unit_manager = Unit.get_instance()
        self.input = Input.get_instance()
        self.waiting_for_world_input: bool = False
        self._hovered = False

        self.wait_for_next_input_of_user: bool = False
        self.wait_for_action_of_user: Optional[Callable] = None
        self.unit_waiting_for_action: Optional[UnitBaseClass] = None

        # List of UI elements that disable input when hovered
        self.non_collidable_ui = []

        self._base.accept("ui.update.user.tile_clicked", self.process_tile_click)
        self._base.accept("ui.update.user.unit_clicked", self.process_unit_click)

        Builder.load_string(KV)

    def register_non_collidable(self, element):
        """Adds a UI element to the list of non-collidable UI elements."""
        if element not in self.non_collidable_ui:
            self.non_collidable_ui.append(element)

    def build(self):
        # Load the UI and keep references to the ids
        self.data = Builder.load_string(KV)
        self.ids: Any = self.data.ids  # type: ignore

        # Get references from the layout
        self.action_bar = self.ids.action_bar
        self.debug_panel = self.ids.debug_panel  # Debug panel
        self.camera_panel = self.ids.camera_panel  # Camera panel

        # Register UI elements as non-collidable
        self.register_non_collidable(self.action_bar)
        self.register_non_collidable(self.debug_panel)
        self.register_non_collidable(self.camera_panel)

        # Reduce clock update frequency (every 0.25 seconds instead of every tick)
        Clock.schedule_interval(self.update_stats_bar, 0.25)

        # Track mouse movement via Panda3D task manager
        self._base.taskMgr.add(self.track_mouse_movement, "TrackMouseMovement")

        return self.data

    def track_mouse_movement(self, task):
        if self._base.mouseWatcherNode.hasMouse():  # Check if the mouse is detected
            mouse_pos = self._base.mouseWatcherNode.getMouse()
            # Convert Panda3D mouse coords (-1 to 1) to screen space
            screen_x = (mouse_pos.getX() + 1) / 2 * self._base.win.getXSize()
            screen_y = (1 - mouse_pos.getY()) / 2 * self._base.win.getYSize()

            self.on_mouse_move(screen_x, screen_y)  # Call mouse move handler

        return task.cont  # Keep running this task every frame

    def on_mouse_move(self, x, y):
        # Convert Y-coordinates if needed
        kivy_window_height = self._base.win.getYSize()
        y = kivy_window_height - y  # Flip Y-axis if needed

        # Check if mouse is inside any registered UI element
        inside_ui = any(
            element.x <= x <= element.right and element.y <= y <= element.top for element in self.non_collidable_ui
        )

        # print(f"Inside UI: {inside_ui}, Mouse Pos: {x}, {y}")

        if inside_ui:
            self.input.active = False
        else:
            self.input.active = True

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
        if action.on_the_spot_action:
            action.action_kwargs["unit"] = unit
            action.run()
            if action.remove_actions_after_use:
                self.action_bar.clear_widgets()
            return

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
        if action.remove_actions_after_use:
            self.action_bar.clear_widgets()
