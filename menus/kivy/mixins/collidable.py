from typing import TYPE_CHECKING, Dict, Tuple

from gameplay.city import messenger
from managers.input import Input

if TYPE_CHECKING:
    from main import Openciv


class CollisionPreventionMixin:
    non_collidable_ui = []
    # Cache mapping element -> (ui_x, ui_y, ui_right, ui_top)
    ui_geometry_cache: Dict[object, Tuple[float, float, float, float]] = {}
    has_tracking_enabled: bool = False
    in_collision_with_ui: bool = False
    tick_rate: float = 0.5  # How often to check for mouse movement
    ui_geometry_update_interval: float = 5.0  # Seconds between UI geometry cache updates

    def __init__(self, base: "Openciv"):
        self._input = Input.get_instance()
        self._base: "Openciv" = base

        if not self.has_tracking_enabled:
            self.enable_tracking()
            self.has_tracking_enabled = True

        # Start a separate task to update the UI geometry cache
        self._base.taskMgr.doMethodLater(
            self.ui_geometry_update_interval, self._update_ui_geometry_cache_task, "UpdateUIGeometryCache"
        )

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

    def _update_ui_geometry_cache_task(self, task):
        self.update_ui_geometry_cache()
        return task.again  # Schedule the next update

    def update_ui_geometry_cache(self):
        """
        Updates the cached geometry for each non-collidable UI element.
        This method recalculates each element's screen-space bounding box.
        """
        for element in self.non_collidable_ui:
            parent = element.parent
            if not parent:
                continue  # Skip orphaned elements
            # Calculate real width and height, handling size_hint if necessary
            real_width = element.size_hint_x * parent.width if element.size_hint_x else element.width
            real_height = element.size_hint_y * parent.height if element.size_hint_y else element.height
            # Convert to absolute screen-space position
            ui_x, ui_y = element.to_window(element.x, element.y)
            ui_right = ui_x + real_width
            ui_top = ui_y + real_height
            self.ui_geometry_cache[element] = (ui_x, ui_y, ui_right, ui_top)

    def force_update_ui_geometry(self):
        """Manually forces an update of the UI geometry cache."""
        self.update_ui_geometry_cache()

    def on_mouse_move(self, x, y):
        # Flip Y-axis to match Kivy's coordinate system
        kivy_window_height = self._base.win.getYSize()
        y = kivy_window_height - y

        inside_ui = False
        # Use cached geometry if available
        for element, (ui_x, ui_y, ui_right, ui_top) in self.ui_geometry_cache.items():
            # Check if the mouse is inside the UI element
            if ui_x <= x <= ui_right and ui_y <= y <= ui_top:
                inside_ui = True
                break  # Stop checking after first detected collision

        if inside_ui:
            messenger.send("system.input.raycaster_off")
            self.in_collision_with_ui = True
        else:
            messenger.send("system.input.raycaster_on")
            self.in_collision_with_ui = False

    def register_non_collidable(self, element):
        """Adds a UI element to the list of non-collidable UI elements."""
        if element not in self.non_collidable_ui:
            self.non_collidable_ui.append(element)
            # Optionally update its cache immediately
            self.force_update_ui_geometry()

    def unregister_non_collidable(self, element):
        """Removes a UI element from the list of non-collidable UI elements."""
        if element in self.non_collidable_ui:
            self.non_collidable_ui.remove(element)
            # Remove element from cache if present
            self.ui_geometry_cache.pop(element, None)
