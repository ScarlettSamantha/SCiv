from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from direct.showbase.Loader import Loader
from direct.showbase.MessengerGlobal import messenger
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from panda3d.core import PStatClient  # type: ignore

from gameplay.lose import LoseConditions
from gameplay.player import Player
from gameplay.tech import Tech
from gameplay.tile import Tile
from gameplay.unit import Unit
from managers.entity import EntityManager, EntityType
from managers.i18n import T_TranslationOrStr, Translation, t_
from managers.player import PlayerManager
from managers.world import World
from menus.kivy.elements.popup import ModalPopup as PopupOverride
from menus.screens.save_load import SaveLoadScreen
from mixins.singleton import Singleton
from system.entity import BaseEntity

if TYPE_CHECKING:
    from main import SCIV
    from managers.game import Game
    from menus.kivy.core import SCivGUI
    from menus.screens.game_ui import GameUIScreen


class ui(Singleton, DirectObject):
    current_menu = None

    def __init__(self, base: "SCIV"):
        from managers.game import Game

        self.menus = []
        self._base: "SCIV" = base
        self.current_menu = None
        self.game: Optional["Game"] = Game.get_singleton_instance()
        self.map: World = World.get_singleton_instance()

        self.current_tile: Optional[Tile] = None
        self.previous_tile: Optional[Tile] = None
        self.current_tiles: List[Tile] = []

        self.neighboring_tiles: List[Tile] = []
        self.previous_tiles: List[Tile] = []

        self.current_unit: Optional[Unit] = None
        self.previous_unit: Optional[Unit] = None

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

        self.highlighted_tiles: List[Tile] = []
        self.highlight_tile_radius: int = 2

    def __setup__(self, base: "SCIV", *args: Any, **kwargs: Any):
        super().__setup__(*args, **kwargs)
        self._base = base
        self.registered = False
        if not self.registered:
            self.register()
            self.registered = True

    def reset(self):
        self.current_tile = None
        self.previous_tile = None
        self.neighboring_tiles = []
        self.previous_tiles = []
        self.current_unit = None
        self.previous_unit = None
        self.game_menu_state = None
        self.showing_colors = False
        self.show_resources_in_radius = False
        self.show_colors_in_radius = False
        self.debug_show = {"actions": False, "stats": False, "debug": False}
        self.popups = {}
        self.previous_screen_name = ""
        self.showing_escape = False

        self.game_gui.reset()  # type: ignore # We reset the game gui so we can start fresh

    def reset_game_ui(self):
        self.get_screen("game_ui").reset()  # type: ignore
        MessengerGlobal.messenger.send("ui.update.ui.refresh_top_bar")

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
        self.game_gui.run()  # type: ignore

    def register(self) -> bool:
        self.accept("ui.update.user.tile_clicked", self.select_tile)
        self.accept("ui.update.user.tile_hover", self.on_tile_hover)
        self.accept("ui.update.user.tile_unhover", self.on_tile_unhover)

        self.accept("ui.update.ui.debug_ui_toggle", self.debug_ui_change)
        self.accept("ui.update.ui.show_save", self.on_show_save)
        self.accept("ui.update.ui.show_load", self.on_show_load)
        self.accept("ui.update.ui.hide_save", self.on_hide_save)
        self.accept("ui.update.ui.hide_load", self.on_hide_load)
        self.accept("ui.update.ui.show_game_ui", self.on_show_game_ui)
        self.accept("ui.request.save_game", self.on_request_save_game)
        self.accept("ui.request_main_menu", self.on_request_main_menu)
        self.accept("ui.request.reroll", self.on_reroll)
        self.accept("ui.request.open.popup", self.show_draggable_popup)

        self.accept("game.state.true_game_start", self.post_game_start)
        self.accept("game.turn.end_process", self.on_turn_change)

        self.accept("game.gameplay.research.player_starts_research", self.on_start_research_session)
        self.accept("game.gameplay.research.player_cancels_research", self.on_cancels_research_session)

        self.accept("system.main.ready", self.on_main_ready)
        self.accept("system.game.player_game_over", self.on_game_over_player)
        self.accept("system.game.opponent_game_over", self.on_game_over_opponent)

        self.accept("escape", self.on_escape_press)
        self.accept("p", self.activate_pstat)
        self.accept("l", self.deactivate_pstat)
        self.accept("z", self.calculate_icons_for_tiles)
        self.accept("space", self.on_space_press)
        return True

    def get_main_game_ui(self) -> "Screen | GameUIScreen":
        return self.get_screen("game_ui")

    def insert_refresh_frame(self):
        self._base.task_mgr.step()  # type: ignore

    def on_tile_hover(self, tile_coords: str) -> None: ...

    def on_tile_unhover(self, tile_coords: List[str]) -> None: ...

    def on_space_press(self):
        MessengerGlobal.messenger.send("game.requests.end_turn")

    def on_escape_press(self):
        if self.game is None:
            raise ValueError("Game not initialized")

    def on_game_over_player(self, player: Player, reason: LoseConditions):
        MessengerGlobal.messenger.send(
            "ui.request.open.popup",
            [
                "game_over_popup",
                t_(f"ui.dialogs.lose.player.conditions.{reason.value}.title"),
                t_(f"ui.dialogs.lose.player.conditions.{reason.value}.message"),
                True,
                self.on_lose_confirm_clicked,
            ],
        )

    def on_game_over_opponent(self, player: Player, reason: LoseConditions):
        MessengerGlobal.messenger.send(
            "ui.request.open.popup",
            [
                "game_over_popup",
                str(t_(f"ui.dialogs.lose.opponent.conditions.{reason.value}.title")).format(name=str(player.name)),
                str(t_(f"ui.dialogs.lose.opponent.conditions.{reason.value}.message")).format(name=str(player.name)),
            ],
        )

    def on_lose_confirm_clicked(self):
        MessengerGlobal.messenger.send("ui.update.ui.request_main_menu")
        MessengerGlobal.messenger.send("game.state.main_menu")

    def on_start_research_session(self, player: Player, tech: Tech):
        from menus.screens.game_ui import GameUIScreen

        if player != PlayerManager.session_player():
            return

        ui: GameUIScreen | Screen = self.get_main_game_ui()  # type: ignore

        if not isinstance(ui, GameUIScreen):
            raise ValueError("UI is not a GameUIScreen")

        ui.refresh_top_bar()

    def on_cancels_research_session(self, player: Player):
        if player != PlayerManager.session_player():
            return

        ui: GameUIScreen | Screen = self.get_main_game_ui()

        if not isinstance(ui, GameUIScreen):
            raise ValueError("UI is not a GameUIScreen")

        ui.refresh_top_bar()

    def on_unit_destroyed(self, unit: Unit):
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

    def on_request_main_menu(self):
        self.get_gui().load_main_menu()
        MessengerGlobal.messenger.send("game.state.main_menu")
        MessengerGlobal.messenger.send("ui.update.ui.hide_pause")

    def on_reroll(self):
        self.get_game().reroll()

    def on_request_save_game(self, save_name: str):
        self.get_game().save(save_name)

    def on_show_game_ui(self):
        self.get_gui().load_game_ui()

    def on_main_ready(self):
        self.get_gui().set_screen("main_menu")

    def on_show_save(self):
        self.previous_screen_name = self.get_gui().get_screen_manager().current  # type: ignore
        self.set_screen("save_load_screen")
        screen: SaveLoadScreen = self.get_gui().get_screen_manager().get_screen("save_load_screen")  # type: ignore
        screen.show_save_menu()  # type: ignore

    def on_show_load(self):
        self.previous_screen_name = self.get_gui().get_screen_manager().current  # type: ignore
        self.set_screen("save_load_screen")
        self.get_gui().get_screen_manager().get_screen("save_load_screen").show_load_menu()  # type: ignore

    def on_hide_save(self, go_back_to_previous: bool = True):
        if self.previous_screen_name is None or self.previous_screen_name == "":
            self.previous_screen_name = "game_ui"

        self.get_gui().get_screen_manager().current = self.previous_screen_name

    def on_hide_load(self, go_back_to_previous: bool = True):
        if self.previous_screen_name is None or self.previous_screen_name == "":
            self.previous_screen_name = "game_ui"

        self.get_gui().get_screen_manager().current = self.previous_screen_name

    def highlight_tiles(self, tiles: List[Tile], color: Optional[Tuple[float, float, float, float]] = None):
        for tile in tiles:
            tile.calculate()

    def show_draggable_popup(
        self,
        id: str,
        title: T_TranslationOrStr,
        message: T_TranslationOrStr,
        confirm: bool = False,
        on_confirm: Optional[Callable[[], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
    ):
        if isinstance(title, Translation):
            title = str(title)
        if isinstance(message, Translation):
            message = str(message)

        if confirm:
            popup = PopupOverride(
                title=title,
                message=message,
                on_confirm=on_confirm,  # type: ignore
                cancel_callback=on_cancel,
                width=400,
                height=200,  # type: ignore
            )
            self.popups[id] = popup
            popup.open()  # type: ignore
        else:
            popup = PopupOverride(title=title, message=message, width=400, height=200)
            self.popups[id] = popup
            popup.open()  # type: ignore

    def close_popup(self, id: str):
        if id in self.popups:
            self.popups[id].dismiss()  # type: ignore

    def post_game_start(self):
        screen: "GameUIScreen" = self.get_gui().get_screen("game_ui")
        screen.player = PlayerManager.session_player()
        screen.build_screen()  # type: ignore

    def activate_pstat(self):
        PStatClient.connect("127.0.0.1", 5185)  # type: ignore

    def deactivate_pstat(self):
        PStatClient.disconnect()  # type: ignore

    def calculate_icons_for_tiles(self):
        for _, tile in self.map.map.items():
            tile.tile_yield.calculate()

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

    def get_game_ui(self):
        # If we don't have an active Game, create one
        if self.game is None:
            messenger.send("system.game.start")
        else:
            # If we do, we're just resuming it
            messenger.send("system.game.resume")

    def set_screen(self, screen_name: str):
        self.get_gui().get_screen_manager().current = screen_name

    def get_screen(self, screen_name: str) -> Screen:
        return self.get_gui().get_screen_manager().get_screen(screen_name)  # type: ignore

    def get_escape_menu(self):
        if self.showing_escape:
            self.set_screen("game_ui")
            self.get_screen("save_load_screen").hide_load_menu()  # type: ignore
            self.get_screen("save_load_screen").hide_save_menu()  # type: ignore
            self.showing_escape = False
            self.get_game().unpause()
            return

        self.showing_escape = True
        self.set_screen("pause_menu")
        self.get_game().pause()

    def clear_selected_unit(self):
        if self.current_unit is None:
            return

        self.current_unit = None
        self.previous_unit = None

    def clear_selection(self):
        self.current_tiles = []
        self.previous_tiles = []

        self.current_unit = None
        self.previous_unit = None

    def clear_previous_selected_tiles(self):
        # Restore colors of previously selected tile and neighbors
        tiles = self.previous_tiles
        if self.previous_tile is not None:
            tiles.append(self.previous_tile)

        if len(tiles) == 0:
            return

    def select_tile(self, tile_coords: str):
        x, y = tile_coords.split("_")[-2:]
        tile = self.map.grid.get((int(x), int(y)))

        if tile is None:
            messenger.send("ui.update.user.tile_not_found", [tile_coords])
            return

        if self.previous_tile is not None:
            self.previous_tile.deselect()

        tile.select()

        if tile.is_city() and tile.city is not None and tile.city.player is not None:
            if PlayerManager.is_session_player(tile.city.player):
                messenger.send("ui.update.user.city_clicked", [tile.city])
            else:
                messenger.send("ui.update.user.enemy_city_clicked", [tile.city])

        self.previous_tile = self.current_tile
        self.current_tile = tile

    def select_unit(self, unit: List[str] | Unit):
        if isinstance(unit, list):
            result = self.get_entities().get(EntityType.UNIT, unit[0])
            if result is None:
                return
            object: BaseEntity | Unit = result
        else:
            object: BaseEntity | Unit = unit

        if self.current_tile is not None:
            self.previous_tile = self.current_tile
            self.current_tile = None

        if self.current_unit is not None:
            self.previous_unit = self.current_unit

        if isinstance(object, Unit):
            if object.model is not None:
                self.current_unit = object

    def trigger_render_analyze(self):
        self._base.render.analyze()  # type: ignore
