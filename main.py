from logging import Logger
from direct.showbase.ShowBase import ShowBase
from direct.showbase.Messenger import Messenger
from lights import setup_lights
from camera import CivCamera

from managers.log import LogManager
from managers.unit import Unit

from managers.input import Input
from managers.config import ConfigManager
from managers.i18n import _i18n, set_i18n

import pathlib
import simplepbr
from panda3d.core import ClockObject, load_prc_file


class Openciv(ShowBase):
    def __init__(
        self,
    ):
        from managers.world import World
        from managers.ui import ui

        # config_mgr must be applied BEFORE ShowBase to set up prc data
        ShowBase.__init__(self)
        simplepbr.init()
        self.disableMouse()

        # Base messenger object from panda3d
        self.messenger: Messenger = Messenger()

        # My logger that is used in the entire project.
        self.logger: LogManager = LogManager.get_instance()
        self.logger.setup_loggers()

        self.engine_logger: Logger = self.logger.engine.getChild("Main")
        self.engine_logger.info("Starting OpenCiv")
        # I18n system
        self.engine_logger.info("Setting up i18n")
        base_file_path = pathlib.Path(__file__).parent.absolute()
        self.i18n = _i18n(str(base_file_path / "i18n"), "en_EN", True)
        set_i18n(self.i18n)

        # Manager load order is very important DO NOT CHANGE.
        self.engine_logger.info("Setting up input manager")
        self.input_manager = Input(self)
        Input._set_instance(self.input_manager)
        self.input_manager.inject_into_camera()

        from managers.game import Game

        self.engine_logger.info("Setting up game manager")
        config_mgr = ConfigManager()
        ConfigManager._set_instance(config_mgr)
        config_mgr.apply_config_to_prc()

        self.engine_logger.info("Setting up camera")
        self.civ_camera = CivCamera(self)
        CivCamera._set_instance(self.civ_camera)
        self.civ_camera.register()

        self.engine_logger.info("Setting up lights")
        setup_lights(self)

        self.engine_logger.info("Setting up world")
        self.world = World.get_instance()
        self.world.__setup__(self)

        # Init game base system
        self.engine_logger.info("Setting up game manager")
        self.game_manager_instance = Game(self, self.civ_camera)
        Game._set_instance(self.game_manager_instance)

        self.engine_logger.info("Setting up UI manager")
        self.ui_manager = ui(self)
        self.ui_manager.kivy_setup()
        self.ui_manager.register()
        ui._set_instance(self.ui_manager)

        self.ui_manager.map = self.world

        self.engine_logger.info("Setting up unit manager")
        self.unit_manager = Unit(self)
        Unit._set_instance(self.unit_manager)
        self.messenger.send("system.main.ready")


if __name__ == "__main__":
    globalClock = ClockObject.getGlobalClock()  # Removes frame sync
    globalClock.setFrameRate(144)
    load_prc_file("config.prc")
    app = Openciv()

    try:
        app.run()
    except SystemExit:
        print("Goodbye :-)")
