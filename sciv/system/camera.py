from logging import Logger
from math import cos, pi, sin
from typing import TYPE_CHECKING, Any, Literal, Optional, Tuple

from direct.showbase.DirectObject import DirectObject
from direct.task import Task
from panda3d.core import Camera as PandaCamera, LPoint3f, LVecBase3f, MouseWatcher, NodePath
from panda3d_kivy.core.window import WindowBase  # type: ignore
from mixins.singleton import Singleton

if TYPE_CHECKING:
    from game import SCIV


class Camera(Singleton, DirectObject):
    """

    Modified camera controller:
      - Left-drag => rotate around pivot (with a threshold)
      - Right-drag => pan/move
      - Q/E => rotate around pivot by rotation_speed
      - Mouse wheel => zoom
      - R => recenter
      - WASD/arrow keys => optional panning
    """

    def __init__(self, base: "SCIV"):
        self.base: "SCIV" = base
        self.active = True
        self.mouseWatcherNode: MouseWatcher = self.base.mouseWatcherNode  # type: ignore
        self.logger: Logger = self.base.logger.engine.getChild("camera")

        # Field-of-View parameters
        self.fov: float = 70.0

        # Zoom parameters
        self.zoom: float = 20.0
        self.min_zoom: float = 2.0
        self.max_zoom: float = 50.0
        self.zoom_speed: float = 2.0

        self.zoom_enabled: bool = True
        self.lock: bool = False

        # Fixed pitch at 45 degrees
        self.pitch: float = 45.0

        # Pivot rotation (yaw)
        self.yaw: float = 0.0
        self._update_yaw_trig()

        # Pan & rotate speeds
        self.pan_speed: float = 20.0
        self.rotate_speed: float = 60.0  # degrees/sec

        # Optional target NodePath to center on
        self.target: Optional[NodePath] = None

        # Window dimensions & aspect
        self.win_x: int = self.base.win.getXSize()  # type: ignore
        self.win_y: int = self.base.win.getYSize()  # type: ignore
        self._aspect_ratio: float = self.win_x / self.win_y if self.win_y else 1.0

        # Create pivot node
        self.pivot = self.base.render.attachNewNode("cameraPivot")  # type: ignore
        self.reset_pivot_position()

        # Attach the camera to this pivot
        self.base.camera.reparentTo(self.pivot)  # type: ignore
        self.update_camera_position()

        # Apply default FOV and aspect ratio
        lens = self.base.cam.node().getLens()
        lens.setFov(self.fov)
        lens.setAspectRatio(self._aspect_ratio)
        self.base.cam.node().setLens(lens)

        # --- Throttling state ---
        # Desired state variables
        self._desired_pivot_pos: LPoint3f = self.pivot.getPos()  # type: ignore
        self._desired_yaw = self.yaw
        self._desired_zoom = self.zoom
        # Flush interval (seconds)
        self.update_interval: float = 0.05
        self._time_since_last_flush: float = 0.0

        # Track key & drag states
        self.keys = {
            "up": False,
            "down": False,
            "left": False,
            "right": False,
            "rotate_left": False,
            "rotate_right": False,
        }
        self.left_dragging = False
        self.right_dragging = False
        self.last_mouse_pos: Tuple[float, float] = (0.0, 0.0)
        self.drag_threshold = 40  # pixels to trigger rotation

        # Set up controls & add update task
        self.setup_controls()

    def _update_yaw_trig(self):
        rad = self.yaw * (pi / 180.0)
        self._cos_yaw = cos(rad)
        self._sin_yaw = sin(rad)

    def register(self) -> Literal[True]:
        # Single throttled update task
        self.base.taskMgr.add(self.update, "updateCivCameraTask")  # type: ignore
        return True

    def reset(self):
        self.pivot.setPos(0, 0, 0)  # type: ignore
        self.base.camera.setPos(0, 0, 0)  # type: ignore
        self.base.camera.setHpr(0, 0, 0)  # type: ignore

        # Reset lens FOV and aspect
        lens = self.base.cam.node().getLens()
        lens.setFov(self.fov)
        lens.setAspectRatio(self._aspect_ratio)
        self.base.cam.node().setLens(lens)

        self.yaw = 0.0
        self._update_yaw_trig()
        self.zoom = 20.0
        # reset desired states too
        self._desired_pivot_pos = self.pivot.getPos()  # type: ignore
        self._desired_yaw = self.yaw
        self._desired_zoom = self.zoom
        self.update_camera_position()

    def __setup__(self, *args: Any, **kwargs: Any):
        return super().__setup__(*args, **kwargs)

    def base_camera(self) -> NodePath | PandaCamera:
        """Return the camera node."""
        return self.base.camera  # type: ignore

    def getPos(self) -> LPoint3f:
        return self.base_camera().getPos(self.base.render)  # type: ignore

    def getHpr(self) -> LVecBase3f:
        return self.base_camera().getHpr(self.base.render)  # type: ignore

    def setup_controls(self):
        # WASD / arrows
        for key, name in [
            ("arrow_up", "up"),
            ("w", "up"),
            ("arrow_down", "down"),
            ("s", "down"),
            ("arrow_left", "left"),
            ("a", "left"),
            ("arrow_right", "right"),
            ("d", "right"),
        ]:
            self.accept(key, self.set_key, [name, True])
            self.accept(f"{key}-up", self.set_key, [name, False])

        # Q/E rotation
        self.accept("q", self.set_key, ["rotate_left", True])
        self.accept("q-up", self.set_key, ["rotate_left", False])
        self.accept("e", self.set_key, ["rotate_right", True])
        self.accept("e-up", self.set_key, ["rotate_right", False])

        # Mouse wheel => zoom
        self.accept("wheel_up", self.zoom_in)
        self.accept("wheel_down", self.zoom_out)

        # Recenter
        self.accept("r", self.recenter)

        # Mouse drags
        self.accept("mouse1", self.start_left_drag)
        self.accept("mouse1-up", self.stop_left_drag)
        self.accept("mouse3", self.start_right_drag)
        self.accept("mouse3-up", self.stop_right_drag)

        # Zoom/control locks
        self.accept("system.input.disable_zoom", self.disable_zoom)
        self.accept("system.input.enable_zoom", self.enable_zoom)
        self.accept("system.input.disable_control", self.disable_control)
        self.accept("system.input.enable_control", self.enable_control)
        self.accept("system.input.camera_lock", self.lock_camera)
        self.accept("system.input.camera_unlock", self.unlock_camera)

        # Window resize
        self.accept("window-event", self.on_window_resize)  # type: ignore

    def set_key(self, key: str, value: Any):
        self.keys[key] = value

    def lock_camera(self):
        self.lock = True

    def unlock_camera(self):
        self.lock = False

    def disable_control(self):
        self.active = False

    def enable_control(self):
        self.active = True

    def disable_zoom(self):
        if self.lock:
            return
        self.logger.debug("Disabling zoom")
        self.zoom_enabled = False

    def enable_zoom(self):
        if self.lock:
            return
        self.logger.debug("Enabling zoom")
        self.zoom_enabled = True

    def zoom_in(self):
        if not self.zoom_enabled:
            return
        # adjust desired only
        self._desired_zoom = max(self.min_zoom, self._desired_zoom - self.zoom_speed)

    def zoom_out(self):
        if not self.zoom_enabled:
            return
        self._desired_zoom = min(self.max_zoom, self._desired_zoom + self.zoom_speed)

    def on_window_resize(self, window: WindowBase) -> None:  # type: ignore
        if window != self.base.win:  # type: ignore
            return

        self.win_x = window.getXSize()  # type: ignore
        self.win_y = window.getYSize()  # type: ignore
        self._aspect_ratio = self.win_x / self.win_y if self.win_y else 1.0  #   type: ignore
        self.logger.debug(f"Window resized: {self.win_x}x{self.win_y}, aspect={self._aspect_ratio:.2f}")  # type: ignore

        # update lens aspect ratio
        lens = self.base.cam.node().getLens()
        lens.setAspectRatio(self._aspect_ratio)  # type: ignore
        self.base.cam.node().setLens(lens)

    def update_camera_position(self):
        """Place camera at (zoom, pitch) around the pivot, and rotate by yaw."""
        rad = self.pitch * (pi / 180.0)
        offset_y = -self.zoom * cos(rad)
        offset_z = self.zoom * sin(rad)
        self.base_camera().setPos(0, offset_y, offset_z)  # type: ignore
        self.pivot.setH(self.yaw)  # type: ignore
        self.base_camera().lookAt(self.pivot)  # type: ignore

    def reset_pivot_position(self):
        if self.target is not None:
            self.pivot.setPos(self.target.getPos())  # type: ignore
        else:
            self.pivot.setPos(0, 0, 0)  # type: ignore

    def recenter(self):
        from managers.game import PlayerManager

        center: Tuple[float, float, float] = (0, 0, 0)
        if PlayerManager.if_has_capital():
            capital = PlayerManager.player().capital
            if capital is None:
                return
            tile = capital.get_tile().get_pos()
            center = (tile[0], tile[1], 0)
        elif units := PlayerManager.session_player().get_all_units():
            unit = list(units)[0]  # type: ignore
            if unit is not None and unit.tile is not None:  # type: ignore
                pos = unit.get_tile().get_pos()  # type: ignore
                center = (pos[0], pos[1], 0)
        else:
            raise NotImplementedError("No target to recenter on")

        # immediately jump pivot
        self.pivot.setPos(*center)  # type: ignore
        self._desired_pivot_pos: LPoint3f = self.pivot.getPos()  # type: ignore
        # reset yaw and zoom
        self.yaw = 0.0
        self._update_yaw_trig()
        self.zoom = 20.0
        self._desired_yaw = self.yaw
        self._desired_zoom = self.zoom
        self.base.camera.setHpr(0, 0, 0)  # type: ignore
        self.base.camera.setPos(*center)  # type: ignore

    def start_left_drag(self):
        if not self.mouseWatcherNode.hasMouse():
            return
        self.left_dragging = True
        md = self.mouseWatcherNode.getMouse()
        self.last_mouse_pos = (md.getX(), md.getY())

    def stop_left_drag(self):
        self.left_dragging = False

    def start_right_drag(self):
        if not self.mouseWatcherNode.hasMouse():
            return
        self.right_dragging = True
        md = self.mouseWatcherNode.getMouse()
        self.last_mouse_pos = (md.getX(), md.getY())

    def stop_right_drag(self):
        self.right_dragging = False

    def _sample_input(self, dt: float):
        # pan with keys
        forward = (self._sin_yaw, -self._cos_yaw)
        right = (self._cos_yaw, self._sin_yaw)
        px, py, pz = self._desired_pivot_pos  # type: ignore

        if self.keys["down"]:
            px += forward[0] * self.pan_speed * dt  # type: ignore
            py += forward[1] * self.pan_speed * dt  # type: ignore
        if self.keys["up"]:
            px -= forward[0] * self.pan_speed * dt  # type: ignore
            py -= forward[1] * self.pan_speed * dt  # type: ignore
        if self.keys["left"]:
            px -= right[0] * self.pan_speed * dt  # type: ignore
            py -= right[1] * self.pan_speed * dt  # type: ignore
        if self.keys["right"]:
            px += right[0] * self.pan_speed * dt  # type: ignore
            py += right[1] * self.pan_speed * dt  # type: ignore

        # rotation keys
        if self.keys["rotate_left"]:
            self._desired_yaw += self.rotate_speed * dt
        if self.keys["rotate_right"]:
            self._desired_yaw -= self.rotate_speed * dt

        # dragging deltas
        if self.mouseWatcherNode.hasMouse():
            md = self.mouseWatcherNode.getMouse()
            x, y = md.getX(), md.getY()
            dx = x - self.last_mouse_pos[0]
            dy = y - self.last_mouse_pos[1]

            if self.left_dragging and abs(dx) >= self.drag_threshold:
                self._desired_yaw -= dx * 0.1
            elif self.right_dragging:
                # screen px to world units
                delta_px_x = dx * self.win_x / 2
                delta_px_y = dy * self.win_y / 2
                pan_factor = 0.015 * (self._desired_zoom / 25)
                px += (-delta_px_x * pan_factor) * self._cos_yaw + (delta_px_y * pan_factor) * self._sin_yaw  # type: ignore
                py += (-delta_px_x * pan_factor) * self._sin_yaw - (delta_px_y * pan_factor) * self._cos_yaw  # type: ignore

            # update last_mouse_pos always
            self.last_mouse_pos = (x, y)

        # commit new pivot pos
        self._desired_pivot_pos = LPoint3f(px, py, pz)  # type: ignore

    def _flush_to_gpu(self):
        # apply accumulated desired state
        self.pivot.setPos(self._desired_pivot_pos)  # type: ignore
        self.yaw = self._desired_yaw
        self._update_yaw_trig()
        self.zoom = self._desired_zoom
        self.update_camera_position()

    def update(self, task: Task.Task) -> Literal[1]:
        if not self.active and not (self.left_dragging or self.right_dragging or any(self.keys.values())):
            return task.cont
        dt: float = self.base.clock.getDt()  # type: ignore
        # sample inputs every frame
        self._sample_input(dt)  # type: ignore
        # throttle flush
        self._time_since_last_flush += dt
        if self._time_since_last_flush >= float(self.update_interval):  # type: ignore
            self._flush_to_gpu()
            self._time_since_last_flush = 0.0
        return task.cont
