from logging import Logger
from math import cos, pi, sin
from typing import TYPE_CHECKING, Tuple

from direct.showbase.DirectObject import DirectObject

from mixins.singleton import Singleton

if TYPE_CHECKING:
    from main import SCIV


class Camera(Singleton, DirectObject):
    """
    Modified camera controller:
      - Left-drag => rotate around pivot (slower)
      - Right-drag => pan/move
      - Q/E => rotate around pivot by rotation_speed
      - Mouse wheel => zoom
      - R => recenter
      - WASD/arrow keys => optional panning
    """

    def __init__(self, base: "SCIV"):
        self.base: "SCIV" = base
        self.active = True
        self.logger: Logger = self.base.logger.engine.getChild("camera")

        # Zoom parameters
        self.zoom = 20.0
        self.min_zoom = 2.0
        self.max_zoom = 50.0
        self.zoom_speed = 2.0

        self.zoom_enabled: bool = True

        self.lock: bool = False

        # Optional pitch
        self.pitch = 45.0  # We'll keep a fixed pitch at 45 degrees

        # Pivot rotation (yaw)
        self.yaw = 0.0

        # Pan speed (for WASD/arrow keys)
        self.pan_speed = 20.0
        # Rotation speed for Q/E (degrees/sec)
        self.rotate_speed = 60.0

        # If you have a target NodePath to center on
        self.target = None

        # Create pivot node
        self.pivot = self.base.render.attachNewNode("cameraPivot")
        self.reset_pivot_position()

        # Attach the camera to this pivot
        self.base.camera.reparentTo(self.pivot)
        self.update_camera_position()

        # Track key states
        self.keys = {
            "up": False,
            "down": False,
            "left": False,
            "right": False,
            # For Q/E rotation
            "rotate_left": False,
            "rotate_right": False,
        }

        # Dragging state
        self.left_dragging = False
        self.right_dragging = False
        self.last_mouse_pos = (0, 0)

        # Set up controls & add update task
        self.setup_controls()

    def register(self):
        self.base.taskMgr.add(self.update, "updateCivCameraTask")
        return True

    def reset(self):
        self.pivot.setPos(0, 0, 0)
        self.base.camera.setPos(0, 0, 0)
        self.base.camera.setHpr(0, 0, 0)
        self.yaw = 0
        self.zoom = 20.0
        self.update_camera_position()

    def __setup__(self, *args, **kwargs):
        return super().__setup__(*args, **kwargs)

    def getPos(self):
        """Return the current position of the camera in world space."""
        return self.base.camera.getPos(self.base.render)

    def getHpr(self):
        """Return the current orientation (heading, pitch, roll) of the camera."""
        return self.base.camera.getHpr(self.base.render)

    # -------------------------------------------------------------------------
    #  Setup Controls
    # -------------------------------------------------------------------------
    def setup_controls(self):
        """Bind keys/mouse for panning, zooming, rotating, re-centering, etc."""

        # WASD / arrow keys for panning
        self.accept("arrow_up", self.set_key, ["up", True])
        self.accept("arrow_up-up", self.set_key, ["up", False])
        self.accept("arrow_down", self.set_key, ["down", True])
        self.accept("arrow_down-up", self.set_key, ["down", False])
        self.accept("arrow_left", self.set_key, ["left", True])
        self.accept("arrow_left-up", self.set_key, ["left", False])
        self.accept("arrow_right", self.set_key, ["right", True])
        self.accept("arrow_right-up", self.set_key, ["right", False])

        self.accept("w", self.set_key, ["up", True])
        self.accept("w-up", self.set_key, ["up", False])
        self.accept("s", self.set_key, ["down", True])
        self.accept("s-up", self.set_key, ["down", False])
        self.accept("a", self.set_key, ["left", True])
        self.accept("a-up", self.set_key, ["left", False])
        self.accept("d", self.set_key, ["right", True])
        self.accept("d-up", self.set_key, ["right", False])

        # Q/E for rotation
        self.accept("q", self.set_key, ["rotate_left", True])
        self.accept("q-up", self.set_key, ["rotate_left", False])
        self.accept("e", self.set_key, ["rotate_right", True])
        self.accept("e-up", self.set_key, ["rotate_right", False])

        # Mouse wheel for zoom
        self.accept("wheel_up", self.zoom_in)
        self.accept("wheel_down", self.zoom_out)

        # Recenter pivot
        self.accept("r", self.recenter)

        # Left mouse => rotate
        self.accept("mouse1", self.start_left_drag)
        self.accept("mouse1-up", self.stop_left_drag)

        # Disable/enable zoom
        self.accept("system.input.disable_zoom", self.disable_zoom)
        self.accept("system.input.enable_zoom", self.enable_zoom)

        # Right mouse => pan (drag to move)
        self.accept("mouse3", self.start_right_drag)
        self.accept("mouse3-up", self.stop_right_drag)

        # Disable/enable camera control
        self.accept("system.input.disable_control", self.disable_control)
        self.accept("system.input.enable_control", self.enable_control)

        # Lock/unlock camera
        self.accept("system.input.camera_lock", self.lock_camera)
        self.accept("system.input.camera_unlock", self.unlock_camera)

    def set_key(self, key, value):
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
        if self.lock is True:
            return
        self.logger.debug("Disabling zoom")
        self.zoom_enabled = False

    def enable_zoom(self):
        if self.lock is True:
            return

        self.logger.debug("Enabling zoom")
        self.zoom_enabled = True

    # -------------------------------------------------------------------------
    #  Zoom
    # -------------------------------------------------------------------------
    def zoom_in(self):
        if not self.zoom_enabled:
            return

        self.zoom = max(self.min_zoom, self.zoom - self.zoom_speed)
        self.update_camera_position()

    def zoom_out(self):
        if not self.zoom_enabled:
            return

        self.zoom = min(self.max_zoom, self.zoom + self.zoom_speed)
        self.update_camera_position()

    # -------------------------------------------------------------------------
    #  Camera Positioning
    # -------------------------------------------------------------------------
    def update_camera_position(self):
        """Place camera at (zoom, pitch) around the pivot, and rotate by yaw."""
        rad = self.pitch * (pi / 180.0)

        # Distance "out" in the pivot's -Y direction
        offset_y = -self.zoom * cos(rad)
        offset_z = self.zoom * sin(rad)

        # Move the camera relative to pivot
        self.base.camera.setPos(0, offset_y, offset_z)

        # Turn pivot to yaw
        self.pivot.setH(self.yaw)

        # Make camera look at pivot
        self.base.camera.lookAt(self.pivot)

    # -------------------------------------------------------------------------
    #  Pivot Position Helpers
    # -------------------------------------------------------------------------
    def reset_pivot_position(self):
        """Set pivot to target or (0,0,0) if no target."""
        if self.target:
            self.pivot.setPos(self.target.getPos())
        else:
            self.pivot.setPos(0, 0, 0)

    def recenter(self):
        """
        Recenter camera pivot on target or (0,0,0),
        and optionally reset yaw/zoom.
        """
        from managers.game import PlayerManager

        center: Tuple[float, float, float] = (0, 0, 0)
        # Determine correct center first
        if PlayerManager.if_has_capital():
            capital = PlayerManager.player().capital
            if capital is None:
                return
            tile = capital.tile.get_pos()
            center = (tile[0], tile[1], 0)
        elif len((units := PlayerManager.session_player().get_all_units())) > 0:
            unit = units[0]()
            if unit is not None and unit.tile is not None:
                center = unit.tile.get_pos()
                center = (center[0], center[1], 0)
        else:
            center = self.target.getPos() if self.target else (0, 0, 0)

        # Move pivot only once to prevent flickering
        self.pivot.setPos(center)

        # Reset the camera's rotation but keep yaw
        self.base.camera.setHpr(0, self.pitch, 0)  # Reset heading & roll, keep default pitch
        self.yaw = 0  # Reset yaw
        self.zoom = 20.0  # Reset zoom
        self.update_camera_position()

    # -------------------------------------------------------------------------
    #  Mouse Drag
    # -------------------------------------------------------------------------
    def start_left_drag(self):
        """Begin left-drag => rotating."""
        if not self.base.mouseWatcherNode.hasMouse():
            return
        self.left_dragging = True
        md = self.base.win.getPointer(0)
        self.last_mouse_pos = (md.getX(), md.getY())

    def stop_left_drag(self):
        """Stop left-drag."""
        self.left_dragging = False

    def start_right_drag(self):
        """Begin right-drag => panning the pivot."""
        if not self.base.mouseWatcherNode.hasMouse():
            return
        self.right_dragging = True
        md = self.base.win.getPointer(0)
        self.last_mouse_pos = (md.getX(), md.getY())

    def stop_right_drag(self):
        """Stop right-drag."""
        self.right_dragging = False

    # -------------------------------------------------------------------------
    #  Main Update
    # -------------------------------------------------------------------------
    def update(self, task):
        """Per-frame update for panning with keys, Q/E rotation, and dragging."""
        if not self.active:
            return task.cont

        dt = self.base.clock.getDt()
        move_vec = (0, 0)  # Store movement in X, Y

        # Convert degrees to radians for rotation
        yaw_rad = self.yaw * (pi / 180.0)

        # Calculate forward and right movement directions based on yaw
        forward = (sin(yaw_rad), -cos(yaw_rad))  # Forward movement vector
        right = (cos(yaw_rad), sin(yaw_rad))  # Right movement vector

        # WASD-based movement (relative to camera yaw)
        if self.keys["down"]:
            move_vec = (move_vec[0] + forward[0] * self.pan_speed * dt, move_vec[1] + forward[1] * self.pan_speed * dt)
        if self.keys["up"]:
            move_vec = (move_vec[0] - forward[0] * self.pan_speed * dt, move_vec[1] - forward[1] * self.pan_speed * dt)
        if self.keys["left"]:
            move_vec = (move_vec[0] - right[0] * self.pan_speed * dt, move_vec[1] - right[1] * self.pan_speed * dt)
        if self.keys["right"]:
            move_vec = (move_vec[0] + right[0] * self.pan_speed * dt, move_vec[1] + right[1] * self.pan_speed * dt)

        # Apply movement to the pivot
        if move_vec != (0, 0):
            x0, y0, z0 = self.pivot.getPos()
            self.pivot.setPos(x0 + move_vec[0], y0 + move_vec[1], z0)
            self.update_camera_position()

        # Q/E-based rotation
        if self.keys["rotate_left"]:
            self.yaw += self.rotate_speed * dt
            self.update_camera_position()
        if self.keys["rotate_right"]:
            self.yaw -= self.rotate_speed * dt
            self.update_camera_position()

        # Mouse dragging (adjusted for rotation)
        if self.base.mouseWatcherNode.hasMouse():
            md = self.base.win.getPointer(0)
            x = md.getX()
            y = md.getY()
            delta_x = x - self.last_mouse_pos[0]
            delta_y = y - self.last_mouse_pos[1]

            if self.left_dragging:
                # Left-drag => rotate around pivot's heading
                rotation_factor = 0.1  # Slower rotation
                self.yaw -= delta_x * rotation_factor
                self.update_camera_position()

            elif self.right_dragging:
                # Right-drag => pan the pivot relative to rotation
                pan_factor = 0.02  # Adjust sensitivity
                move_x = (-delta_x * pan_factor) * cos(yaw_rad) - (delta_y * pan_factor) * sin(yaw_rad)
                move_y = (-delta_x * pan_factor) * sin(yaw_rad) + (delta_y * pan_factor) * cos(yaw_rad)

                x0, y0, z0 = self.pivot.getPos()
                self.pivot.setPos(x0 + move_x, y0 + move_y, z0)
                self.update_camera_position()

            # Store new mouse pos
            self.last_mouse_pos = (x, y)

        return task.cont
