from logging import Logger
from math import cos, exp, pi, sin
from typing import TYPE_CHECKING, Any, Dict, Literal, Optional, Tuple

from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from direct.task import Task
from gameplay.city import City  # type: ignore
from managers.input import Input
from mixins.singleton import Singleton
from panda3d.core import Camera as PandaCamera
from panda3d.core import Lens, LPoint3f, LVecBase3f, MouseWatcher, NodePath
from panda3d_kivy.core.window import WindowBase  # type: ignore

if TYPE_CHECKING:
    from game import OpenCiv
    from gameplay.tile import Tile


class Camera(Singleton, DirectObject):
    def __init__(self, base: "OpenCiv"):
        self.base: "OpenCiv" = base
        self.active = True
        self.mouseWatcherNode: MouseWatcher = self.base.mouseWatcherNode  # type: ignore
        self.logger: Logger = self.base.logger.engine.getChild("camera")

        self.fov: float = 70.0

        self.zoom: float = 20.0
        self.min_zoom: float = 2.0
        self.max_zoom: float = 80.0
        self.zoom_speed: float = 3.0
        self.scroll_tick_rate: float = 0.1

        self.zoom_enabled: bool = True
        self.lock: bool = False

        self.pitch: float = 45.0

        self.yaw: float = 0.0
        self._update_yaw_trig()

        self.pan_speed: float = 20.0
        self.rotate_speed: float = 80.0
        self.pan_drag_sensitivity: float = 0.015
        self.rotate_drag_sensitivity: float = 0.16
        self.drag_threshold_pixels: float = 2.0
        self.pan_responsiveness: float = 18.0
        self.rotate_responsiveness: float = 16.0
        self.zoom_responsiveness: float = 20.0
        self.pan_overscroll_tiles: float = 1.5
        self.pan_overscroll_zoom_ratio: float = 0.1

        self.target: Optional[NodePath] = None
        self._world_pan_bounds: Optional[Tuple[float, float, float, float]] = None
        self._world_pan_bounds_signature: Optional[Tuple[int, int, int, int]] = None

        self.win_x: int = self.base.win.getXSize()  # type: ignore
        self.win_y: int = self.base.win.getYSize()  # type: ignore
        self._aspect_ratio: float = self.win_x / self.win_y if self.win_y else 1.0

        self.pivot = self.base.render.attachNewNode("cameraPivot")  # type: ignore
        self.reset_pivot_position()

        self.base.camera.reparentTo(self.pivot)  # type: ignore
        self.update_camera_position()

        lens = self.get_lens()
        lens.setFov(self.fov)
        lens.setAspectRatio(self._aspect_ratio)
        self.base.cam.node().setLens(lens)

        self._desired_pivot_pos: LPoint3f = self.pivot.getPos()  # type: ignore
        self._desired_yaw = self.yaw
        self._desired_zoom = self.zoom

        self.keys: Dict[str, bool] = {
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

        self._scrolling: bool = False
        self._since_last_scroll: float = 0.0
        self.scroll_end_timeout: float = max(self.scroll_tick_rate * 3.0, 0.25)
        self._scroll_tick_task_name: str = "cameraScrollTickTask"

        self.setup_controls()

        self.input: Input = self.base.input_manager

    def _update_yaw_trig(self):
        rad = self.yaw * (pi / 180.0)
        self._cos_yaw = cos(rad)
        self._sin_yaw = sin(rad)

    def register(self) -> Literal[True]:
        self.base.taskMgr.add(self.update, "updateCivCameraTask")  # type: ignore
        return True

    def reset(self):
        self.pivot.setPos(0, 0, 0)  # type: ignore
        self.base.camera.setPos(0, 0, 0)  # type: ignore
        self.base.camera.setHpr(0, 0, 0)  # type: ignore
        lens = self.get_lens()
        lens.setFov(self.fov)
        lens.setAspectRatio(self._aspect_ratio)
        self.base.cam.node().setLens(lens)
        self.yaw = 0.0
        self._update_yaw_trig()
        self.zoom = 20.0
        self._desired_pivot_pos = self.pivot.getPos()  # type: ignore
        self._desired_yaw = self.yaw
        self._desired_zoom = self.zoom
        self.update_camera_position()

    def base_camera(self) -> NodePath | PandaCamera:
        return self.base.camera  # type: ignore

    def getPos(self) -> LPoint3f:
        return self.base_camera().getPos(self.base.render)  # type: ignore

    def getHpr(self) -> LVecBase3f:
        return self.base_camera().getHpr(self.base.render)  # type: ignore

    def setup_controls(self):
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
        self.accept("q", self.set_key, ["rotate_left", True])
        self.accept("q-up", self.set_key, ["rotate_left", False])
        self.accept("e", self.set_key, ["rotate_right", True])
        self.accept("e-up", self.set_key, ["rotate_right", False])
        self.accept("wheel_up", self.zoom_in)
        self.accept("wheel_down", self.zoom_out)
        self.accept("r", self.recenter)
        self.accept("mouse1", self.start_left_drag)
        self.accept("mouse1-up", self.stop_left_drag)
        self.accept("mouse3", self.start_right_drag)
        self.accept("mouse3-up", self.stop_right_drag)
        self.accept("system.input.disable_zoom", self.disable_zoom)
        self.accept("system.input.enable_zoom", self.enable_zoom)
        self.accept("system.input.disable_control", self.disable_control)
        self.accept("system.input.enable_control", self.enable_control)
        self.accept("system.input.camera_lock", self.lock_camera)
        self.accept("system.input.camera_unlock", self.unlock_camera)
        self.accept("game.camera.request.center_on_tile", self._on_center_on_tile)
        self.base.taskMgr.add(self.on_window_resize, "checkWindowResizeTask", delay=5.0)  # type: ignore

    def _on_center_on_tile(self, tile: "Tile"):
        pos = tile.get_renderer().anchor_node.getPos(self.base.render)
        self.pivot.setPos(pos)
        self._desired_pivot_pos = self.pivot.getPos()

    def set_key(self, key: str, value: Any):
        self.keys[key] = value

    def clear_drag_state(self) -> None:
        self.left_dragging = False
        self.right_dragging = False

    def lock_camera(self):
        self.lock = True
        self.clear_drag_state()

    def unlock_camera(self):
        self.lock = False

    def disable_control(self):
        self.active = False
        self.clear_drag_state()

    def enable_control(self):
        self.active = True

    def begin_external_capture(self) -> None:
        self.clear_drag_state()
        self.active = False
        self.lock = True
        self.zoom_enabled = False

    def end_external_capture(self, *, active: bool = True, lock: bool = False, zoom_enabled: bool = True) -> None:
        self.clear_drag_state()
        self.active = active
        self.lock = lock
        self.zoom_enabled = zoom_enabled

    def disable_zoom(self):
        if self.lock:
            return
        self.logger.debug("Disabling zoom")
        self.zoom_enabled = False

    def zoom_factor(self) -> float:
        return (self.zoom - self.min_zoom) / (self.max_zoom - self.min_zoom)

    def enable_zoom(self):
        if self.lock:
            return
        self.logger.debug("Enabling zoom")
        self.zoom_enabled = True

    def _notify_scrolled(self):
        self._scrolling = True
        self._since_last_scroll = 0.0
        if not self.base.taskMgr.hasTaskNamed(self._scroll_tick_task_name):  # type: ignore
            self.base.taskMgr.doMethodLater(self.scroll_tick_rate, self._scroll_tick, self._scroll_tick_task_name)  # type: ignore

    def on_scroll_tick(self) -> None:
        MessengerGlobal.messenger.send("system.camera.zoom_ticked")

    def on_scroll_end(self) -> None:
        MessengerGlobal.messenger.send("system.camera.zoom_ended")

    def _scroll_tick(self, task: Task.Task) -> Literal[1]:
        if not self._scrolling:
            return Task.done  # type: ignore
        self.on_scroll_tick()
        task.delayTime = self.scroll_tick_rate  # type: ignore
        return Task.again  # type: ignore

    def zoom_in(self):
        if not self.zoom_enabled:
            return
        self._desired_zoom = max(self.min_zoom, self._desired_zoom - self.zoom_speed)
        self._notify_scrolled()

    def zoom_out(self):
        if not self.zoom_enabled:
            return
        self._desired_zoom = min(self.max_zoom, self._desired_zoom + self.zoom_speed)
        self._notify_scrolled()

    def on_window_resize(self, _: WindowBase | None) -> Literal[1]:  # type: ignore
        self.win_x = self.base.win.getXSize()  # type: ignore
        self.win_y = self.base.win.getYSize()  # type: ignore
        self._aspect_ratio = self.win_x / self.win_y if self.win_y else 1.0  #   type: ignore
        lens = self.get_lens()
        lens.setAspectRatio(self._aspect_ratio)  # type: ignore
        self.base.cam.node().setLens(lens)
        return 1

    def _get_world_pan_bounds(self) -> Optional[Tuple[float, float, float, float]]:
        world = self.base.world
        grid = world.get_grid()
        signature = (id(grid), len(grid), world.cols, world.rows)

        if self._world_pan_bounds_signature == signature:
            return self._world_pan_bounds

        if len(grid) == 0:
            self._world_pan_bounds_signature = signature
            self._world_pan_bounds = None
            return None

        tiles_iter = iter(grid.values())
        first_tile = next(tiles_iter, None)
        if first_tile is None:
            self._world_pan_bounds_signature = signature
            self._world_pan_bounds = None
            return None

        min_x = max_x = float(first_tile.pos_x)
        min_y = max_y = float(first_tile.pos_y)

        for tile in tiles_iter:
            tile_x = float(tile.pos_x)
            tile_y = float(tile.pos_y)

            if tile_x < min_x:
                min_x = tile_x
            elif tile_x > max_x:
                max_x = tile_x

            if tile_y < min_y:
                min_y = tile_y
            elif tile_y > max_y:
                max_y = tile_y

        self._world_pan_bounds_signature = signature
        self._world_pan_bounds = (min_x, max_x, min_y, max_y)
        return self._world_pan_bounds

    def _get_pan_overscroll_margin(self, bounds: Tuple[float, float, float, float]) -> Tuple[float, float]:
        world = self.base.world
        min_x, max_x, min_y, max_y = bounds
        span_x = max_x - min_x
        span_y = max_y - min_y
        fallback_step = max(float(world.hex_radius) * 2.0, 1.0)
        tile_step_x = span_x / max(world.cols - 1, 1) if world.cols > 1 else fallback_step
        tile_step_y = span_y / max(world.rows - 1, 1) if world.rows > 1 else fallback_step
        tile_step_x = max(tile_step_x, fallback_step)
        tile_step_y = max(tile_step_y, fallback_step)
        zoom_margin = self._desired_zoom * self.pan_overscroll_zoom_ratio
        return (
            tile_step_x * self.pan_overscroll_tiles + zoom_margin,
            tile_step_y * self.pan_overscroll_tiles + zoom_margin,
        )

    def _pan_speed_scale(self) -> float:
        return max(0.85, min(3.0, self._desired_zoom / 20.0))

    def _smoothing_factor(self, dt: float, responsiveness: float) -> float:
        if dt <= 0.0:
            return 1.0
        return min(1.0, 1.0 - exp(-responsiveness * dt))

    def _has_pending_motion(self) -> bool:
        current_x, current_y, current_z = self.pivot.getPos()  # type: ignore
        desired_x, desired_y, desired_z = self._desired_pivot_pos  # type: ignore
        return (
            abs(float(desired_x) - float(current_x)) > 0.001
            or abs(float(desired_y) - float(current_y)) > 0.001
            or abs(float(desired_z) - float(current_z)) > 0.001
            or abs(self._desired_yaw - self.yaw) > 0.05
            or abs(self._desired_zoom - self.zoom) > 0.01
        )

    def _clamp_pivot_position(self, pivot_pos: LPoint3f) -> LPoint3f:
        bounds = self._get_world_pan_bounds()
        if bounds is None:
            return pivot_pos

        min_x, max_x, min_y, max_y = bounds
        margin_x, margin_y = self._get_pan_overscroll_margin(bounds)
        pivot_x, pivot_y, pivot_z = pivot_pos  # type: ignore

        clamped_x = min(max(float(pivot_x), min_x - margin_x), max_x + margin_x)
        clamped_y = min(max(float(pivot_y), min_y - margin_y), max_y + margin_y)
        return LPoint3f(clamped_x, clamped_y, float(pivot_z))

    def update_camera_position(self):
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

        player = PlayerManager.session_player()
        assert player is not None, "No session player found to recenter camera on."

        center: Tuple[float, float, float] = (0, 0, 0)
        if (unit := self.input.selected_unit) is not None:
            if unit.tile is not None:
                pos = unit.get_tile().get_pos()  # type: ignore
                center = (pos[0], pos[1], 0)
            else:
                self.logger.debug(f"Recentered on unit at {center} but no tile found.")
        elif (tile := self.input.selected_tile) is not None:
            pos = tile.get_pos()  # type: ignore
            center = (pos[0], pos[1], 0)
        elif player.capital is not None:
            capital: City | None = player.capital()
            assert capital is not None, "Player has no capital to recenter on."
            capital_pos = capital.get_pos()
            center = (capital_pos[0], capital_pos[1], 0)
        elif units := player.get_all_units():
            unit = list(units)[0]  # type: ignore
            if unit is not None and unit.tile is not None:  # type: ignore
                pos = unit.get_tile().get_pos()  # type: ignore
                center = (pos[0], pos[1], 0)
        else:
            raise NotImplementedError("No target to recenter on")

        self.pivot.setPos(*center)  # type: ignore
        self._desired_pivot_pos: LPoint3f = self.pivot.getPos()  # type: ignore

        self.yaw = 0.0
        self._update_yaw_trig()
        self.zoom = 20.0
        self._desired_yaw = self.yaw
        self._desired_zoom = self.zoom
        self.base.camera.setHpr(0, 0, 0)  # type: ignore
        self.base.camera.setPos(*center)  # type: ignore

    def start_left_drag(self):
        if not self.active or self.lock:
            return
        if not self.mouseWatcherNode.hasMouse():
            return
        self.left_dragging = True
        md = self.mouseWatcherNode.getMouse()
        self.last_mouse_pos = (md.getX(), md.getY())

    def stop_left_drag(self):
        self.left_dragging = False

    def start_right_drag(self):
        if not self.active or self.lock:
            return
        if not self.mouseWatcherNode.hasMouse():
            return
        self.right_dragging = True
        md = self.mouseWatcherNode.getMouse()
        self.last_mouse_pos = (md.getX(), md.getY())

    def stop_right_drag(self):
        self.right_dragging = False

    def _sample_input(self, dt: float):
        forward = (self._sin_yaw, -self._cos_yaw)
        right = (self._cos_yaw, self._sin_yaw)
        px, py, pz = self._desired_pivot_pos  # type: ignore
        pan_speed = self.pan_speed * self._pan_speed_scale()

        if self.keys["down"]:
            px += forward[0] * pan_speed * dt  # type: ignore
            py += forward[1] * pan_speed * dt  # type: ignore
        if self.keys["up"]:
            px -= forward[0] * pan_speed * dt  # type: ignore
            py -= forward[1] * pan_speed * dt  # type: ignore
        if self.keys["left"]:
            px -= right[0] * pan_speed * dt  # type: ignore
            py -= right[1] * pan_speed * dt  # type: ignore
        if self.keys["right"]:
            px += right[0] * pan_speed * dt  # type: ignore
            py += right[1] * pan_speed * dt  # type: ignore

        if self.keys["rotate_left"]:
            self._desired_yaw += self.rotate_speed * dt
        if self.keys["rotate_right"]:
            self._desired_yaw -= self.rotate_speed * dt

        if self.mouseWatcherNode.hasMouse():
            md = self.mouseWatcherNode.getMouse()
            x, y = md.getX(), md.getY()
            dx = x - self.last_mouse_pos[0]
            dy = y - self.last_mouse_pos[1]
            delta_px_x = dx * self.win_x / 2
            delta_px_y = dy * self.win_y / 2

            if self.left_dragging and abs(delta_px_x) >= self.drag_threshold_pixels:
                self._desired_yaw -= delta_px_x * self.rotate_drag_sensitivity
            elif self.right_dragging:
                pan_factor = self.pan_drag_sensitivity * self._pan_speed_scale()
                px += (-delta_px_x * pan_factor) * self._cos_yaw + (delta_px_y * pan_factor) * self._sin_yaw  # type: ignore
                py += (-delta_px_x * pan_factor) * self._sin_yaw - (delta_px_y * pan_factor) * self._cos_yaw  # type: ignore

            self.last_mouse_pos = (x, y)

        self._desired_pivot_pos = self._clamp_pivot_position(LPoint3f(px, py, pz))  # type: ignore

    def _flush_to_gpu(self, dt: float):
        pan_factor = self._smoothing_factor(dt, self.pan_responsiveness)
        rotate_factor = self._smoothing_factor(dt, self.rotate_responsiveness)
        zoom_factor = self._smoothing_factor(dt, self.zoom_responsiveness)

        current_x, current_y, current_z = self.pivot.getPos()  # type: ignore
        desired_x, desired_y, desired_z = self._desired_pivot_pos  # type: ignore

        self.pivot.setPos(
            float(current_x) + (float(desired_x) - float(current_x)) * pan_factor,
            float(current_y) + (float(desired_y) - float(current_y)) * pan_factor,
            float(current_z) + (float(desired_z) - float(current_z)) * pan_factor,
        )  # type: ignore
        self.yaw += (self._desired_yaw - self.yaw) * rotate_factor
        self.zoom += (self._desired_zoom - self.zoom) * zoom_factor

        if abs(self._desired_yaw - self.yaw) <= 0.01:
            self.yaw = self._desired_yaw
        if abs(self._desired_zoom - self.zoom) <= 0.01:
            self.zoom = self._desired_zoom

        self._update_yaw_trig()
        self.update_camera_position()

    def update(self, task: Task.Task) -> Literal[1]:
        has_input = self.left_dragging or self.right_dragging or any(self.keys.values())
        if not self.active and not (has_input or self._scrolling or self._has_pending_motion()):
            return task.cont
        dt: float = self.base.clock.getDt()  # type: ignore

        self._sample_input(dt)  # type: ignore

        if self._scrolling:
            self._since_last_scroll += dt
            if self._since_last_scroll >= float(self.scroll_end_timeout):
                self._scrolling = False
                self.on_scroll_end()
                if self.base.taskMgr.hasTaskNamed(self._scroll_tick_task_name):  # type: ignore
                    self.base.taskMgr.remove(self._scroll_tick_task_name)  # type: ignore

        self._flush_to_gpu(dt)
        return task.cont

    def get_lens(self) -> Lens:
        return self.base.cam.node().getLens()
