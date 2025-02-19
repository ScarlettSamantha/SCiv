from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFileData
from lights import setup_lights
from camera import CivCamera
from managers.world import World
from managers.ui import ui
from managers.input import Input
from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties
from managers.config import ConfigManager   
# 1) Limit FPS to 60
class FlatHexExample(ShowBase):
    def __init__(self, config_mgr):
        # config_mgr must be applied BEFORE ShowBase to set up prc data
        ShowBase.__init__(self)

        self.config_mgr = config_mgr
        self.disableMouse()
        
        # Listen for window events (including moves / resizes)
        self.accept("window-event", self.on_window_event)

        # ---------------------------------------------------------------------
        # In-game initialization (your existing code)
        ui.base = self
        ui_manager = ui.get_instance()
        ui_manager.__setup__()

        input_manager = Input.get_instance({"base": self})
        input_manager.__setup__(self)
        input_manager.inject_into_camera()

        world = World.get_instance({"base": self})
        world.__setup__(self)
        world.generate(50, 50, 0.5, 1.5)

        if world.middle_x is None or world.middle_y is None:
            raise ValueError("Something very weird has happened.")

        # Middle target for the CivCamera
        self.middle_target = self.render.attachNewNode("middle_target")
        self.middle_target.setPos(world.middle_x, world.middle_y, 0)

        self.civ_camera = CivCamera(self, target=self.middle_target)
        setup_lights(self)
        
        # I18n system
        
        
        
        
        
        world.setup_hex_tiles()
        ui_manager.get_main_menu()
        ui_manager.map = world

        # ---------------------------------------------------------------------
        # Optionally: an example of toggling window modes at runtime
        # E.g., press F11 to toggle fullscreen
        self.accept("f11", self.toggle_fullscreen)

    def on_window_event(self, window=None):
        """
        Called whenever the window is moved, resized, minimized, etc.
        We capture the new x, y, w, h and save to config (if not in fullscreen).
        """
        if window is not None:
            props = window.getProperties()
            if props.hasOrigin() and props.hasSize():
                x = props.getXOrigin()
                y = props.getYOrigin()
                w = props.getXSize()
                h = props.getYSize()
                self.config_mgr.update_window_position_size(x, y, w, h)

    def toggle_fullscreen(self):
        """
        Example: Switch between fullscreen <-> windowed at runtime.
        """
        current_mode = self.config_mgr.config_data["window"].get("screen-mode", "windowed")
        new_mode = "fullscreen" if current_mode != "fullscreen" else "windowed"
        self.config_mgr.set_screen_mode(new_mode)
        
        # Now we must re-apply the config and adjust the window properties
        self.resetWindow()

    def resetWindow(self):
        """
        Safely close and re-open the window with new prc settings.
        """
        # 1) Re-apply config to Panda3D’s PRC
        self.config_mgr.apply_config_to_prc()
        
        # 2) Create new WindowProperties from the updated config
        props = WindowProperties.getDefault()
        # ShowBase.processMessages(0) might sometimes be used if changes aren't immediate

        # 3) Re-open the window
        self.win = self.openDefaultWindow(props=props, keepCamera=True) # noqa
    
config_mgr = ConfigManager("config.json")
config_mgr.apply_config_to_prc()

app = FlatHexExample(config_mgr)
app.run()
