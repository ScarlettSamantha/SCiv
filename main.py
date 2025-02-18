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

# 1) Limit FPS to 60
loadPrcFileData("", "clock-mode limited")       # switch clock to "limited" mode
loadPrcFileData("", "clock-frame-rate 60")      # set max 60 FPS

# 2) Change default window position
loadPrcFileData("", "win-origin 30 100")

# 3) Optionally change window size, title, etc.
loadPrcFileData("", "win-size 1920 1080")
loadPrcFileData("", "window-title My Panda3D App")


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
        
        self.base.accept("arrow_up", self.onUpPress)
        self.base.accept("arrow_up-up", self.onUpRelease)

    def onUpPress(self):
        print("Arrow Up Pressed")

    def onUpRelease(self):
        print("Arrow Up Released")

    def set_key(self, key, value):
        print(f"Key: {key}, Value: {value}")  # Quick debug
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


class FlatHexExample(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Disable the default mouse-based camera controls immediately.
        self.disableMouse()

        # Calculate grid parameters.
        hex_radius = 0.5  
        col_spacing = 1.5 * hex_radius
        row_spacing = sqrt(3) * hex_radius
        cols = 5
        rows = 5

        # Compute the middle of the grid.
        middle_x = ((cols - 1) * col_spacing) / 2.0
        middle_y = ((rows - 1) * row_spacing) / 2.0

        # Create a NodePath for the middle target.
        self.middle_target = self.render.attachNewNode("middle_target")
        self.middle_target.setPos(middle_x, middle_y, 0)

        # Initialize the Civ-style camera with the middle target.
        self.civ_camera = CivCamera(self, target=self.middle_target)

        # Create onscreen text to display the camera position.
        self.cam_text = OnscreenText(
            text="",           # updated every frame
            parent=self.a2dTopLeft,
            scale=0.05,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
            pos=(0.05, -0.07),
            mayChange=True
        )

        self.setup_lights()
        self.setup_hex_tiles()
        self.taskMgr.add(self.update_camera_text, "updateCameraTextTask")
        self.taskMgr.add(self.update_task, "civCamUpdate")
    
    def setup_hex_tiles(self):
        """Set up a grid of hexagon tiles."""
        hex_radius = 0.5  
        col_spacing = 1.5 * hex_radius
        row_spacing = sqrt(3) * hex_radius

        rows = 200
        cols = 200

        # Load and adjust the hex model.
        hex_model = self.loader.loadModel("hex_tile.obj")
        hex_model.setScale(0.48)
        # Rotate the model so it lies flat.
        hex_model.setHpr(180, 90, 90)

        for col in range(cols):
            for row in range(rows):
                x = col * col_spacing
                if col % 2 == 1:
                    y = row * row_spacing + (row_spacing * 0.5)
                else:
                    y = row * row_spacing
                new_hex = hex_model.copyTo(self.render)
                new_hex.setPos(x, y, 0)
    
    def update_camera_text(self, task):
        """Display the current camera position onscreen."""
        pos = self.camera.getPos(self.render)
        self.cam_text.setText(f"Camera Position: {pos}")
        return Task.cont
    
    def update_task(self, task):
        """Polls keyboard input each frame and moves camera pivot accordingly."""
        dt = globalClock.getDt()

        # The mouseWatcherNode is where Panda3D collects keyboard/mouse states.
        mw = self.mouseWatcherNode

        # Basic arrow-key movement
        dx = 0
        dy = 0
        if mw.isButtonDown(KeyboardButton.up()):
            dy += self.civ_camera.pan_speed * dt
        if mw.isButtonDown(KeyboardButton.down()):
            dy -= self.civ_camera.pan_speed * dt
        if mw.isButtonDown(KeyboardButton.left()):
            dx -= self.civ_camera.pan_speed * dt
        if mw.isButtonDown(KeyboardButton.right()):
            dx += self.civ_camera.pan_speed * dt

        # WASD
        if mw.isButtonDown(KeyboardButton.asciiKey("w")):
            dy += self.civ_camera.pan_speed * dt
        if mw.isButtonDown(KeyboardButton.asciiKey("s")):
            dy -= self.civ_camera.pan_speed * dt
        if mw.isButtonDown(KeyboardButton.asciiKey("a")):
            dx -= self.civ_camera.pan_speed * dt
        if mw.isButtonDown(KeyboardButton.asciiKey("d")):
            dx += self.civ_camera.pan_speed * dt

        # Scroll wheel zoom in/out (not event-based, but we can check the wheel "buttons")
        # On many systems, wheel_up is considered button 4, wheel_down is button 5, etc.
        # But often these do NOT come through isButtonDown(...) well—so you may do events for wheel.
        # For demonstration: check bracket keys for manual zoom.
        if mw.isButtonDown(KeyboardButton.asciiKey("[")):
            self.zoom = max(self.zoom - self.civ_camera.zoom_speed, self.civ_camera.min_zoom)
            self.civ_camera.update_camera_position()
        if mw.isButtonDown(KeyboardButton.asciiKey("]")):
            self.zoom = min(self.zoom + self.civ_camera.zoom_speed, self.civ_camera.max_zoom)
            self.civ_camera.update_camera_position()

        # Move the pivot
        if dx != 0 or dy != 0:
            pos = self.civ_camera.pivot.getPos()
            self.civ_camera.pivot.setPos(pos.x + dx, pos.y + dy, pos.z)
            self.civ_camera.update_camera_position()

        return Task.cont

    def setup_lights(self):
        # Ambient light.
        ambient_light = AmbientLight("ambient")
        ambient_light.setColor(Vec4(0.4, 0.4, 0.4, 1))
        ambient_node = self.render.attachNewNode(ambient_light)

        # Directional light.
        directional_light = DirectionalLight("directional")
        directional_light.setColor(Vec4(0.9, 0.9, 0.8, 1))
        directional_node = self.render.attachNewNode(directional_light)
        directional_node.setHpr(45, -60, 0)

        self.render.setLight(ambient_node)
        self.render.setLight(directional_node)


# Run the demo
app = FlatHexExample()
app.run()
