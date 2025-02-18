from direct.showbase.ShowBase import NodePath
from math import pi, sin, cos
from direct.task import Task
from ui import update_camera_text
from ursina import camera
from math import sqrt, sin, cos, pi
from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, Vec4, TextNode, NodePath
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task
from panda3d.core import loadPrcFileData
from math import sin, cos, pi, sqrt
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    AmbientLight,
    DirectionalLight,
    Vec4,
    TextNode,
    KeyboardButton,
    loadPrcFileData,
)
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task


class CivCamera:
    """
    A camera controller that mimics a Civilization-style view.
    It supports:
      - A fixed pitch angle.
      - Panning using both arrow keys and WASD.
      - Mouse wheel zooming.
      - Re-centering to a designated middle target.
    """
    def __init__(self, base, target: NodePath = None):
        self.base = base

        # Initial zoom distance (controls how far the camera is from the pivot)
        self.zoom = 20.0  
        self.min_zoom = 10.0
        self.max_zoom = 50.0

        # Speeds (units per second for panning; fixed step for zoom)
        self.pan_speed = 20.0  
        self.zoom_speed = 2.0  

        # Fixed pitch angle (in degrees) for the camera
        self.pitch = 45.0  

        # If a target is provided, store it.
        self.target = target

        # Create a pivot node; if a target exists, position the pivot at the target.
        self.pivot = base.render.attachNewNode("camPivot")
        if self.target:
            self.pivot.setPos(self.target.getPos())
        else:
            self.pivot.setPos(0, 0, 0)

        # Reparent the camera to the pivot.
        self.base.camera.reparentTo(self.pivot)
        self.update_camera_position()

        # Dictionary to track key states for panning.
        self.keys = {"up": False, "down": False, "left": False, "right": False}

        self.setup_controls()
        self.base.taskMgr.add(self.update, "updateCivCameraTask")
        self.base.taskMgr.add(update_camera_text, "updateCameraText")

    def setup_controls(self):
        # Arrow keys for panning.
        self.base.accept("arrow_up",    self.set_key, ["up", True])
        self.base.accept("arrow_up-up", self.set_key, ["up", False])
        self.base.accept("arrow_down",    self.set_key, ["down", True])
        self.base.accept("arrow_down-up", self.set_key, ["down", False])
        self.base.accept("arrow_left",    self.set_key, ["left", True])
        self.base.accept("arrow_left-up", self.set_key, ["left", False])
        self.base.accept("arrow_right",    self.set_key, ["right", True])
        self.base.accept("arrow_right-up", self.set_key, ["right", False])
        # WASD keys for panning.
        self.base.accept("w",    self.set_key, ["up", True])
        self.base.accept("w-up", self.set_key, ["up", False])
        self.base.accept("s",    self.set_key, ["down", True])
        self.base.accept("s-up", self.set_key, ["down", False])
        self.base.accept("a",    self.set_key, ["left", True])
        self.base.accept("a-up", self.set_key, ["left", False])
        self.base.accept("d",    self.set_key, ["right", True])
        self.base.accept("d-up", self.set_key, ["right", False])
        # Mouse wheel for zooming.
        self.base.accept("wheel_up", self.zoom_in)
        self.base.accept("wheel_down", self.zoom_out)
        # Optional: recenter the camera onto the middle target when 'r' is pressed.
        self.base.accept("r", self.recenter)

    def set_key(self, key, value):
        self.keys[key] = value

    def zoom_in(self):
        self.zoom -= self.zoom_speed
        if self.zoom < self.min_zoom:
            self.zoom = self.min_zoom
        self.update_camera_position()

    def zoom_out(self):
        self.zoom += self.zoom_speed
        if self.zoom > self.max_zoom:
            self.zoom = self.max_zoom
        self.update_camera_position()

    def update_camera_position(self):
        """
        Update the camera's position relative to the pivot.
        With a fixed pitch, calculate:
          - Y offset = -zoom * cos(pitch)
          - Z offset = zoom * sin(pitch)
        Then, ensure the camera is looking at the pivot.
        """
        rad = self.pitch * (pi / 180.0)
        offset_y = -self.zoom * cos(rad)
        offset_z = self.zoom * sin(rad)
        self.base.camera.setPos(0, offset_y, offset_z)
        self.base.camera.lookAt(self.pivot)

    def update(self, task):
        """
        Update camera panning each frame based on the current key states.
        """
        dt = globalClock.getDt()
        dx = 0
        dy = 0
        if self.keys["up"]:
            dy += self.pan_speed * dt
        if self.keys["down"]:
            dy -= self.pan_speed * dt
        if self.keys["left"]:
            dx -= self.pan_speed * dt
        if self.keys["right"]:
            dx += self.pan_speed * dt

        if dx or dy:
            cur_pos = self.pivot.getPos()
            self.pivot.setPos(cur_pos.getX() + dx,
                              cur_pos.getY() + dy,
                              cur_pos.getZ())
            self.update_camera_position()
        return task.cont

    def recenter(self):
        """
        Recenter the camera's pivot to the middle target's position.
        """
        if self.target:
            self.pivot.setPos(self.target.getPos())
            self.update_camera_position()

