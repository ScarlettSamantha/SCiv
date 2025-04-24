import pathlib
from logging import Logger

import simplepbr
from direct.showbase.Messenger import Messenger
from direct.showbase.ShowBase import ShowBase
from panda3d.core import load_prc_file  # type: ignore
from panda3d_kivy import monkey

from helpers.cache import Cache
from managers.config import ConfigManager
from managers.i18n import I18nManager, set_i18n
from managers.input import Input
from managers.log import LogManager
from managers.unit import Unit

monkey.patch_kivy()  # this is needed to make kivy work with panda3d we need to attach the window to the current panda3d window


class SCIV(ShowBase):
    def __init__(self):
        from managers.assets import AssetManager
        from managers.ui import ui
        from managers.world import World
        from system.camera import Camera
        from system.lights import setup_lights
        from version import __version__

        self.version = __version__
        # Get the commit hash from git if available, otherwise 'Unknown'
        self.commit = self._get_git_commit()

        # config_mgr must be applied BEFORE ShowBase to set up prc data
        ShowBase.__init__(self)
        simplepbr.init()
        self.disableMouse()
        Cache.set_showbase_instance(self)

        self.base_path = pathlib.Path(__file__).parent.absolute()
        # Base messenger object from panda3d
        self.messenger: Messenger = Messenger()

        # My logger that is used in the entire project.
        self.logger: LogManager = LogManager.get_singleton_instance()
        self.logger.setup_loggers()

        self.engine_logger: Logger = self.logger.engine.getChild("Main")
        self.engine_logger.info("Starting OpenCiv")
        # I18n system
        self.engine_logger.info("Setting up i18n")
        base_file_path = pathlib.Path(__file__).parent.absolute()
        self.i18n = I18nManager(str(base_file_path / "i18n"), "en_EN", True)
        set_i18n(self.i18n)

        # Start loading and generating assets
        self.engine_logger.info("Generating non-static assets")
        self.generate_non_static_assets()

        # Manager load order is very important DO NOT CHANGE.
        self.engine_logger.info("Setting up input manager")
        self.input_manager = Input(self)
        Input.set_singleton_instance(self.input_manager)
        self.input_manager.inject_into_camera()

        from managers.game import Game

        self.engine_logger.info("Setting up game manager")
        config_mgr = ConfigManager()
        ConfigManager.set_singleton_instance(config_mgr)
        config_mgr.apply_config_to_prc()

        self.engine_logger.info("Setting up asset manager")
        self.asset_manager: AssetManager = AssetManager.get_singleton_instance()
        AssetManager.set_singleton_instance(self.asset_manager)
        self.asset_manager.set_base(self)

        self.engine_logger.info("Setting up camera")
        self.civ_camera = Camera(self)
        Camera.set_singleton_instance(self.civ_camera)
        self.civ_camera.register()

        self.engine_logger.info("Setting up lights")
        setup_lights(self)

        # Init game base system
        self.engine_logger.info("Setting up game manager")
        self.game_manager_instance = Game(self, self.civ_camera)
        Game.set_singleton_instance(self.game_manager_instance)

        self.engine_logger.info("Setting up world")
        self.world = World.get_singleton_instance()
        self.world.__setup__()

        self.engine_logger.info("Setting up unit manager")
        self.unit_manager = Unit(self)
        Unit.set_singleton_instance(self.unit_manager)

        self.engine_logger.info("Setting up UI manager")
        self.ui_manager = ui(self)
        self.ui_manager.map = self.world
        self.ui_manager.kivy_setup()
        self.ui_manager.register()
        ui.set_singleton_instance(self.ui_manager)

        self.messenger.send("system.main.ready")

    def generate_non_static_assets(self):
        from system.atlas import AtlasGenerator

        icon_generator = AtlasGenerator(
            input_dir=pathlib.Path(__file__).parent / "assets" / "icons",
            output_image=pathlib.Path(__file__).parent / "assets" / "generated" / "icons" / "atlas.png",
            output_mapping=pathlib.Path(__file__).parent / "assets" / "generated" / "icons" / "mapping.json",
            icon_size=(128, 128),
            max_icons=512,
            atlas_columns=16,
        )
        icon_generator.run()
        Cache.set_atlas(icon_generator)

    def _get_git_commit(self) -> str:
        """
        Retrieve the current git commit hash if the git package is available.

        Returns "Unknown" if git is not installed or the repository isn't available.
        """
        try:
            import git  # type: ignore

            repo = git.Repo(search_parent_directories=True)  # type: ignore
            return repo.head.object.hexsha  # type: ignore
        except Exception:
            return "Unknown"

    def get_base_path(self) -> pathlib.Path:
        return self.base_path

    def get_child_logger(self, name: str) -> Logger:
        return self.logger.engine.getChild(name)


if __name__ == "__main__":
    load_prc_file("config.prc")
    app = SCIV()

    try:
        app.run()
    except SystemExit:
        print("Goodbye :-)")
