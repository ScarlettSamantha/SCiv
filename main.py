from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFileData
from lights import setup_lights
from camera import CivCamera
from managers.world import World
from managers.ui import ui
from managers.input import Input

# 1) Limit FPS to 60
loadPrcFileData("", "clock-mode limited")       # switch clock to "limited" mode
loadPrcFileData("", "clock-frame-rate 60")      # set max 60 FPS

# 2) Change default window position
loadPrcFileData("", "win-origin 30 100")

# 3) Optionally change window size, title, etc.
loadPrcFileData("", "win-size 1920 1080")
loadPrcFileData("", "window-title My Panda3D App")

class FlatHexExample(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        # Disable the default mouse-based camera controls immediately.
        self.disableMouse()

        ui_manager = ui.get_instance({"base": self})
        ui_manager.__setup__(self)
        
        input_manager = Input.get_instance({"base": self})
        input_manager.__setup__(self)
        input_manager.inject_into_camera()
        
        world = World.get_instance({"base": self})
        world.__setup__(self)
        world.generate(50, 50, 0.5, 1.5)
        
        if world.middle_x is None or world.middle_y is None:
            raise ValueError("Something very weird has happend.")
        
        # Create a NodePath for the middle target.
        self.middle_target = self.render.attachNewNode("middle_target")
        self.middle_target.setPos(world.middle_x, world.middle_y, 0)

        # Initialize the Civ-style camera with the middle target.
        self.civ_camera = CivCamera(self, target=self.middle_target)

        setup_lights(self)
        world.setup_hex_tiles()
        ui_manager.get_main_menu()
    
app = FlatHexExample()
app.run()
