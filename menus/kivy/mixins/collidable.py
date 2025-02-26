from managers.input import Input
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import Openciv


class CollisionPreventionMixin:
    non_collidable_ui = []
    has_tracking_enabled: bool = False
    in_collision_with_ui: bool = False
    tick_rate: float = 0.25  # How often to check for mouse movement

    def __init__(self, base: "Openciv"):
        self._input = Input.get_instance()
        self._base: "Openciv" = base

        if not self.has_tracking_enabled:
            self.enable_tracking()
            self.has_tracking_enabled = True

    def enable_tracking(self):
        self._base.taskMgr.add(self.track_mouse_movement, "TrackMouseMovement", delay=self.tick_rate)

    def track_mouse_movement(self, task):
        if self._base.mouseWatcherNode.hasMouse():  # Check if the mouse is detected
            mouse_pos = self._base.mouseWatcherNode.getMouse()
            # Convert Panda3D mouse coords (-1 to 1) to screen space
            screen_x = (mouse_pos.getX() + 1) / 2 * self._base.win.getXSize()
            screen_y = (1 - mouse_pos.getY()) / 2 * self._base.win.getYSize()

            self.on_mouse_move(screen_x, screen_y)  # Call mouse move handler

        return task.cont  # Keep running this task every frame

    def on_mouse_move(self, x, y):
        # Flip Y-axis to match Kivy's coordinate system
        kivy_window_height = self._base.win.getYSize()
        y = kivy_window_height - y

        inside_ui = False
        for element in self.non_collidable_ui:
            parent = element.parent
            if not parent:
                continue  # Skip orphaned elements

            # Get real width/height, handling size_hint if necessary
            real_width = element.size_hint_x * parent.width if element.size_hint_x else element.width
            real_height = element.size_hint_y * parent.height if element.size_hint_y else element.height

            # Convert to absolute screen-space position
            ui_x, ui_y = element.to_window(element.x, element.y)
            ui_right = ui_x + real_width
            ui_top = ui_y + real_height

            # Check if the mouse is inside the UI element
            if ui_x <= x <= ui_right and ui_y <= y <= ui_top:
                inside_ui = True
                break  # Stop checking after first detected collision

        self._input.active = not inside_ui

    def register_non_collidable(self, element):
        """Adds a UI element to the list of non-collidable UI elements."""
        if element not in self.non_collidable_ui:
            self.non_collidable_ui.append(element)

    def unregister_non_collidable(self, element):
        """Removes a UI element from the list of non-collidable UI elements."""
        if element in self.non_collidable_ui:
            self.non_collidable_ui.remove(element)
