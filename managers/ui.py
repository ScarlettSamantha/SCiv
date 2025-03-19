from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from direct.showbase.Loader import Loader
from direct.showbase.MessengerGlobal import messenger
from kivy.uix.popup import Popup
from panda3d.core import PStatClient

from gameplay.tiles.base_tile import BaseTile
from gameplay.units.unit_base import UnitBaseClass
from helpers.colors import Colors
from managers.action import ActionManager
from managers.entity import EntityManager, EntityType
from managers.i18n import T_TranslationOrStr, Translation
from managers.player import PlayerManager
from managers.world import World
from menus.kivy.elements.popup import ModalPopup as PopupOverride
from menus.screens.game_ui import GameUIScreen
from mixins.singleton import Singleton
from system.entity import BaseEntity

if TYPE_CHECKING:
    from main import SCIV
    from managers.game import Game
    from menus.kivy.core import SCivGUI


class ui(Singleton, DirectObject):
    current_menu = None

    def __init__(self, base: "SCIV"):
        from managers.game import Game

        self.menus = []
        self._base: "SCIV" = base
        self.current_menu = None
        self.game: Optional["Game"] = Game.get_instance()
        self.map: World = World.get_instance()

        self.current_tile: Optional[BaseTile] = None
        self.previous_tile: Optional[BaseTile] = None

        self.neighboring_tiles: List[BaseTile] = []
        self.previous_tiles: List[BaseTile] = []

        self.current_unit: Optional[UnitBaseClass] = None
        self.previous_unit: Optional[UnitBaseClass] = None

        self.game_menu_state: Optional[Game] = None
        self.registered = False if not self.registered else self.register

        self.game_gui: Optional[SCivGUI] = None

        self.showing_colors = False
        self.loader: Loader = Loader(self._base)

        self.show_resources_in_radius: bool = False
        self.show_colors_in_radius: bool = False

        self.debug_show: Dict[str, bool] = {"actions": False, "stats": False, "debug": False}

        self.popups: Dict[str, Popup] = {}
        self.previous_screen_name: Optional[str] = ""
        self.showing_escape: bool = False

    def __setup__(self, base, *args, **kwargs):
        super().__setup__(*args, **kwargs)
        self._base = base
        self.registered = False
        if not self.registered:
            self.register()
            self.registered = True

    def get_gui(self) -> "SCivGUI":
        if self.game_gui is None:
            raise ValueError("GUI not initialized")
        return self.game_gui

    def get_entities(self) -> EntityManager:
        if self.game is None:
            raise AssertionError("Game not initialized")

        return self.game.entities

    def get_game(self) -> "Game":
        if self.game is None:
            raise ValueError("Game not initialized")
        return self.game

    def kivy_setup(self):
        from menus.kivy.core import SCivGUI

        self.game_gui = SCivGUI(self._base)
        self.game_gui.run()

    def register(self) -> bool:
        self.accept("ui.update.user.tile_clicked", self.select_tile)
        self.accept("ui.update.ui.debug_ui_toggle", self.debug_ui_change)
        self.accept("ui.update.ui.resource_ui_change", self.on_resource_ui_change_request)
        self.accept("ui.update.ui.lense_change", self.on_lense_change)
        self.accept("ui.update.ui.show_save", self.on_show_save)
        self.accept("ui.update.ui.show_load", self.on_show_load)
        self.accept("ui.update.ui.hide_save", self.on_hide_save)
        self.accept("ui.update.ui.hide_load", self.on_hide_load)
        self.accept("unit.action.move.visiting_tile", self.leave_trail)

        self.accept("ui.request.open.popup", self.show_draggable_popup)

        self.accept("escape", self.get_escape_menu)

        self.accept("f7", self.trigger_render_analyze)
        self.accept("p", self.activate_pstat)
        self.accept("l", self.deactivate_pstat)
        self.accept("n", self.show_colors_for_resources)
        self.accept("m", self.show_colors_for_water)
        self.accept("b", self.show_colors_for_units)

        self.accept("z", self.calculate_icons_for_tiles)
        self.accept("x", self.toggle_big_tile_icons)
        self.accept("c", self.toggle_little_tile_icons)
        self.accept("game.state.true_game_start", self.post_game_start)
        self.accept("game.turn.end_process", self.on_turn_change)
        self.accept("system.main.ready", self.on_main_ready)
        return True

    def get_main_game_ui(self) -> GameUIScreen:
        return self.get_gui().get_screen_manager().get_screen("game_ui")

    def on_unit_destroyed(self, unit: UnitBaseClass):
        messenger.send("ui.update.ui.unit_unselected", [unit])
        if unit == self.current_unit:
            self.current_unit = None
        if unit == self.previous_unit:
            self.previous_unit = None

    def on_turn_change(self, turn: int):
        MessengerGlobal.messenger.send("ui.update.ui.refresh_top_bar")
        MessengerGlobal.messenger.send("ui.update.ui.refresh_city_ui")
        MessengerGlobal.messenger.send("ui.update.ui.refresh_player_turn_control", [turn])
        return True

    def on_main_ready(self):
        self.get_gui().set_screen("main_menu")

    def on_show_save(self):
        self.set_screen("save_load_screen")
        self.get_gui().get_screen_manager().get_screen("save_load_screen").show_save_menu()

    def on_show_load(self):
        self.set_screen("save_load_screen")
        self.get_gui().get_screen_manager().get_screen("save_load_screen").show_load_menu()

    def on_hide_save(self, go_back_to_previous: bool = True):
        self.get_gui().get_screen_manager().get_screen("save_load_screen").hide_save_menu()
        self.get_gui().get_screen_manager().current = "game_ui"

    def on_hide_load(self, go_back_to_previous: bool = True):
        self.get_gui().get_screen_manager().get_screen("save_load_screen").hide_load_menu()
        self.get_gui().get_screen_manager().current = "game_ui" if go_back_to_previous else "main_menu"

    def show_draggable_popup(
        self,
        id: str,
        title: T_TranslationOrStr,
        message: T_TranslationOrStr,
        confirm: bool = False,
        on_confirm: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
    ):
        if isinstance(title, Translation):
            title = str(title)
        if isinstance(message, Translation):
            message = str(message)

        if confirm:
            popup = PopupOverride(
                title=title, message=message, on_confirm=on_confirm, cancel_callback=on_cancel, width=400, height=200
            )
            self.popups[id] = popup
            popup.open()
        else:
            popup = PopupOverride(title=title, message=message, width=400, height=200)
            self.popups[id] = popup
            popup.open()

    def close_popup(self, id: str):
        if id in self.popups:
            self.popups[id].dismiss()

    def post_game_start(self):
        self.calculate_icons_for_tiles(small=False, large=True)
        self.get_gui().set_screen("game_ui")

    def activate_pstat(self):
        PStatClient.connect("127.0.0.1", 5185)

    def deactivate_pstat(self):
        PStatClient.disconnect()

    def calculate_icons_for_tiles(self, small: bool = True, large: bool = True):
        for _, tile in self.map.map.items():
            tile.tile_yield.calculate()
            self.toggle_tile_icons(tile, small=small, large=large)

    def on_resource_ui_change_request(self, value: Enum):
        from menus.kivy.parts.debug_actions import MapActionsValues

        self.show_resources_in_radius = False
        small, big = False, False

        if MapActionsValues.BIG_ICONS == value:
            big = True
        elif MapActionsValues.SMALL_ICONS == value:
            small = True
        elif MapActionsValues.SMALL_BIG_ICONS == value:
            small, big = True, True
        elif MapActionsValues.ALL_IN_RADIUS == value:
            self.show_resources_in_radius = True  # We hide the rest of the icons

        self.calculate_icons_for_tiles(small=small, large=big)

    def debug_ui_change(self, value: Enum):
        from menus.kivy.parts.debug_actions import DebugUIOptionsValues

        actions, stats, debug = False, False, False

        if DebugUIOptionsValues.ALL_DEBUG_UI == value:
            actions, stats, debug = True, True, True
        elif DebugUIOptionsValues.NONE == value:
            ...  # Do nothing as we are already set to False
        elif DebugUIOptionsValues.DEBUG == value:
            debug = True
        elif DebugUIOptionsValues.STATS == value:
            stats = True
        elif DebugUIOptionsValues.ACTIONS == value:
            actions = True
        elif DebugUIOptionsValues.DEBUG_AND_STATS == value:
            debug, stats = True, True
        elif DebugUIOptionsValues.DEBUG_AND_ACTIONS == value:
            debug, actions = True, True
        else:
            raise ValueError("Invalid value for debug ui change")

        self.draw_debug_ui(debug, stats, actions)

    def draw_debug_ui(self, debug: bool, stats: bool, actions: bool):
        if self.game_gui is None:
            raise AssertionError("GUI not initialized")

        self.debug_show = {"actions": actions, "stats": stats, "debug": debug}
        self.game_gui.debug_ui_state(stats, actions, debug)

    def on_lense_change(self, value: Enum):
        from menus.kivy.parts.debug_actions import LenseOptionsValues

        self.restore_all_tiles_colors()

        if LenseOptionsValues.RESOURCES == value:
            self.show_colors_for_resources()
        elif LenseOptionsValues.WATER == value:
            self.show_colors_for_water()
        elif LenseOptionsValues.UNITS == value:
            self.show_colors_for_units()
        elif LenseOptionsValues.EMPIRES == value:
            self.show_empire_colors()
        elif LenseOptionsValues.NONE == value:
            return
        else:
            raise ValueError("Invalid value for lense change")

    def toggle_tile_icons(self, tile: BaseTile, small: bool = False, large: bool = False):
        tile.clear_all_icons()
        if small:
            tile.add_small_icons()
        if large:
            tile.add_icon_to_tile()

    def toggle_big_tile_icons(self):
        for _, tile in self.map.map.items():
            if tile._showing_large_icons is False:
                tile.add_icon_to_tile()
            else:
                tile.clear_large_icons()

    def toggle_little_tile_icons(self):
        for _, tile in self.map.map.items():
            if tile._showing_small_icons is False:
                tile.add_small_icons()
            else:
                tile.clear_small_icons()

    def get_game_ui(self):
        # If we don't have an active Game, create one
        if self.game is None:
            messenger.send("system.game.start")
        else:
            # If we do, we're just resuming it
            messenger.send("system.game.resume")

    def set_screen(self, screen_name: str):
        self.get_gui().get_screen_manager().current = screen_name

    def get_escape_menu(self):
        if self.showing_escape:
            self.set_screen("game_ui")
            self.showing_escape = False
            self.get_game().unpause()
            return

        self.showing_escape = True
        self.set_screen("pause_menu")
        self.get_game().pause()

    def clear_selected_unit(self):
        if self.current_unit is None:
            return

        self.current_unit.set_color(Colors.RESTORE)
        self.current_unit = None
        self.previous_unit = None

    def clear_selection(self):
        self.current_tiles[0].set_color(Colors.RESTORE)
        self.current_tiles = []
        self.previous_tiles = []

        if self.current_unit is not None:
            self.current_unit.set_color(Colors.RESTORE)
        self.current_unit = None
        self.previous_unit = None

    def clear_previous_selected_tiles(self):
        # Restore colors of previously selected tile and neighbors
        tiles = self.previous_tiles
        if self.previous_tile is not None:
            tiles.append(self.previous_tile)

        if len(tiles) == 0 or tiles is None:
            return

        for tile in tiles:
            if self.show_resources_in_radius:
                tile.clear_all_icons()
            tile.set_color(Colors.RESTORE)

    def select_tile(self, tile_coords: List[str]):
        from gameplay.repositories.tile import TileRepository

        tile = self.map.map.get(tile_coords[0])
        if tile is None:
            return

        tile.calculate()

        if tile.city is not None and tile.city.player is not None:
            if PlayerManager.is_session_player(tile.city.player):
                messenger.send("ui.update.user.city_clicked", [tile.city])
            else:
                messenger.send("ui.update.user.enemy_city_clicked", [tile.city])

        self.previous_tile = self.current_tile
        self.current_tile = tile

        self.previous_tiles = self.neighboring_tiles
        self.neighboring_tiles = []
        self.neighboring_tiles = TileRepository.get_neighbors(tile, check_passable=False)

        if self.show_resources_in_radius:
            self.toggle_tile_icons(tile, small=True, large=True)

        for neighbor in self.neighboring_tiles:
            if self.show_resources_in_radius:
                self.toggle_tile_icons(neighbor, small=True, large=True)
            if self.show_resources_in_radius:
                neighbor_tile_colors: List[Tuple[float, float, float, float]] = [Colors.PURPLE] * 3
                self.color_tile(neighbor, neighbor_tile_colors)

    def color_tile(
        self,
        tile: BaseTile,
        color: Optional[Tuple[float, float, float, float] | List[Tuple[float, float, float, float]]] = None,
    ):
        if color is None:
            color = Colors.RESTORE

        if tile.owner == PlayerManager.session_player():
            tile.set_color(color if isinstance(color, tuple) else color[0])
        elif tile.owner is PlayerManager.get_nature():
            tile.set_color(color if isinstance(color, tuple) else color[1])
        else:
            tile.set_color(color if isinstance(color, tuple) else color[2])

    def leave_trail(
        self,
        unit: Any,
        tile: BaseTile,
    ):
        from gameplay.actions.timed.trail import Trial

        ActionManager.add_timed_action(Trial(tile=tile))

    def color_neighbors(
        self,
        tile: BaseTile,
        color: Optional[Tuple[float, float, float, float] | List[Tuple[float, float, float, float]]] = None,
    ):
        from gameplay.repositories.tile import TileRepository

        if color is None:
            color = Colors.RESTORE

        neighbors = TileRepository.get_neighbors(tile, check_passable=False)
        for i, _tile in enumerate(neighbors):
            _tile.set_color(color if isinstance(color, tuple) else color[i % len(color)])

        return neighbors

    def restore_tile_colors(self, tile: BaseTile):
        tile.set_color(Colors.RESTORE)

    def restore_all_tiles_colors(self):
        self.showing_color = False
        for _, tile in self.map.map.items():
            tile.set_color(Colors.RESTORE)

    def select_unit(self, unit: List[str] | UnitBaseClass):
        if isinstance(unit, list):
            result = self.get_entities().get(EntityType.UNIT, unit[0])
            if result is None:
                return
            object: BaseEntity | UnitBaseClass = result
        else:
            object: BaseEntity | UnitBaseClass = unit

        if self.current_tile is not None:
            self.current_tile.set_color(Colors.RESTORE)
            self.previous_tile = self.current_tile
            self.current_tile = None

        if self.current_unit is not None:
            self.previous_unit = self.current_unit
            if self.previous_unit.model is not None:
                self.previous_unit.set_color(Colors.RESTORE)

        if object is not None and isinstance(object, UnitBaseClass):
            if object.owner == PlayerManager.session_player():
                # Green for player units
                object.set_color(Colors.GREEN)
            else:
                # Red for enemy units
                object.set_color(Colors.RED)
            self.current_unit = object

    def trigger_render_analyze(self):
        self._base.render.analyze()  # type: ignore

    def show_colors_for_water(self):
        for _, hex in self.map.map.items():
            if self.showing_colors:
                hex.set_color(Colors.RESTORE)
                continue

            if hex.is_coast and hex.is_water:
                hex.set_color(Colors.TIEL)
            elif hex.is_water:
                hex.set_color(Colors.BLUE)
            elif not hex.is_water:
                hex.set_color(Colors.RED)
            else:
                hex.set_color(Colors.RESTORE)

    def show_colors_for_resources(self):
        from gameplay.resource import ResourceTypeBonus, ResourceTypeStrategic

        for _, hex in self.map.map.items():
            if len(hex.resources) > 0:
                is_strategic: bool = len(hex.resources.resources[ResourceTypeStrategic]) > 0
                is_bonus: bool = len(hex.resources.resources[ResourceTypeBonus]) > 0
                if is_strategic:
                    hex.set_color(Colors.YELLOW)
                elif is_bonus:
                    hex.set_color(Colors.BLUE)
                else:
                    hex.set_color(Colors.GREEN)
            else:
                hex.set_color(Colors.RED)

    def show_colors_for_units(self):
        for _, hex in self.map.map.items():
            if len(hex.units) > 0:
                hex.set_color(Colors.BLUE)
            else:
                hex.set_color(Colors.RED)

    def show_empire_colors(self):
        for _, hex in self.map.map.items():
            if hex.owner is not None:
                hex.set_color(hex.owner.color)
            else:
                hex.set_color(Colors.RESTORE)
