from math import pi, cos, sin
from panda3d.core import NodePath


class CivCamera:
    """
    Modified camera controller:
      - Left-drag => rotate around pivot (slower)
      - Right-drag => pan/move
      - Q/E => rotate around pivot by rotation_speed
      - Mouse wheel => zoom
      - R => recenter
      - WASD/arrow keys => optional panning
    """

    def __init__(self, base):
        self.base = base
        self.active = True

        # Zoom parameters
        self.zoom = 20.0
        self.min_zoom = 10.0
        self.max_zoom = 50.0
        self.zoom_speed = 2.0

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
        self.base.taskMgr.add(self.update, "updateCivCameraTask")

    # -------------------------------------------------------------------------
    #  Setup Controls
    # -------------------------------------------------------------------------
    def setup_controls(self):
        """Bind keys/mouse for panning, zooming, rotating, recentering, etc."""

        # WASD / arrow keys for panning
        self.base.accept("arrow_up", self.set_key, ["up", True])
        self.base.accept("arrow_up-up", self.set_key, ["up", False])
        self.base.accept("arrow_down", self.set_key, ["down", True])
        self.base.accept("arrow_down-up", self.set_key, ["down", False])
        self.base.accept("arrow_left", self.set_key, ["left", True])
        self.base.accept("arrow_left-up", self.set_key, ["left", False])
        self.base.accept("arrow_right", self.set_key, ["right", True])
        self.base.accept("arrow_right-up", self.set_key, ["right", False])

        self.base.accept("w", self.set_key, ["up", True])
        self.base.accept("w-up", self.set_key, ["up", False])
        self.base.accept("s", self.set_key, ["down", True])
        self.base.accept("s-up", self.set_key, ["down", False])
        self.base.accept("a", self.set_key, ["left", True])
        self.base.accept("a-up", self.set_key, ["left", False])
        self.base.accept("d", self.set_key, ["right", True])
        self.base.accept("d-up", self.set_key, ["right", False])

        # Q/E for rotation
        self.base.accept("q", self.set_key, ["rotate_left", True])
        self.base.accept("q-up", self.set_key, ["rotate_left", False])
        self.base.accept("e", self.set_key, ["rotate_right", True])
        self.base.accept("e-up", self.set_key, ["rotate_right", False])

        # Mouse wheel for zoom
        self.base.accept("wheel_up", self.zoom_in)
        self.base.accept("wheel_down", self.zoom_out)

        # Recenter pivot
        self.base.accept("r", self.recenter)

        # Left mouse => rotate
        self.base.accept("mouse1", self.start_left_drag)
        self.base.accept("mouse1-up", self.stop_left_drag)

        # Right mouse => pan (drag to move)
        self.base.accept("mouse3", self.start_right_drag)
        self.base.accept("mouse3-up", self.stop_right_drag)

    def set_key(self, key, value):
        self.keys[key] = value

    # -------------------------------------------------------------------------
    #  Zoom
    # -------------------------------------------------------------------------
    def zoom_in(self):
        self.zoom = max(self.min_zoom, self.zoom - self.zoom_speed)
        self.update_camera_position()

    def zoom_out(self):
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
        self.reset_pivot_position()
        # Reset orientation/zoom if desired:
        self.yaw = 0.0
        self.zoom = 20.0
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

        # Key-based panning in X/Y
        dx, dy = 0.0, 0.0
        if self.keys["up"]:
            dy += self.pan_speed * dt
        if self.keys["down"]:
            dy -= self.pan_speed * dt
        if self.keys["left"]:
            dx -= self.pan_speed * dt
        if self.keys["right"]:
            dx += self.pan_speed * dt

        if (dx != 0) or (dy != 0):
            x0, y0, z0 = self.pivot.getPos()
            self.pivot.setPos(x0 + dx, y0 + dy, z0)
            self.update_camera_position()

        # Q/E-based rotation
        if self.keys["rotate_left"]:
            self.yaw -= self.rotate_speed * dt
            self.update_camera_position()
        if self.keys["rotate_right"]:
            self.yaw += self.rotate_speed * dt
            self.update_camera_position()

        # Mouse dragging
        if self.base.mouseWatcherNode.hasMouse():
            md = self.base.win.getPointer(0)
            x = md.getX()
            y = md.getY()
            delta_x = x - self.last_mouse_pos[0]
            delta_y = y - self.last_mouse_pos[1]

            if self.left_dragging:
                # Left-drag => rotate around pivot's heading
                # We'll do direct offset => yaw change
                # Lower factor to reduce speed
                rotation_factor = 0.1  # Slower rotation
                self.yaw -= delta_x * rotation_factor
                self.update_camera_position()

            elif self.right_dragging:
                # Right-drag => pan the pivot in XY plane
                pan_factor = 0.02  # Tweak for sensitivity
                x0, y0, z0 = self.pivot.getPos()
                new_x = x0 - (delta_x * pan_factor)
                new_y = y0 + (delta_y * pan_factor)
                self.pivot.setPos(new_x, new_y, z0)
                self.update_camera_position()

            # Store new mouse pos
            self.last_mouse_pos = (x, y)

        return task.cont
