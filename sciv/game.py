#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from typing import TYPE_CHECKING, cast

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
os.chdir(SCRIPT_DIR)

import pathlib
from logging import Logger

import simplepbr
from direct.showbase.Messenger import Messenger
from direct.showbase.ShowBase import ShowBase
from helpers.cache import Cache
from helpers.direct_loading_screen import LoadingScreen
from helpers.os import WindowsHelper
from helpers.paths import PathsHelper
from kivy.config import Config
from managers.config import ConfigManager
from managers.i18n import I18nManager, set_i18n
from managers.input import Input
from managers.log import LogManager
from managers.unit import UnitManager
from panda3d.core import loadPrcFile
from panda3d_kivy import monkey  # type: ignore

Config.set("modules", "inspector", "")  # type: ignore
Config.set("graphics", "gl_backend", "angle_sdl2")  # type: ignore

monkey.patch_kivy()  # attach Kivy to the Panda3D window # type: ignore

loadPrcFile("config.prc")  # Load the Panda3D configuration file

if TYPE_CHECKING:
    from panda3d.core import GraphicsWindow
    from system.camera import Camera


class OpenCiv(ShowBase):
    def __init__(self):
        from helpers.cache import Cache
        from helpers.debug import Debug
        from managers.assets import AssetManager
        from managers.ui import ui
        from system.camera import Camera
        from system.lights import setup_lights
        from system.vars import DEBUG, __version__, get_git_commit

        self.debug: bool = DEBUG
        Debug.debug = self.debug

        self.version: str = __version__
        self.commit: str = get_git_commit()

        # Configuration manager setup
        config_mgr = ConfigManager()
        ConfigManager.set_singleton_instance(config_mgr)

        if (
            self.debug
            and (enabled := config_mgr.get_by_key(("debug", "sentry", "enable"), None)) is not None
            and enabled is True
            and (sentry_dsn := config_mgr.get_by_key(("debug", "sentry", "dsn"), None)) is not None
            and sentry_dsn.strip() != ""
        ):
            from helpers.debug import Debug

            self.sentry = Debug.init_sentry(sentry_dsn)

        # Initialize base ShowBase
        ShowBase.__init__(self)
        config_mgr.apply_config_to_prc()
        config_mgr.disable_vsync()
        self.config_manager: ConfigManager = config_mgr
        self.base_path: pathlib.Path = pathlib.Path.cwd().absolute()

        if WindowsHelper.is_windows():
            WindowsHelper.load_dll(str(self.base_path / "libs/win-amd64/glew32.dll"))

        # Loading screen
        loading_screen = LoadingScreen(
            self, [str(self.base_path / "assets" / "logo.png")], 15, on_continue=self.on_loading_screen_continue
        )
        loading_screen.next_stage("Loading OpenCiv")
        simplepbr.init()
        loading_screen.next_stage("Loading Panda3D")
        self.disableMouse()

        # Logging
        loading_screen.next_stage("Setting up logging")
        self.logger: LogManager = LogManager.get_singleton_instance()
        self.logger.setup_loggers()

        # Cache
        Cache.set_showbase_instance(self)
        self.engine_logger: Logger = self.logger.engine.getChild("Main")
        self.engine_logger.info("Starting OpenCiv")

        # Messenger
        loading_screen.next_stage("Loading Messenger")
        self.messenger: Messenger = Messenger()

        # Internationalization
        loading_screen.next_stage(f"Loading translations for {self.config_manager.get_language()}")
        self.engine_logger.info("Setting up i18n")
        base_file_path: pathlib.Path = pathlib.Path(__file__).parent.absolute()
        PathsHelper.base_path = str(base_file_path)
        self.i18n = I18nManager(str(base_file_path / "i18n"), self.config_manager.get_language(), True)
        Cache.set_i18n_instance(self.i18n)
        set_i18n(self.i18n)

        # Generate assets
        loading_screen.next_stage("Generating assets")
        self.engine_logger.info("Generating non-static assets")
        self.generate_non_static_assets()

        # Input manager
        loading_screen.next_stage("Setting up input manager")
        self.engine_logger.info("Setting up input manager")
        self.input_manager = Input(self)
        Input.set_singleton_instance(self.input_manager)
        self.input_manager.inject_into_camera()

        from managers.game import Game

        # Asset manager
        self.engine_logger.info("Setting up asset manager")
        loading_screen.next_stage("Setting up asset manager")
        self.asset_manager: AssetManager = AssetManager.get_singleton_instance()
        AssetManager.set_singleton_instance(self.asset_manager)
        self.asset_manager.set_base(self)

        # Camera
        loading_screen.next_stage("Setting up camera")
        self.engine_logger.info("Setting up camera")
        self.game_camera = Camera(self)
        Camera.set_singleton_instance(self.game_camera)
        self.game_camera.register()

        # Lights
        loading_screen.next_stage("Setting up lights")
        self.engine_logger.info("Setting up lights")
        setup_lights(self)

        # Game manager
        self.engine_logger.info("Setting up game manager")
        loading_screen.next_stage("Setting up game manager")
        self.game_manager_instance = Game(self, self.game_camera)
        Game.set_singleton_instance(self.game_manager_instance)

        # World
        self.engine_logger.info("Setting up world")
        loading_screen.next_stage("Setting up world")
        from managers.world import World

        self.world = World.get_singleton_instance()
        self.world.__setup__()

        # Unit manager
        loading_screen.next_stage("Setting up unit manager")
        self.engine_logger.info("Setting up unit manager")
        self.unit_manager = UnitManager(self)
        UnitManager.set_singleton_instance(self.unit_manager)

        # UI manager
        self.engine_logger.info("Setting up UI manager")
        loading_screen.next_stage("Setting up kivy")
        self.ui_manager = ui(self)
        self.ui_manager.map = self.world

        # Continue or show "Ready"
        if config_mgr.get_by_key(("qol", "intro_skip")):
            self.on_loading_screen_continue()
            loading_screen.destroy()
        else:
            loading_screen.next_stage("Ready")

    def window(self) -> "GraphicsWindow":
        from panda3d.core import GraphicsWindow

        return cast(GraphicsWindow, self.win)

    def get_camera(self) -> "Camera":
        return self.game_camera

    def __getstate__(self):
        return None

    def on_loading_screen_continue(self):
        from managers.ui import ui

        self.ui_manager.kivy_setup()
        ui.set_singleton_instance(self.ui_manager)

        self.messenger.send("system.main.ready")

    def generate_non_static_assets(self, force: bool = False) -> None:
        from helpers.debug import Debug
        from helpers.paths import PathsHelper
        from system.atlas import AtlasGenerator

        icon_tile_set = ConfigManager.get_singleton_instance().get_default(("assets", "icon-tile-set"), "default")
        terrain_tile_set = ConfigManager.get_singleton_instance().get_default(("assets", "tile-set-tiles"), "default")
        base_path = pathlib.Path(PathsHelper.get_data_dir()) / "assets" / "generated"

        icon_generator = AtlasGenerator(
            input_dir=[
                pathlib.Path(__file__).parent / "assets" / "icons" / icon_tile_set,
                base_path / "icons" / "resources",
            ],
            output_image=base_path / "generated" / "icons" / "atlas.png",
            output_mapping=base_path / "generated" / "icons" / "mapping.json",
            icon_size=(
                self.config_manager.get_by_key(("assets", "icon_resolution_x")),
                self.config_manager.get_by_key(("assets", "icon_resolution_y")),
            ),
            max_icons=512,
            atlas_columns=16,
        )

        terrain_atlas = AtlasGenerator(
            input_dir=pathlib.Path(__file__).parent / "assets" / "terrain" / terrain_tile_set,
            output_image=base_path / "terrain" / "atlas.png",
            output_mapping=base_path / "terrain" / "mapping.json",
            icon_size=(
                self.config_manager.get_by_key(("assets", "terrain_resolution_x")),
                self.config_manager.get_by_key(("assets", "terrain_resolution_y")),
            ),
            max_icons=128,
            atlas_columns=16,
        )

        if force or Debug.system_asset_generation():
            self.engine_logger.info("Forcing asset generation")
            icon_generator.run(force=force)
            terrain_atlas.run(force=force)
        else:
            if not icon_generator.exists():
                self.engine_logger.info("Icon atlas does not exist, generating assets")
                icon_generator.run(force=force)
            else:
                self.engine_logger.info("Icon atlas exists, skipping generation loading cache")
                icon_generator.load_caches()

            if not terrain_atlas.exists():
                self.engine_logger.info("Terrain atlas does not exist, generating assets")
                terrain_atlas.run(force=force)
            else:
                self.engine_logger.info("Terrain atlas exists, skipping generation loading cache")
                terrain_atlas.load_caches()

        Cache.set_icon_atlas(icon_generator)
        Cache.set_terrain_atlas(terrain_atlas)

    def get_base_path(self) -> pathlib.Path:
        return self.base_path

    def get_child_logger(self, name: str) -> Logger:
        return self.logger.engine.getChild(name)


if __name__ == "__main__":
    app = OpenCiv()

    try:
        app.run()
    except (SystemExit, AssertionError):
        print("Goodbye :-)")
