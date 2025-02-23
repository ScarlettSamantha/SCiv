from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties

from lights import setup_lights
from camera import CivCamera

from managers.world import World
from managers.unit import Unit
from managers.ui import ui
from managers.input import Input
from managers.config import ConfigManager
from managers.i18n import _i18n, set_i18n
from managers.game import Game
import pathlib
import simplepbr


class Openciv(ShowBase):
    def __init__(self, config_mgr):
        # config_mgr must be applied BEFORE ShowBase to set up prc data
        ShowBase.__init__(self)
        simplepbr.init()
        self.config_mgr = config_mgr
        self.disableMouse()

        base_file_path = pathlib.Path(__file__).parent.absolute()
        self.i18n = _i18n(base_file_path / "i18n", "en_EN", True)
        set_i18n(self.i18n)

        # Listen for window events (including moves / resizes)
        self.accept("window-event", self.on_window_event)

        # Manager load order is very important DO NOT CHANGE.
        self.input_manager = Input(self)
        Input._set_instance(self.input_manager)
        self.input_manager.inject_into_camera()

        # I18n system

        self.civ_camera = CivCamera(self)
        CivCamera._set_instance(self.civ_camera)
        self.civ_camera.register()

        setup_lights(self)

        # Init game base system

        self.world = World.get_instance()
        self.world.__setup__(self)

        self.ui_manager = ui(self)
        ui._set_instance(self.ui_manager)
        self.ui_manager.get_main_menu()
        self.ui_manager.map = self.world

        self.unit_manager = Unit(self)
        Unit._set_instance(self.unit_manager)

        self.game_manager_instance = Game(self, self.civ_camera)
        Game._set_instance(self.game_manager_instance)
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
        self.openDefaultWindow(props=props, keepCamera=True)  # noqa


config_mgr = ConfigManager("config.json")
config_mgr.apply_config_to_prc()

app = Openciv(config_mgr)
app.run()
