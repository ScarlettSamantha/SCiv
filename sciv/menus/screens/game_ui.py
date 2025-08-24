from logging import Logger
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type, Union

from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from direct.showbase.MessengerGlobal import messenger
from gameplay.city import City
from gameplay.civic import CivicTree
from gameplay.improvement import Improvement
from gameplay.player import Player
from gameplay.repositories.tile import TileRepository
from gameplay.tile import Tile
from gameplay.unit import Unit
from gameplay.unit_path import MovementPathBlocksRenderer
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from managers.combat import T_TARGET
from managers.combat_log import CombatLog, CombatLogEntry
from managers.entity import EntityManager, EntityType
from managers.log import LogManager
from managers.player import PlayerManager
from managers.unit import UnitManager
from managers.world import World
from menus.kivy.elements.log_popup import LogPopup
from menus.kivy.elements.message import MessageRenderer
from menus.kivy.mixins.collidable import CollisionPreventionMixin
from menus.kivy.parts.action_bar import ActionBar
from menus.kivy.parts.city import CityUI
from menus.kivy.parts.civics import Civics
from menus.kivy.parts.debug import DebugPanel
from menus.kivy.parts.debug_actions import DebugActions
from menus.kivy.parts.debug_map_stats import DebugMapStats
from menus.kivy.parts.inspect_entity import InspectEntity
from menus.kivy.parts.player_attack import TargetingDuelPanel
from menus.kivy.parts.player_combat_log import PlayerCombatLog
from menus.kivy.parts.player_info import PlayerInfo
from menus.kivy.parts.player_list import PlayerList
from menus.kivy.parts.player_select import UnitSummaryPanel
from menus.kivy.parts.player_turn_control import PlayerTurnControl
from menus.kivy.parts.research import Research
from menus.kivy.parts.stats import StatsPanel
from menus.kivy.parts.top_bar import TopBar
from menus.screens.pause_menu import PauseMenu
from mixins.inspectable import Inspectable
from panda3d.core import Vec3
from system.actions import Action
from system.camera import Camera
from system.entity import BaseEntity
from system.messenger import Messenger

if TYPE_CHECKING:
    from game import OpenCiv


class GameUIScreen(Screen, CollisionPreventionMixin, DirectObject):
    debug_data: Dict[str, str] = {
        "state": "Playing",
    }

    def __init__(self, *args: Any, **kwargs: Any):
        if "base" not in kwargs:
            raise ValueError("GameUIScreen requires a 'base' keyword argument.")
        self._base: "OpenCiv" = kwargs.pop("base", None)

        from managers.ui import ui

        super().__init__(base=self._base, *args, **kwargs)  # type: ignore

        self.world_manager = World.get_singleton_instance()
        self.camera: Camera = Camera.get_singleton_instance()
        self.unit_manager: UnitManager = UnitManager.get_singleton_instance()
        self.ui_manager: ui = ui.get_singleton_instance()
        self.player: Optional[Player] = None

        self.waiting_for_world_input: bool = False

        self.wait_for_next_input_of_user: bool = False
        self.wait_for_action_of_user: Optional[Action] = None
        self.wait_for_action: Optional[Action] = None

        self.debug_panel: Optional[Label] = None
        self.camera_panel: Optional[Label] = None

        self.root_layout: Optional[FloatLayout] = None

        self.action_bar_frame: Optional[ActionBar] = None
        self.debug_frame: Optional[DebugPanel] = None
        self.stats_frame: Optional[StatsPanel] = None
        self.debug_actions: Optional[DebugActions] = None
        self.debug_map_stats: Optional[DebugMapStats] = None
        self.player_turn_control: Optional[PlayerTurnControl] = None
        self.city_ui: Optional[CityUI] = None
        self.top_bar: Optional[TopBar] = None
        self.research: Optional[Research] = None
        self.civics: Optional[Civics] = None
        self.player_list: Optional[PlayerList] = None
        self.player_info: Optional[PlayerInfo] = None
        self.player_combat_log: Optional[PlayerCombatLog] = None
        self.messenger: Optional[MessageRenderer] = None
        self.inspect: Optional[InspectEntity] = None
        self.player_attack_info: Optional[TargetingDuelPanel] = None
        self.unit_path_renderer: Optional[MovementPathBlocksRenderer] = None
        self.player_target_info: Optional[UnitSummaryPanel] = None
        self.logger: Logger = self._base.logger.graphics.getChild("ui.game_ui")
        self.log: LogPopup = LogPopup(handler=LogManager.get_singleton_instance().ui_handler)

        self.showing_city: Optional[City] = None

        self.debug_panels_showing_state: Dict[str, bool] = {
            "stats": False,
            "actions": False,
            "debug": False,
        }

        self.logger.info("Game UI Screen initialized.")
        self.register()
        self.logger.info("Game UI Screen built.")

    def refresh_messenger(self):
        if self.messenger is None:
            return
        self.messenger.refresh(0)

    def on_game_start(self, *args: Any):
        self.player = PlayerManager.session_player()
        self.build_player_list()
        self.build_combat_log()
        self.build_messenger()

        if self.debug_map_stats is not None:
            self.debug_map_stats.update()

        self.add_widget(self.build_debug_map_stats())  # type: ignore
        # self.add_widget(self.build_debug_frame())  # type: ignore
        self.add_widget(self.build_top_bar())  # type: ignore
        self.add_widget(self.build_stats_frame())  # type: ignore

        self.register_non_collidable(self.player_combat_log)  # type: ignore
        self.accept(
            "escape", self.on_escape
        )  # this is to prevent the pause menu from being opened before the game starts
        MessengerGlobal.messenger.send("ui.update.ui.hide_pause")

    def on_game_end(self, *args: Any):
        self.ignore("escape")
        self.manager.current = "main_menu"

    def reset(self):
        self.logger.info("Resetting game UI screen.")
        self.clear_action_bar()
        self.update_ui_geometry_cache()
        if self.top_bar is not None:
            self.top_bar.update()

    def register(self):
        self.logger.info("Registering event listeners.")

        self.accept("ui.request.action.stage", self.request_action_stage)

        self.accept("ui.update.user.city_clicked", self.process_city_click)
        self.accept("ui.update.user.enemy_city_clicked", self.process_enemy_city_click)

        self.accept("ui.update.ui.unit_unselected", self.clear_action_bar)

        self.accept("system.unit.destroyed", self.clear_action_bar)
        self.accept("game.gameplay.unit.destroyed", self.on_unit_destroyed)

        self.accept("game.state.true_game_start", self.on_game_start)
        self.accept("game.state.load_finished", self.on_game_start)
        self.accept("game.state.main_menu", self.on_game_end)

        self.accept("ui.update.ui.show_research_ui", self.open_research)
        self.accept("ui.update.ui.hide_research_ui", self.close_research)
        self.accept("ui.update.ui.show_civics_ui", self.open_civics)
        self.accept("ui.update.ui.hide_civics_ui", self.close_civics)
        self.accept("ui.update.ui.show_inspect_ui", self.open_inspect)
        self.accept("ui.update.ui.hide_inspect_ui", self.close_inspect)
        self.accept("ui.update.ui.toggle_log", self.toggle_log)
        self.accept("ui.update.ui.refresh_action_bar", self.refresh_action_bar)
        self.accept("ui.update.ui.refresh_basic_elements", self.update_ui_elements)
        self.accept("ui.update.ui.refresh_city_ui", self.refresh_city)
        self.accept("ui.update.ui.open_player_attack_info", self.open_player_attack_info)
        self.accept("ui.update.ui.close_player_attack_info", self.close_player_attack_info)

        self.accept("t", self.toggle_research)
        self.accept("c", self.toggle_civics)

    def request_action_stage(self, action: Action, executor: "Player | None" = None):
        self.logger.info(f"Requesting action stage for action: {action.name}")

        if self.wait_for_next_input_of_user or self.wait_for_action_of_user is not None:
            self.logger.info("Already waiting for user input, ignoring request.")
            return

        if executor is None:
            executor = PlayerManager.session_player()

        self.prepare_action(action=action, executor=executor)

    def popup(self, name: str, header: str, text: str):
        messenger.send("ui.request.open.popup", [name, header, text])

    def refresh_city(self, city: City | None = None, *args: Any, **kwargs: Any):
        if self.city_ui is not None:
            if city is not None:
                self.city_ui.set_city(city)
            self.city_ui.update()

    def on_escape(self):
        if self.research is not None and self.research.is_open:
            self.close_research()
            return

        screen: PauseMenu | Screen = self.ui_manager.get_screen("pause_menu")

        if screen.pause_menu._is_open or self.player_info is not None:  # type: ignore
            MessengerGlobal.messenger.send("ui.update.ui.hide_pause")
        else:
            show_pause: bool = True
            if self.civics is not None and self.civics.is_open:
                self.close_civics()
                show_pause = False
            if self.research is not None and self.research.is_open:
                self.close_research()
                show_pause = False
            if self.inspect is not None and self.inspect.is_open:
                self.close_inspect()
                show_pause = False
            if self.debug_actions is not None and self.debug_actions.is_open:
                self.close_debug_actions()
                show_pause = False
            if self.log.is_open:
                self.close_log()

            self.clear_selected_unit()
            self.clear_selected_tile()
            self.clear_action_bar()

            if show_pause:
                MessengerGlobal.messenger.send("ui.update.ui.show_pause")

    def on_unit_destroyed(self, unit: BaseEntity):
        self.clear_action_bar()

    def process_enemy_city_click(self, city: Any):
        self.popup("enemy_city_selected", "Enemy City", f"City: {city.name}\nOwner: {city.player.name}")
        if self.city_ui is not None and not self.city_ui.is_hidden():
            self.showing_city = None
            self.close_city_ui()

    def process_city_click(self, city: Any):
        self.open_city_ui(city=city)

    def unregister(self):
        self.logger.info("Unregistering event listeners.")

    def get_debug_frame(self) -> DebugPanel:
        if self.debug_frame is None:
            raise AssertionError("Debug panel is not initialized.")
        return self.debug_frame

    def get_stats_frame(self) -> StatsPanel:
        if self.stats_frame is None:
            raise AssertionError("Camera panel is not initialized.")
        return self.stats_frame

    def get_action_bar_frame(self) -> ActionBar:
        if self.action_bar_frame is None:
            raise AssertionError("Action bar is not initialized.")
        return self.action_bar_frame

    def get_debug_actions(self) -> DebugActions:
        if self.debug_actions is None:
            raise AssertionError("Debug actions is not initialized.")
        return self.debug_actions

    def get_debug_map_stats(self) -> DebugMapStats:
        if self.debug_map_stats is None:
            raise AssertionError("Debug map stats is not initialized.")
        return self.debug_map_stats

    def get_turn_control(self) -> PlayerTurnControl:
        if self.player_turn_control is None:
            raise AssertionError("Player turn control is not initialized.")
        return self.player_turn_control

    def get_root_layout(self) -> FloatLayout:
        if self.root_layout is None:
            raise AssertionError("Root layout is not initialized.")
        return self.root_layout

    def get_city_ui(self) -> CityUI:
        if self.city_ui is None:
            raise AssertionError("City UI is not initialized.")
        return self.city_ui

    def get_top_bar(self) -> TopBar:
        if self.top_bar is None:
            raise AssertionError("Top bar is not initialized.")
        return self.top_bar

    def get_research(self) -> Research:
        if self.research is None:
            raise AssertionError("Research is not initialized.")
        return self.research

    def get_civics(self) -> Civics:
        if self.civics is None:
            raise AssertionError("Civics is not initialized.")
        return self.civics

    def get_player_list(self) -> PlayerList:
        if self.player_list is None:
            raise AssertionError("Player list is not initialized.")
        return self.player_list

    def build_screen(self):
        self.logger.info("Building game UI screen.")
        self.root_layout = FloatLayout(size_hint=(1, 1))

        self.root_layout.add_widget(self.build_action_bar())  # type: ignore
        self.root_layout.add_widget(self.build_player_turn_control())  # type: ignore

        if self.action_bar_frame is None or self.player_turn_control is None:
            raise AssertionError("Action bar, debug panel, or stats panel, player_turn_control is not initialized.")

        self.logger.info("Game UI screen built.")
        self.logger.info("Registering non-collidable UI elements.")

        self.register_non_collidable(self.action_bar_frame.frame)  # type: ignore
        self.register_non_collidable(self.player_turn_control.frame)  # type: ignore

        self.logger.info("Non-collidable UI elements registered.")
        self.add_widget(self.root_layout)

    def bring_to_front(self, widget: Widget):
        parent: Widget = widget.parent
        if widget in parent.children:
            parent.remove_widget(widget)
            parent.add_widget(widget)
        elif widget in self.children:
            self.remove_widget(widget)
            self.add_widget(widget)

    def send_to_back(self, widget: Widget):
        parent: Widget = widget.parent
        if widget in parent.children:
            parent.remove_widget(widget)
            parent.add_widget(widget, len(parent.children) - 1)
        elif widget in self.children:
            self.remove_widget(widget)
            self.add_widget(widget, index=len(self.children) - 1)

    def build_inspect_entity(self) -> InspectEntity:
        self.inspect = InspectEntity(self)
        return self.inspect

    def build_action_bar(self) -> GridLayout:
        self.action_bar_frame = ActionBar()
        return self.action_bar_frame.build()

    def build_stats_frame(self) -> FloatLayout:
        self.stats_frame = StatsPanel(base=self._base)
        self.debug_panels_showing_state["stats"] = True
        return self.stats_frame.build()

    def build_debug_frame(self) -> FloatLayout:
        self.debug_frame = DebugPanel(base=self._base)
        self.debug_panels_showing_state["debug"] = True
        return self.debug_frame.build_debug_frame()

    def build_debug_actions(self) -> DebugActions:
        self.debug_actions = DebugActions(screen=self)
        return self.debug_actions

    def build_debug_map_stats(self) -> GridLayout:
        self.debug_map_stats = DebugMapStats(base=self._base, logger=self.logger)
        return self.debug_map_stats.build()

    def build_player_turn_control(self) -> FloatLayout:
        self.player_turn_control = PlayerTurnControl(base=self._base)
        return self.player_turn_control.build_debug_frame()

    def build_top_bar(self) -> TopBar:
        self.top_bar = TopBar(base=self._base, background_color=(0, 0, 0, 0.9), border=(0, 0, 0, 0))
        return self.top_bar.build()

    def build_research(self) -> Research:
        if self.player is None or (tree := self.player.tech.get_tree()) is None:
            raise AssertionError("Player or tech tree is not initialized.")
        self.research = Research(tree=tree, manager=self)
        self.research.build()
        return self.research

    def build_civics(self) -> Civics:
        if self.player is None:
            raise AssertionError("Player is not initialized.")
        tree: CivicTree | None = self.player.civics.get_tree()

        if tree is None:
            raise AssertionError("Civic tree is not initialized.")

        if self.civics is not None:
            self.remove_widget(self.civics)

        self.civics = Civics(tree=tree, manager=self)
        return self.civics

    def build_player_list(self) -> PlayerList:
        self.player_list = PlayerList(base=self._base)
        self.player_list.build()
        self.add_widget(self.player_list)
        return self.player_list

    def build_player_info(self) -> PlayerInfo:
        self.player_info = PlayerInfo()
        self.player_info.build()
        self.add_widget(self.player_info)
        return self.player_info

    def build_combat_log(self) -> PlayerCombatLog:
        combat_log = CombatLog()
        logs: List[CombatLogEntry] = combat_log.get_entries(PlayerManager.session_player())
        self.player_combat_log = PlayerCombatLog(log=logs)
        self.player_combat_log.build()
        self.player_combat_log.update()
        self.add_widget(self.player_combat_log)
        return self.player_combat_log

    def build_messenger(self) -> MessageRenderer:
        messenger: Messenger = PlayerManager.session_player().messenger
        assert isinstance(messenger, Messenger), "Messenger is not an instance of Messenger class."
        self.messenger = MessageRenderer(messenger=messenger)
        self.add_widget(self.messenger)
        return self.messenger

    def refresh_top_bar(self, dt: Optional[float] = None):
        if self.top_bar is None:
            self.build_top_bar()

        if self.top_bar is None:
            raise AssertionError("Top bar is not initialized.")

        self.top_bar.update()

    def clear_selected_unit(self):
        self.clear_action_bar()
        self.ui_manager.clear_selected_unit()
        self.close_unit_summary_panel()

    def clear_selected_tile(self):
        self.ui_manager.clear_selected_tile()
        self.close_city_ui()

    def toggle_log(self):
        if not self.log.is_open:
            self.open_log()
        else:
            self.close_log()

    def toggle_debug_panels(self, debug: bool, stats: bool, actions: bool):
        if self.debug_frame is None or self.stats_frame is None:
            raise AssertionError("debug panel, or stats panel is not initialized.")

        self.get_debug_frame().get_frame().disabled = not debug
        self.get_debug_frame().get_frame().opacity = 0 if not debug else 1
        self.get_stats_frame().get_frame().disabled = not stats
        self.get_stats_frame().get_frame().opacity = 0 if not stats else 1

        if debug and not self.debug_panels_showing_state["debug"]:
            self.add_widget(self.debug_frame)
            self.register_non_collidable(self.debug_frame.frame)  # type: ignore
        else:
            frame = self.get_debug_frame()
            for child in frame.children:  # type: ignore
                frame.remove_widget(child)  # type: ignore
            self.remove_widget(frame)  # type: ignore
            self.unregister_non_collidable(self.debug_frame.frame)  # type: ignore

        if stats and not self.debug_panels_showing_state["stats"]:
            frame = self.get_stats_frame().get_frame()
            self.add_widget(frame)
            self.register_non_collidable(self.stats_frame.frame)  # type: ignore
        else:
            frame = self.get_stats_frame()
            frame.hide()
            self.register_non_collidable(self.stats_frame.frame)  # type: ignore

    def process_tile_click(self, tile: Optional[Union[str, Tile]] = None) -> bool:
        if isinstance(tile, str):
            _tile: Optional[Tile] = self.world_manager.lookup_on_tag(tile)
        else:
            _tile: Optional[Tile] = tile if isinstance(tile, Tile) else None

        tile_change: bool = False

        if _tile is None:
            return False

        if self.city_ui is not None:
            self.close_city_ui()
            self.showing_city = None

        # self.debug_frame.update_debug_info_for_tile(_tile)  # type: ignore # We know it exists because it's initialized in build_screen

        if self.wait_for_next_input_of_user is False:
            self.clear_selected_unit()  # Clear the action bar

        generate_buttons: bool = True
        # If we are waiting for an action, execute it now
        if self.wait_for_next_input_of_user and self.wait_for_action_of_user is not None:
            self.run_prepared_action(tile=tile)  # type: ignore
            self.wait_for_action_of_user = None  # Call the stored action with the tile
            self.wait_for_next_input_of_user = False

            if self.wait_for_action is not None and self.wait_for_action.keep_targeting_after_use is False:
                if self.ui_manager.select_tile(_tile):
                    tile_change = True  # We changed the selected tile, so we need to update the unit selection
            else:
                generate_buttons = False

            self.wait_for_action_of_user = None  # Reset state
            self.action_waiting_for = None  # Reset action waiting state

        else:
            self.ui_manager.select_tile(_tile)
            tile_change = True

        if (unit := self.ui_manager.current_unit) is not None and generate_buttons is True:
            self.generate_buttons_for_unit_actions(unit)  # Update

        return tile_change

    def process_unit_click(self, unit: Optional[Union[str, "Tile"]] = None) -> bool:
        self.logger.debug(f"Unit clicked: {unit}")
        if isinstance(unit, str):
            _unit: Optional[BaseEntity] = EntityManager.get_singleton_instance().get(EntityType.UNIT, unit)
        else:
            _unit: Optional[BaseEntity] = unit if isinstance(unit, Unit) else None

        should_select_unit: bool = True

        if _unit is None or not isinstance(_unit, Unit):
            self.logger.warning(f"Unit {_unit} not found or is not a Unit instance.")
            return False

        if self.wait_for_action_of_user is not None and self.wait_for_action_of_user:
            self.run_prepared_action(unit=_unit)  # type: ignore
            if self.wait_for_action is not None and self.wait_for_action.keep_targeting_after_use is True:
                # If the action keeps targeting, we don't change the selected unit
                should_select_unit = False
            self.wait_for_next_input_of_user = False
            self.wait_for_action_of_user = None  # Reset state
            # self.wait_for_action = None
            self.action_waiting_for = None

        if should_select_unit is True and _unit.is_alive():
            self.ui_manager.select_unit(_unit)  # type: ignore # We know it exists but because its a weak reference, mypy doesn't know it exists
            self.open_unit_summary_panel(_unit)
        else:
            self.close_unit_summary_panel()

        self.clear_action_bar()
        if self.ui_manager.current_unit is not None:
            self.generate_buttons_for_unit_actions(self.ui_manager.current_unit)

        if self.city_ui is not None:
            self.close_city_ui()
            self.showing_city = None

        return should_select_unit

    def refresh_action_bar(self, dt: Optional[float] = None):
        if self.ui_manager.current_unit is None:
            self.clear_action_bar()
            return

        self.clear_action_bar()
        self.generate_buttons_for_unit_actions(self.ui_manager.current_unit)

    def generate_buttons_for_unit_actions(self, unit: str | BaseEntity):
        _unit: Optional[Unit] = None
        if isinstance(unit, str):
            _unit: Optional[Unit] = self.unit_manager.find_unit(unit)
        else:
            _unit: Optional[Unit] = unit if isinstance(unit, Unit) else None

        if _unit is not None:
            if self.action_bar_frame is None:
                raise AssertionError("Action bar frame is not initialized.")
            self.action_bar_frame.generate(
                unit=_unit,
                action_preparer=self.prepare_action,
                build_action_preparer=self.prepare_build_action,
            )

    def update_ui_elements(self):
        self.refresh_action_bar()
        self.refresh_targeting_ui()

    def refresh_targeting_ui(self):
        if self.player_attack_info is not None:
            self.player_attack_info.update()

    def clear_action_bar(self):
        if self.action_bar_frame is None:
            return
        self.action_bar_frame.clear_buttons()

    def get_selected_tile(self) -> Optional[Tile]:
        return self.ui_manager.get_selected_tile()

    def get_selected_unit(self) -> Optional[Unit]:
        return self.ui_manager.get_selected_unit()

    def prepare_build_action(self, improvement: Type[Improvement], unit: Unit):
        from gameplay.actions.unit.build import BuildAction

        action = BuildAction(improvement, unit)
        action.action_kwargs["unit"] = unit
        action.action_kwargs["improvement"] = improvement
        action.run()

        self.clear_action_bar()
        self.generate_buttons_for_unit_actions(unit)

    def prepare_action(self, *args: Any, **kwargs: Any):
        action: Action | None = kwargs.get("action")
        executor: T_TARGET | None = kwargs.get("executor")

        assert isinstance(action, Action), "Action must be an instance of Action class."

        if action.is_disabled:
            self.logger.warning(f"Action {action.name} is disabled and cannot be executed.")
            return

        kwargs.pop("executor")
        kwargs.pop("action", None)

        action.action_kwargs = kwargs
        action.action_kwargs["executor"] = executor

        if action.on_the_spot_action:
            action.run()
            if action.remove_actions_after_use:
                self.get_action_bar_frame().clear_widgets()  # type: ignore
            return

        self.wait_for_next_input_of_user = True
        self.wait_for_action_of_user = action  # type: ignore
        self.waiting_for_world_input = True  # type: ignore # We know it exists because it's initialized in build_screen

    def run_prepared_action(self, *args: Any, **kwargs: Any):
        if self.wait_for_action_of_user is None:
            self.logger.warning("No action prepared to run.")
            return

        if self.wait_for_next_input_of_user is False:
            self.logger.warning("Not waiting for user input, cannot run prepared action.")
            return

        self.execute_action(self.wait_for_action_of_user, *args, **kwargs)  # type: ignore

    def execute_action(self, action: Action, *args: Any, **kwargs: Any):
        unit: Unit | None = kwargs.pop("unit", None)
        tile: Tile | None = kwargs.pop("tile", None)

        if not action.debug_action and unit is None and tile is None:
            self.logger.warning("No unit or tile selected for action execution.")
            return

        if action.targeting_tile_action and tile is None:
            self.logger.warning("Action requires a tile target, but none is selected.")
            return

        if action.targeting_unit_action and unit is None:
            self.logger.warning("Action requires a unit target, but none is selected.")
            return

        if action.targeting_tile_action:
            action.action_kwargs["target"] = tile
        if action.targeting_unit_action:
            action.action_kwargs["target"] = unit

        action.action_kwargs.update(kwargs)
        action.run()

        self.wait_for_next_input_of_user = False
        self.wait_for_action_of_user = None
        self.unit_waiting_for_action = None

        if action.remove_actions_after_use:
            self.clear_action_bar()

    def open_player_attack_info(self, source: Unit, target: Unit | None = None):
        self.player_attack_info = TargetingDuelPanel()
        self.player_attack_info.set_units(source, target)
        self.add_widget(self.player_attack_info)

    def close_player_attack_info(self):
        if self.player_attack_info is not None:
            self.player_attack_info.destroy()
            self.remove_widget(self.player_attack_info)
            self.player_attack_info = None

    def build_unit_path_renderer(self):
        self.unit_path_renderer = MovementPathBlocksRenderer(self._base.render)

    def open_unit_path_renderer(self, source: T_TARGET, target: T_TARGET):
        if self.unit_path_renderer is None:
            self.build_unit_path_renderer()
        assert self.unit_path_renderer is not None, "Unit path renderer is not initialized."

        source_tile: Tile = source.get_tile()
        target_tile: Tile = target.get_tile()

        tile_path: List[Tile] | None = TileRepository.astar(
            source_tile, target_tile, avoid_occupied=False, movement_points=1.0
        )
        self.unit_path_renderer.set_path([Vec3(*tile.get_pos()) for tile in tile_path] if tile_path is not None else [])
        self.unit_path_renderer.show()

    def close_unit_path_renderer(self):
        if self.unit_path_renderer is not None:
            self.unit_path_renderer.hide()

    def open_unit_summary_panel(self, unit: Unit):
        if self.player_target_info is None:
            self.player_target_info = UnitSummaryPanel()
            self.add_widget(self.player_target_info)
        self.player_target_info.set_unit(unit)

    def close_unit_summary_panel(self):
        if self.player_target_info is not None:
            self.remove_widget(self.player_target_info)
            self.player_target_info = None

    def open_log(self):
        self.log.open()
        self.lock_input()

    def close_log(self):
        self.unregister_non_collidable(self.log)
        self.log.done()
        self.unlock_input()

    def open_city_ui(self, city: City):
        self.close_city_ui()
        self.city_ui = CityUI(screen=self, base=self._base, name="", background_color=(0, 0, 0, 1), border=(0, 0, 0, 1))

        assert self.city_ui is not None, "City UI is not initialized."
        assert self.city_ui.frame is not None, "City UI frame is not initialized."

        assert self.root_layout is not None, "Root layout is not initialized."
        self.root_layout.add_widget(self.city_ui.build())
        self.city_ui.show(city=city)

    def close_city_ui(self):
        if self.city_ui is None:
            return

        assert self.city_ui is not None, "City UI is not initialized."
        assert self.root_layout is not None, "Root layout is not initialized."
        self.city_ui.hide()
        self.root_layout.remove_widget(self.city_ui)  # type: ignore
        self.popup_disabled = True

    def open_debug_actions(self):
        if self.debug_actions is None:
            self.debug_actions = self.build_debug_actions()
            self.debug_actions.show()
            self.register_non_collidable(self.debug_actions.frame)
            assert self.root_layout is not None, "Root layout is not initialized."
            self.root_layout.add_widget(self.debug_actions.frame)  # type: ignore
        self.lock_input()

    def close_debug_actions(self):
        if self.debug_actions is not None:
            self.unregister_non_collidable(self.debug_actions.frame)  # type: ignore
            assert self.root_layout is not None, "Root layout is not initialized."
            self.debug_actions.hide()
            self.root_layout.remove_widget(self.debug_actions.frame)  # type: ignore
            self.popup_disabled = True
            self.debug_actions = None
        self.unlock_input()

    def open_inspect(self):
        if self.inspect is None:
            self.inspect = self.build_inspect_entity()
            self.inspect.show()
            self.register_non_collidable(self.inspect.frame)  # type: ignore
            assert self.root_layout is not None, "Root layout is not initialized."
            self.root_layout.add_widget(self.inspect.frame)  # type: ignore
        self.lock_input()

    def close_inspect(self):
        if self.inspect is not None:
            self.unregister_non_collidable(self.inspect.frame)  # type: ignore
            assert self.root_layout is not None, "Root layout is not initialized."
            self.inspect.hide()
            self.root_layout.remove_widget(self.inspect.frame)  # type: ignore
            self.popup_disabled = True
            self.inspect = None
        self.unlock_input()

    def open_research(self):
        if self.research is None:
            self.research = self.build_research()
            self.register_non_collidable(self.research)
            assert self.root_layout is not None, "Root layout is not initialized."
            self.root_layout.add_widget(self.research)
        self.lock_input()

    def open_civics(self):
        if self.civics is None:
            self.civics = self.build_civics()
            self.register_non_collidable(self.civics)
            assert self.root_layout is not None, "Root layout is not initialized."
            self.root_layout.add_widget(self.civics)
        self.lock_input()

    def open_player_info(self, player: Player):
        if self.player_info is None:
            self.player_info = self.build_player_info()
            self.register_non_collidable(self.player_info)
            assert self.root_layout is not None, "Root layout is not initialized."
            self.root_layout.add_widget(self.player_info)
        self.lock_input()

    def close_research(self):
        if self.research is not None:
            self.unregister_non_collidable(self.research)
            assert self.root_layout is not None, "Root layout is not initialized."
            self.research.popup_disabled = True
            self.root_layout.remove_widget(self.research)
            self.popup_disabled = True
            self.research = None
        self.unlock_input()

    def close_civics(self):
        if self.civics is not None:
            self.unregister_non_collidable(self.civics)
            assert self.root_layout is not None, "Root layout is not initialized."
            self.civics.destroy()
            self.root_layout.remove_widget(self.civics)
            self.popup_disabled = True
            self.civics = None
        self.unlock_input()

    def close_player_info(self):
        if self.player_info is not None:
            self.unregister_non_collidable(self.player_info)
            assert self.root_layout is not None, "Root layout is not initialized."
            self.root_layout.remove_widget(self.player_info)
            self.popup_disabled = True
            self.player_info = None
        self.unlock_input()

    def toggle_research(self):
        if self.research is None:
            self.open_research()
        else:
            self.close_research()

    def toggle_civics(self):
        if self.civics is None:
            self.open_civics()
        else:
            self.close_civics()

    def inspect_element(self, entity: Inspectable) -> None:
        if self.inspect is None:
            self.open_inspect()
            assert self.inspect is not None, (
                "Inspect did not get opened properly or assigned to the instance"
            )  # to make mypy happy
            self.inspect.inspect_entity(entity)

    def lock_input(self):
        MessengerGlobal.messenger.send("system.input.raycaster_off")
        MessengerGlobal.messenger.send("system.input.disable_zoom")
        MessengerGlobal.messenger.send("system.input.disable_control")
        MessengerGlobal.messenger.send("system.input.camera_lock")

    def unlock_input(self):
        MessengerGlobal.messenger.send("system.input.camera_unlock")
        MessengerGlobal.messenger.send("system.input.raycaster_on")
        MessengerGlobal.messenger.send("system.input.enable_zoom")
        MessengerGlobal.messenger.send("system.input.enable_control")

    def destroy(self):
        self.logger.info("Destroying GameUIScreen.")
        self.unregister()
        self.clear_action_bar()
        self.clear_selected_unit()
        self.ignore_all()
