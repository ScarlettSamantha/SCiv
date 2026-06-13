#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from typing import TYPE_CHECKING, Tuple, cast

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
os.chdir(SCRIPT_DIR)

import pathlib
from logging import Logger

import simplepbr
from direct.showbase.Messenger import Messenger
from direct.showbase.ShowBase import ShowBase
from direct.task.Task import Task
from helpers.direct_loading_screen import LoadingScreen
from helpers.os import WindowsHelper
from helpers.paths import PathsHelper
from kivy.config import Config
from managers.i18n import I18nManager, set_i18n
from managers.unit import UnitManager
from panda3d.core import loadPrcFile
from panda3d_kivy import monkey  # type: ignore

Config.set("modules", "inspector", "")  # type: ignore
Config.set("graphics", "gl_backend", "angle_sdl2")  # type: ignore
Config.set("kivy", "kivy_clock", "free_all")  # type: ignore
Config.set("kivy", "exit_on_escape", "0")  # type: ignore
Config.set("kivy", "desktop", "1")  # type: ignore
Config.set("graphics", "maxfps", 160)  # type: ignore
Config.set("graphics", "verify_gl_main_thread", "false")  # type: ignore
monkey.patch_kivy()  # type: ignore

loadPrcFile("config.prc")

if TYPE_CHECKING:
    from panda3d.core import GraphicsWindow
    from system.camera import Camera


class OpenCiv(ShowBase):
    def __init__(self) -> None:
        from helpers.cache import Cache
        from managers.config import ConfigManager

        ConfigManager.set_singleton_instance(ConfigManager())

        from helpers.debug import Debug
        from managers.assets import AssetManager
        from managers.input import Input
        from managers.log import LogManager

        self.logger = LogManager.set_instance(LogManager())
        assert self.logger is not None
        self.logger.setup_loggers()

        from managers.entity import EntityManager
        from managers.ui import ui
        from system.camera import Camera
        from system.lights import setup_lights
        from system.vars import DEBUG, __version__, get_git_commit

        self.generate_os_integrations()
        self.debug: bool = DEBUG
        Debug.debug = self.debug

        from managers.debug import DebugManager

        self.debug_manager = DebugManager()
        DebugManager.set_singleton_instance(self.debug_manager)

        self.version: str = __version__
        self.commit: str = get_git_commit()

        config_mgr = ConfigManager()
        ConfigManager.set_singleton_instance(config_mgr)

        if (
            self.debug
            and (enabled := config_mgr.get_by_key(("debug", "sentry", "enable"), None)) is not None
            and enabled is True
            and (sentry_dsn := config_mgr.get_by_key(("debug", "sentry", "dsn"), None)) is not None
            and sentry_dsn.strip() != "" # type: ignore
        ):
            from helpers.debug import Debug

            # self.sentry = Debug.init_sentry(sentry_dsn)

        base_file_path: pathlib.Path = pathlib.Path(__file__).parent.absolute()
        PathsHelper.base_path = str(base_file_path)
        ShowBase.__init__(self)

        Cache.set_showbase_instance(self)
        config_mgr.set_screen_mode(config_mgr.get_screen_mode(), auto_save=False)

        self.config_manager: ConfigManager = config_mgr
        origin = self.config_manager.get_window_origin()
        size = self.config_manager.get_resolution()
        self._pending_window_state: Tuple[int, int, int, int] | None = None
        self._last_configured_window_state: Tuple[int, int, int, int] = (origin[0], origin[1], size[0], size[1])
        self.accept("window-event", self._on_window_event)

        self.base_path: pathlib.Path = pathlib.Path.cwd().absolute()

        if WindowsHelper.is_windows():
            WindowsHelper.load_dll(str(self.base_path / "libs/win-amd64/glew32.dll"))

        self.i18n = I18nManager(str(base_file_path / "i18n"), self.config_manager.get_language(), True)
        Cache.set_i18n_instance(self.i18n)
        set_i18n(self.i18n)

        loading_screen = LoadingScreen(
            self, [str(self.base_path / "logo.png")], 14, on_continue=self.on_loading_screen_continue
        )
        loading_screen.next_stage("Loading OpenCiv")
        simplepbr.init()
        loading_screen.next_stage("Loading Panda3D")
        self.disableMouse()

        loading_screen.next_stage("Setting up logging")

        self.engine_logger: Logger = self.logger.engine.getChild("Main")
        self.engine_logger.info("Starting OpenCiv")

        loading_screen.next_stage("Loading Messenger")
        self.messenger: Messenger = Messenger()

        from managers.game import Game
        from managers.world import World

        self.world = World(self)
        World.set_instance(self.world)
        self.world.__setup__(self)

        loading_screen.next_stage("Setting up input manager")
        self.engine_logger.info("Setting up input manager")
        self.input_manager = Input(self)
        Input.set_singleton_instance(self.input_manager)
        self.input_manager.register_menu_input()
        self.input_manager.inject_into_camera()

        loading_screen.next_stage("Setting up camera")
        self.engine_logger.info("Setting up camera")
        self.game_camera = Camera(self)
        Camera.set_singleton_instance(instance=self.game_camera)
        self.game_camera.register()

        self.ui_manager = ui(self)
        ui.set_singleton_instance(self.ui_manager)

        self.entity_manager = EntityManager(base=self)
        EntityManager.set_singleton_instance(self.entity_manager)

        self.engine_logger.info("Setting up game manager")
        loading_screen.next_stage("Setting up game manager")
        self.game_manager_instance = Game(self, self.game_camera)
        Game.set_singleton_instance(self.game_manager_instance)
        self.input_manager.game = self.game_manager_instance

        self.entity_manager.__setup__(self)

        self.engine_logger.info("Setting up asset manager")
        loading_screen.next_stage("Setting up asset manager")

        self.asset_manager: AssetManager = AssetManager()
        AssetManager.set_singleton_instance(self.asset_manager)
        self.asset_manager.set_base(self)

        loading_screen.next_stage("Generating assets")
        self.engine_logger.info("Generating non-static assets")
        self.generate_non_static_assets()

        loading_screen.next_stage("Setting up lights")
        self.engine_logger.info("Setting up lights")
        setup_lights(self)

        self.engine_logger.info("Setting up world")
        loading_screen.next_stage("Setting up world")

        loading_screen.next_stage("Setting up unit manager")
        self.engine_logger.info("Setting up unit manager")
        self.unit_manager = UnitManager(self)
        UnitManager.set_singleton_instance(self.unit_manager)
        self.input_manager.unit_manager = self.unit_manager
        self.input_manager.setup(self)

        self.engine_logger.info("Setting up UI manager")
        loading_screen.next_stage("Setting up kivy")

        self.ui_manager.map = self.world

        if config_mgr.get_by_key(("qol", "intro_skip")):
            self.on_loading_screen_continue()
            loading_screen.destroy()
        else:
            loading_screen.next_stage("Ready")

    def _on_window_event(self, window: "GraphicsWindow") -> None:
        from managers.config import WINDOW_MODE_WINDOW

        if window is not self.win:
            return

        if self.config_manager.get_screen_mode() != WINDOW_MODE_WINDOW:
            return

        state = self._read_window_state(window)
        if state is None or state == self._last_configured_window_state:
            return

        self._pending_window_state = state
        self.taskMgr.remove("sync-window-state-to-config")
        self.taskMgr.doMethodLater(0.35, self._sync_window_state_to_config, "sync-window-state-to-config")

    def _read_window_state(self, window: "GraphicsWindow") -> Tuple[int, int, int, int] | None:
        width = int(window.getXSize())
        height = int(window.getYSize())

        if width <= 0 or height <= 0:
            return None

        origin_x, origin_y = self.config_manager.get_window_origin()

        try:
            properties = window.getProperties()
            origin_x = int(properties.getXOrigin())
            origin_y = int(properties.getYOrigin())
        except Exception:
            pass

        return origin_x, origin_y, width, height

    def _sync_window_state_to_config(self, task: Task) -> int:
        if self._pending_window_state is None:
            return 1

        origin_x, origin_y, width, height = self._pending_window_state
        self._pending_window_state = None

        if (origin_x, origin_y, width, height) == self._last_configured_window_state:
            return 1

        self.config_manager.update_window_position_size(origin_x, origin_y, width, height, auto_save=True)
        self._last_configured_window_state = (origin_x, origin_y, width, height)

        return 1

    def window(self) -> "GraphicsWindow":
        from panda3d.core import GraphicsWindow  # type: ignore

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

    def generate_os_integrations(self) -> None:
        from helpers.os import LinuxHelper

        if LinuxHelper.is_linux():
            LinuxHelper.generate_application_registration()

    def generate_non_static_assets(self, force: bool = False) -> None:
        from helpers.cache import Cache
        from helpers.debug import Debug
        from helpers.paths import PathsHelper
        from system.atlas import AtlasGenerator

        base_path = pathlib.Path(PathsHelper.get_data_dir()) / "assets" / "generated"

        icon_generator = AtlasGenerator(
            input=[
                pathlib.Path(__file__).parent / "assets.mf",
            ],
            output_image=base_path / "generated" / "icons" / "atlas.png",
            output_mapping=base_path / "generated" / "icons" / "mapping.json",
            icon_size=(
                cast(int, self.config_manager.get_by_key(("assets", "icon_resolution_x"))),
                cast(int, self.config_manager.get_by_key(("assets", "icon_resolution_y"))),
            ),
            max_icons=1024,
            atlas_columns=16,
        )

        if force or Debug.system_asset_generation():
            self.engine_logger.info("Forcing asset generation")
            icon_generator.run(force=force)
        else:
            if not icon_generator.exists():
                self.engine_logger.info("Icon atlas does not exist, generating assets")
                icon_generator.run(force=force)
            else:
                self.engine_logger.info("Icon atlas exists, skipping generation loading cache")
                icon_generator.load_caches()

        Cache.set_icon_atlas(icon_generator)

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
