#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

import pathlib
from logging import Logger

import simplepbr
from direct.showbase.Messenger import Messenger
from direct.showbase.ShowBase import ShowBase
from kivy.config import Config

Config.set("modules", "inspector", "")
from panda3d_kivy import monkey
from helpers.cache import Cache
from helpers.direct_loading_screen import LoadingScreen
from managers.config import ConfigManager
from managers.i18n import I18nManager, set_i18n
from managers.input import Input
from managers.log import LogManager
from managers.unit import UnitManager

os.chdir(os.path.dirname(os.path.abspath(__file__)))
monkey.patch_kivy()  # this is needed to make kivy work with panda3d we need to attach the window to the current panda3d window


class SCIV(ShowBase):
    def __init__(self, debug: bool = False):
        from managers.assets import AssetManager
        from managers.ui import ui
        from managers.world import World
        from system.camera import Camera
        from system.lights import setup_lights
        from version import __version__

        self.debug = debug

        self.version = __version__
        # Get the commit hash from git if available, otherwise 'Unknown'
        self.commit = self._get_git_commit()

        # config_mgr must be applied BEFORE ShowBase to set up prc data
        ShowBase.__init__(self)
        config_mgr = ConfigManager()
        config_mgr.__setup__()
        ConfigManager.set_singleton_instance(config_mgr)
        config_mgr.apply_config_to_prc()

        loading_screen: LoadingScreen = LoadingScreen(
            self, ["assets/logo.png"], 15, on_continue=self.on_loading_screen_continue
        )
        loading_screen.next_stage("Loading OpenCiv")
        simplepbr.init()
        loading_screen.next_stage("Loading Panda3D")
        self.disableMouse()
        Cache.set_showbase_instance(self)

        loading_screen.next_stage("Loading Messenger")
        self.base_path = pathlib.Path(__file__).parent.absolute()
        # Base messenger object from panda3d
        self.messenger: Messenger = Messenger()

        loading_screen.next_stage("Setting up logging")
        self.logger: LogManager = LogManager.get_singleton_instance()
        self.logger.setup_loggers()

        self.engine_logger: Logger = self.logger.engine.getChild("Main")
        self.engine_logger.info("Starting OpenCiv")

        # I18n system
        loading_screen.next_stage("Loading translations for English(en_EN)")
        self.engine_logger.info("Setting up i18n")
        base_file_path = pathlib.Path(__file__).parent.absolute()
        self.i18n = I18nManager(str(base_file_path / "i18n"), "en_EN", True)
        set_i18n(self.i18n)

        # Start loading and generating assets
        loading_screen.next_stage("Generating assets")
        self.engine_logger.info("Generating non-static assets")
        self.generate_non_static_assets()

        # Manager load order is very important DO NOT CHANGE.
        loading_screen.next_stage("Setting up input manager")
        self.engine_logger.info("Setting up input manager")
        self.input_manager = Input(self)
        Input.set_singleton_instance(self.input_manager)
        self.input_manager.inject_into_camera()

        from managers.game import Game

        self.engine_logger.info("Setting up asset manager")
        loading_screen.next_stage("Setting up asset manager")
        self.asset_manager: AssetManager = AssetManager.get_singleton_instance()
        AssetManager.set_singleton_instance(self.asset_manager)
        self.asset_manager.set_base(self)

        loading_screen.next_stage("Setting up camera")
        self.engine_logger.info("Setting up camera")
        self.civ_camera = Camera(self)
        Camera.set_singleton_instance(self.civ_camera)
        self.civ_camera.register()

        loading_screen.next_stage("Setting up lights")
        self.engine_logger.info("Setting up lights")
        setup_lights(self)

        # Init game base system
        self.engine_logger.info("Setting up game manager")
        loading_screen.next_stage("Setting up game manager")
        self.game_manager_instance = Game(self, self.civ_camera)
        Game.set_singleton_instance(self.game_manager_instance)

        self.engine_logger.info("Setting up world")
        loading_screen.next_stage("Setting up world")
        self.world = World.get_singleton_instance()
        self.world.__setup__()

        loading_screen.next_stage("Setting up unit manager")
        self.engine_logger.info("Setting up unit manager")
        self.unit_manager = UnitManager(self)
        UnitManager.set_singleton_instance(self.unit_manager)

        self.engine_logger.info("Setting up UI manager")
        loading_screen.next_stage("Setting up kivy")
        self.ui_manager = ui(self)
        self.ui_manager.map = self.world

        if config_mgr.get_by_key("qol", "intro_skip"):
            self.on_loading_screen_continue()
            loading_screen.destroy()
        else:
            loading_screen.next_stage("Ready")  # This will show the ready button

    def on_loading_screen_continue(self):
        from managers.ui import ui

        self.ui_manager.kivy_setup()
        ui.set_singleton_instance(self.ui_manager)

        self.messenger.send("system.main.ready")

    def generate_non_static_assets(self):
        from system.atlas import AtlasGenerator

        icon_generator = AtlasGenerator(
            input_dir=[
                pathlib.Path(__file__).parent / "assets" / "icons",
                pathlib.Path(__file__).parent / "assets" / "generated" / "icons" / "resources",
            ],
            output_image=pathlib.Path(__file__).parent / "assets" / "generated" / "icons" / "atlas.png",
            output_mapping=pathlib.Path(__file__).parent / "assets" / "generated" / "icons" / "mapping.json",
            icon_size=(128, 128),
            max_icons=512,
            atlas_columns=16,
        )
        icon_generator.run()

        terrain_atlas = AtlasGenerator(
            input_dir=pathlib.Path(__file__).parent / "assets" / "terrain",
            output_image=pathlib.Path(__file__).parent / "assets" / "generated" / "terrain" / "atlas.png",
            output_mapping=pathlib.Path(__file__).parent / "assets" / "generated" / "terrain" / "mapping.json",
            icon_size=(512, 512),
            max_icons=128,
            atlas_columns=16,
        )
        terrain_atlas.run()

        Cache.set_icon_atlas(icon_generator)
        Cache.set_terrain_atlas(terrain_atlas)

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
    app = SCIV(debug=True)

    try:
        app.run()
    except (SystemExit, AssertionError):
        print("Goodbye :-)")
