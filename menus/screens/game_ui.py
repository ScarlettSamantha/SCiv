from typing import Any, Callable, Dict, Optional
from functools import partial

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from sympy import Float


from camera import CivCamera
from gameplay.units.classes._base import UnitBaseClass

from data.tiles.tile import Tile
from managers.ui import ui
from managers.input import Input
from managers.unit import Unit
from managers.world import World
from system.actions import Action


class GameUIScreen(Screen):
    debug_data: Dict[str, str] = {
        "state": "Playing",
    }

    def __init__(self, **kwargs: Any):
        if "game_manager" not in kwargs:
            raise ValueError("Game Manager is required to initialize the UI.")

        self.game_manager: "ui" = kwargs.get("game_manager")  # type: ignore # we check for it above

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

        self.debug_panel: Optional[Label] = None
        self.camera_panel: Optional[Label] = None

        self.root_layout: Optional[FloatLayout] = None
        self.action_bar_frame: Optional[BoxLayout] = None
        self.debug_frame: Optional[FloatLayout] = None
        self.camera_frame: Optional[FloatLayout] = None

        # List of UI elements that disable input when hovered
        self.non_collidable_ui = []

        self._base.accept("ui.update.user.tile_clicked", self.process_tile_click)
        self._base.accept("ui.update.user.unit_clicked", self.process_unit_click)

        Builder.load_string(self.build_screen())

    def get_debug_frame(self) -> FloatLayout:
        if self.debug_frame is None:
            raise AssertionError("Debug panel is not initialized.")

        return self.debug_frame

    def get_camera_frame(self) -> FloatLayout:
        if self.camera_frame is None:
            raise AssertionError("Camera panel is not initialized.")
        return self.camera_frame

    def get_action_bar_frame(self) -> BoxLayout:
        if self.action_bar_frame is None:
            raise AssertionError("Action bar is not initialized.")
        return self.action_bar_frame

    def get_root_layout(self) -> FloatLayout:
        if self.root_layout is None:
            raise AssertionError("Root layout is not initialized.")
        return self.root_layout

    def build_screen(self):
        # Main container
        self.root_layout = FloatLayout()

        # --- Action Bar (Bottom Centered) ---
        self.action_bar_frame = BoxLayout(
            orientation="horizontal",
            size_hint=(None, None),
            width=1000,
            height=80,
            spacing=10,
            pos_hint={"center_x": 0.5, "y": 0},
        )
        self.root_layout.add_widget(self.action_bar_frame)

        # --- Debug Panel (Top-Left Corner) ---
        self.debug_frame = FloatLayout(
            size_hint=(None, None),
            width=300,
            height=500,
            pos_hint={"x": 0, "top": 1},
        )

        with self.debug_frame.canvas.before:  # type: ignore
            Color(0, 0, 0, 0.7)  # Black background with 70% opacity
            self.debug_rect = Rectangle(size=self.debug_frame.size, pos=self.debug_frame.pos)

        def update_debug_rect(instance, value):
            self.debug_rect.size = instance.size
            self.debug_rect.pos = instance.pos

        self.debug_frame.bind(size=update_debug_rect, pos=update_debug_rect)  # type: ignore

        self.debug_panel = Label(
            text="Debug Info:\nFPS: 60\nPlayer Pos: (0,0,0)",
            size_hint_x=1,
            size_hint_y=None,
            font_size="11sp",
            height=50,
            valign="top",
            halign="left",
            text_size=(300, None),
            pos_hint={"top": 1},
            color=(1, 1, 1, 1),
        )

        self.debug_frame.add_widget(self.debug_panel)
        self.root_layout.add_widget(self.debug_frame)

        # --- Camera Panel (Top-Right Corner) ---
        self.camera_frame = FloatLayout(
            size_hint=(None, None),
            width=200,
            height=200,
            pos_hint={"right": 1, "top": 1},
        )

        with self.camera_frame.canvas.before:  # type: ignore
            Color(0, 0, 0, 0.5)  # Black background with 50% opacity
            self.camera_rect = Rectangle(size=self.camera_frame.size, pos=self.camera_frame.pos)

        def update_camera_rect(instance, value):
            self.camera_rect.size = instance.size
            self.camera_rect.pos = instance.pos

        self.camera_frame.bind(size=update_camera_rect, pos=update_camera_rect)  # type: ignore

        self.camera_panel = Label(
            text="Debug Info:\nFPS: 60\nPlayer Pos: (0,0,0)",
            size_hint_x=1,
            size_hint_y=None,
            font_size="11sp",
            height=50,
            valign="top",
            halign="right",
            text_size=(200, None),
            pos_hint={"top": 1, "right": 1},
            color=(1, 1, 1, 1),
        )

        self.camera_frame.add_widget(self.camera_panel)
        self.root_layout.add_widget(self.camera_frame)

        # Add the entire layout to the screen
        self.add_widget(self.root_layout)

        self.register_non_collidable(self.action_bar_frame)
        self.register_non_collidable(self.debug_panel)
        self.register_non_collidable(self.camera_panel)

        Clock.schedule_interval(self.update_stats_bar, 0.25)
        self._base.taskMgr.add(self.track_mouse_movement, "TrackMouseMovement")

        return self.root_layout

    def register_non_collidable(self, element):
        """Adds a UI element to the list of non-collidable UI elements."""
        if element not in self.non_collidable_ui:
            self.non_collidable_ui.append(element)

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
        self.input.active = not inside_ui

    def update_stats_bar(self, dt):
        fps = self._base.clock.getAverageFrameRate()
        text = f"FPS: {fps:.2f}\nYaw: {self.camera.yaw}\nPOS: {self.camera.getPos()} \nHPR: {self.camera.getHpr()} \n"
        self.camera_panel.text = text  # type: ignore # We know it exists because it's initialized in build_screen

    def process_tile_click(self, tile: str):
        _tile: Optional[Tile] = self.world_manager.lookup_on_tag(tile)

        if _tile is not None:
            self.debug_panel.text = "\n".join(f"{key}: {value}" for key, value in _tile.to_gui().items())  # type: ignore # We know it exists because it's initialized in build_screen

            # If we are waiting for an action, execute it now
            if self.wait_for_next_input_of_user and self.wait_for_action_of_user:
                self.wait_for_action_of_user(_tile)  # Call the stored action with the tile
                self.wait_for_next_input_of_user = False
                self.wait_for_action_of_user = None  # Reset state

    def process_unit_click(self, unit: str):
        _unit: Optional[UnitBaseClass] = self.unit_manager.find_unit(unit)
        if _unit is not None:
            self.debug_panel.text = "\n".join(f"{key}: {value}" for key, value in _unit.to_gui().items())  # type: ignore # We know it exists because it's initialized in build_screen
        self.generate_buttons_for_unit_actions(unit)

    def generate_buttons_for_unit_actions(self, unit: str):
        _unit: Optional[UnitBaseClass] = self.unit_manager.find_unit(unit)
        if _unit is not None:
            self.get_action_bar_frame().clear_widgets()

            for action in _unit.get_actions():
                button = Button(
                    text=str(action.name),
                    size_hint=(None, None),
                    width=100,
                    height=75,
                    on_press=partial(self.prepare_action, action, _unit),
                )
                self.get_action_bar_frame().add_widget(button)

    def prepare_action(self, action: Action, unit: UnitBaseClass, _instance):
        """Prepares an action and waits for the next tile click before executing."""
        if action.on_the_spot_action:
            action.action_kwargs["unit"] = unit
            action.run()
            if action.remove_actions_after_use:
                self.get_action_bar_frame().clear_widgets()
            return

        self.wait_for_next_input_of_user = True
        self.wait_for_action_of_user = partial(self.execute_action, action, unit)
        self.unit_waiting_for_action = unit
        self.waiting_for_world_input = True
        self.debug_panel.text = "Waiting for tile selection..."  # type: ignore # We know it exists because it's initialized in build_screen

    def execute_action(self, action: Action, unit: UnitBaseClass, tile: Optional[Tile]):
        """Executes the action after tile selection (if required)."""
        action.action_kwargs["unit"] = unit

        if tile is not None:
            action.action_kwargs["tile"] = tile  # Assign the selected tile

        if action.run() is False:
            self.debug_panel.text = "Action failed!"  # type: ignore # We know it exists because it's initialized in build_screen

        # Reset waiting state
        self.wait_for_next_input_of_user = False
        self.wait_for_action_of_user = None
        self.unit_waiting_for_action = None

        if action.remove_actions_after_use:
            self.get_action_bar_frame().clear_widgets()
