from functools import partial
from logging import Logger
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Type
from weakref import ReferenceType

from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from direct.showbase.MessengerGlobal import messenger
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from gameplay.city import City
from gameplay.civic import CivicTree
from gameplay.improvement import Improvement
from gameplay.player import Player
from gameplay.tile import Tile
from gameplay.unit import Unit
from managers.combat import test_combat_outcome
from managers.entity import EntityManager, EntityType
from managers.player import PlayerManager
from managers.unit import UnitManager
from managers.world import World
from menus.kivy.mixins.collidable import CollisionPreventionMixin
from menus.kivy.parts.action_bar import ActionBar
from menus.kivy.parts.city import CityUI
from menus.kivy.parts.civics import Civics
from menus.kivy.parts.debug import DebugPanel
from menus.kivy.parts.debug_actions import DebugActions
from menus.kivy.parts.debug_map_stats import DebugMapStats
from menus.kivy.parts.player_combat_log import PlayerCombatLog
from managers.combat_log import CombatLog
from menus.kivy.parts.player_info import PlayerInfo
from menus.kivy.parts.player_list import PlayerList
from menus.kivy.parts.player_turn_control import PlayerTurnControl
from menus.kivy.parts.research import Research
from menus.kivy.parts.stats import StatsPanel
from menus.kivy.parts.top_bar import TopBar
from menus.screens.pause_menu import PauseMenu
from system.actions import Action
from system.camera import Camera
from system.entity import BaseEntity

if TYPE_CHECKING:
    from main import SCIV


class GameUIScreen(Screen, CollisionPreventionMixin, DirectObject):
    debug_data: Dict[str, str] = {
        "state": "Playing",
    }

    def __init__(self, *args: Any, **kwargs: Any):
        if "base" not in kwargs:
            raise ValueError("GameUIScreen requires a 'base' keyword argument.")
        self._base: "SCIV" = kwargs.pop("base", None)

        from managers.ui import ui

        super().__init__(base=self._base, *args, **kwargs)  # type: ignore

        self.world_manager = World.get_singleton_instance()
        self.camera: Camera = Camera.get_singleton_instance()
        self.unit_manager: UnitManager = UnitManager.get_singleton_instance()
        self.ui_manager: ui = ui.get_singleton_instance()
        self.player: Optional[Player] = None

        self.waiting_for_world_input: bool = False

        self.wait_for_next_input_of_user: bool = False
        self.wait_for_action_of_user: Optional[partial[Callable[[Optional[Tile]], None]]] = None
        self.unit_waiting_for_action: Optional[Unit] = None

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

        self.logger: Logger = self._base.logger.graphics.getChild("ui.game_ui")

        self.showing_city: Optional[City] = None

        self.debug_panels_showing_state: Dict[str, bool] = {
            "stats": False,
            "actions": False,
            "debug": False,
        }

        self.logger.info("Game UI Screen initialized.")
        self.register()
        self.logger.info("Game UI Screen built.")

    def on_game_start(self, *args: Any):
        self.player = PlayerManager.session_player()
        self.build_player_list()
        self.build_player_info()
        self.build_combat_log()

        if self.debug_map_stats is not None:
            self.debug_map_stats.update()

        self.root_layout.add_widget(self.build_debug_map_stats())  # type: ignore
        self.root_layout.add_widget(self.build_debug_frame())  # type: ignore
        self.root_layout.add_widget(self.build_top_bar())  # type: ignore
        self.root_layout.add_widget(self.build_stats_frame())  # type: ignore

        self.register_non_collidable(self.player_combat_log)  # type: ignore
        self.accept(
            "escape", self.on_escape
        )  # this is to prevent the pause menu from being opened before the game starts
        MessengerGlobal.messenger.send("ui.update.ui.hide_pause")

    def on_game_end(self, *args: Any):
        self.ignore("escape")

    def reset(self):
        self.logger.info("Resetting game UI screen.")
        self.clear_action_bar()
        self.update_ui_geometry_cache()
        if self.city_ui is not None:
            self.city_ui.hide()
        if self.top_bar is not None:
            self.top_bar.update()

    def register(self):
        self.logger.info("Registering event listeners.")

        self.accept("ui.update.user.tile_clicked", self.process_tile_click)
        self.accept("ui.update.user.unit_clicked", self.process_unit_click)
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

        self.accept("t", self.toggle_research)
        self.accept("c", self.toggle_civics)

    def popup(self, name: str, header: str, text: str):
        messenger.send("ui.request.open.popup", [name, header, text])

    def on_escape(self):
        if (
            self.research is not None and self.research.is_open
        ):  # if the research screen is open exit as it is handled in the research screen
            self.close_research()
            return

        screen: PauseMenu | Screen = self.ui_manager.get_screen("pause_menu")

        if screen.pause_menu._is_open or self.player_info.is_open:  # type: ignore
            MessengerGlobal.messenger.send("ui.update.ui.hide_pause")
        else:
            if self.civics is not None and self.civics.is_open:
                self.close_civics()
            if self.research is not None and self.research.is_open:
                self.close_research()

            self.clear_selected_unit()
            self.clear_action_bar()

            MessengerGlobal.messenger.send("ui.update.ui.show_pause")

    def on_unit_destroyed(self, unit: BaseEntity):
        self.clear_action_bar()

    def process_enemy_city_click(self, city: Any):
        self.popup("enemy_city_selected", "Enemy City", f"City: {city.name}\nOwner: {city.player.name}")
        if self.city_ui is not None and not self.city_ui.is_hidden():
            self.showing_city = None
            self.get_city_ui().hide()

    def process_city_click(self, city: Any):
        if self.showing_city is None or city != self.showing_city:
            if self.city_ui is None or self.city_ui.city_label is None:
                raise AssertionError("City UI is not initialized.")

            self.showing_city = city
            self.get_city_ui().show(city=city)
        else:
            if not self.get_city_ui().is_hidden():
                self.showing_city = None
                self.get_city_ui().hide()

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
        self.root_layout.add_widget(self.build_debug_actions())  # type: ignore
        self.root_layout.add_widget(self.build_player_turn_control())  # type: ignore
        self.root_layout.add_widget(self.build_city_ui())  # type: ignore

        if (
            self.action_bar_frame is None
            or self.debug_actions is None
            or self.player_turn_control is None
            or self.city_ui is None
        ):
            raise AssertionError("Action bar, debug panel, or stats panel, player_turn_control is not initialized.")

        self.logger.info("Game UI screen built.")
        self.logger.info("Registering non-collidable UI elements.")

        self.register_non_collidable(self.action_bar_frame.frame)  # type: ignore
        self.register_non_collidable(self.debug_actions.frame)  # type: ignore
        self.register_non_collidable(self.player_turn_control.frame)  # type: ignore
        self.register_non_collidable(self.city_ui.frame)  # type: ignore

        self.logger.info("Non-collidable UI elements registered.")
        self.add_widget(self.root_layout)

    def bring_to_front(self, widget: Widget):
        parent: Widget = widget.parent
        # remove then add without index → goes to the end of children → drawn last → on top
        if widget in parent.children:
            # if the widget is already in the parent, remove it first
            parent.remove_widget(widget)
            parent.add_widget(widget)
        elif widget in self.children:
            # if the widget is in the root layout, remove it first
            self.remove_widget(widget)
            self.add_widget(widget)

    def send_to_back(self, widget: Widget):
        parent: Widget = widget.parent
        if widget in parent.children:
            # if the widget is already in the parent, remove it first
            parent.remove_widget(widget)
            # add without index → goes to the end of children → drawn last → on top
            parent.add_widget(widget, len(parent.children) - 1)
        elif widget in self.children:
            # if the widget is in the root layout, remove it first
            self.remove_widget(widget)
            # add at index=0 → goes to the end of children → drawn last → on top
            # this is a workaround for kivy not allowing to add a widget at index=0
            self.add_widget(widget, index=len(self.children) - 1)

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

    def build_debug_actions(self) -> BoxLayout:
        self.debug_actions = DebugActions(base=self._base, logger=self.logger)
        self.debug_panels_showing_state["actions"] = True
        return self.debug_actions.build()

    def build_debug_map_stats(self) -> GridLayout:
        self.debug_map_stats = DebugMapStats(base=self._base, logger=self.logger)
        return self.debug_map_stats.build()

    def build_player_turn_control(self) -> FloatLayout:
        self.player_turn_control = PlayerTurnControl(base=self._base)
        return self.player_turn_control.build_debug_frame()

    def build_city_ui(self) -> BoxLayout:
        self.city_ui = CityUI(base=self._base, name="", background_color=(0, 0, 0, 1), border=(0, 0, 0, 1))
        result = self.city_ui.build()
        self.city_ui.hide()
        return result

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
        # self.player_info.build()
        # self.player_info.hide_popup()
        self.add_widget(self.player_info)
        return self.player_info

    def build_combat_log(self) -> PlayerCombatLog:
        combat_log = CombatLog()
        test_objects = test_combat_outcome()
        for obj in test_objects:
            combat_log.add_entry(CombatLog.entry_from_outcome(obj), both_sides=False)
        logs = combat_log.get_entries(PlayerManager.session_player())

        self.player_combat_log = PlayerCombatLog(log=logs)
        self.player_combat_log.build()
        self.player_combat_log.update()
        self.add_widget(self.player_combat_log)
        return self.player_combat_log

    def refresh_top_bar(self):
        if self.top_bar is None:
            raise AssertionError("Top bar is not initialized.")
        self.top_bar.update()

    def clear_selected_unit(self):
        self.clear_action_bar()
        self.ui_manager.clear_selected_unit()

    def toggle_debug_panels(self, debug: bool, stats: bool, actions: bool):
        if self.debug_actions is None or self.debug_frame is None or self.stats_frame is None:
            raise AssertionError("Debug actions, debug panel, or stats panel is not initialized.")

        self.get_debug_frame().get_frame().disabled = not debug
        self.get_debug_frame().get_frame().opacity = 0 if not debug else 1
        self.get_stats_frame().get_frame().disabled = not stats
        self.get_stats_frame().get_frame().opacity = 0 if not stats else 1

        if actions and not self.debug_panels_showing_state["actions"]:
            self.add_widget(self.debug_actions)
            self.register_non_collidable(self.debug_actions.frame)  # type: ignore
        else:
            frame = self.get_action_bar_frame().get_frame()
            for child in frame.children:  # type: ignore
                frame.remove_widget(child)  # type: ignore
            self.remove_widget(frame)  # type: ignore
            self.remove_widget(self.debug_actions)  # type: ignore
            self.unregister_non_collidable(self.debug_actions.frame)  # type: ignore

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

    def process_tile_click(self, tile: str):
        _tile: Optional[Tile] = self.world_manager.lookup_on_tag(tile)
        if _tile is None:
            return

        if not _tile.is_city():
            self.get_city_ui().hide()
            self.showing_city = None

        self.debug_frame.update_debug_info("\n".join(f"{key}: {value}" for key, value in _tile.to_gui().items()))  # type: ignore # We know it exists because it's initialized in build_screen

        if self.wait_for_next_input_of_user is False:
            self.clear_selected_unit()  # Clear the action bar

        # If we are waiting for an action, execute it now
        if self.wait_for_next_input_of_user and self.wait_for_action_of_user:
            self.wait_for_action_of_user(_tile)  # Call the stored action with the tile
            self.wait_for_next_input_of_user = False
            self.wait_for_action_of_user = None  # Reset state

        if (unit := self.ui_manager.current_unit) is not None:
            self.generate_buttons_for_unit_actions(unit)  # Update

    def process_unit_click(self, unit: str):
        self.logger.debug(f"Unit clicked: {unit}")
        _unit: ReferenceType[BaseEntity] = EntityManager.get_singleton_instance().get_ref_weak(EntityType.UNIT, unit)

        if unit != self.ui_manager.current_unit:
            self.generate_buttons_for_unit_actions(unit)

        if self.showing_city is not None:
            self.get_city_ui().hide()
            self.showing_city = None

        self.debug_frame.update_debug_info("\n".join(f"{key}: {value}" for key, value in _unit().to_gui().items()))  # type: ignore # We know it exists because it's initialized in build_screen

    def generate_buttons_for_unit_actions(self, unit: str | BaseEntity):
        if self.action_bar_frame is None:
            return

        _unit: Optional[Unit] = None
        if isinstance(unit, str):
            _unit: Optional[Unit] = self.unit_manager.find_unit(unit)
        else:
            _unit: Optional[Unit] = unit if isinstance(unit, Unit) else None

        if _unit is not None:
            self.action_bar_frame.clear_buttons()
            actions = _unit.get_actions()
            for action in actions:
                button = Button(
                    text=str(action.name),
                    size_hint=(None, None),
                    width=100,
                    height=75,
                )
                button.bind(on_press=partial(self.prepare_action, action, _unit))  # type: ignore
                self.action_bar_frame.add_button(button)

            if _unit.can_build is True:
                improvements: List[Type[Improvement]] = _unit.get_tile().get_buildable_improvements()
                for _improvement in improvements:
                    # Check if the improvement is placeable on the tile
                    condition_check = (
                        isinstance(_improvement.placeable_on_condition, bool)
                        and _improvement.placeable_on_condition is True
                    ) or (
                        isinstance(_improvement.placeable_on_condition, Callable)
                        and _improvement.placeable_on_condition() is True
                    )

                    # Check if the improvement is visible or if we don't show the button
                    visible_condition_check = (
                        isinstance(_improvement.visible_on_condition, bool)
                        and _improvement.visible_on_condition is True
                    ) or (
                        isinstance(_improvement.visible_on_condition, Callable)
                        and _improvement.visible_on_condition() is True
                    )
                    if (
                        _improvement.placeable_on_tiles is True
                        and not _unit.get_tile().improvements().has(_improvement)
                        and visible_condition_check
                    ):
                        button: Button = Button(
                            text=str(_improvement.name),
                            size_hint=(None, None),
                            width=100,
                            height=75,
                        )
                        button.disabled = (
                            not _unit.can_build or _unit.get_tile().owner != _unit.owner or condition_check is False
                        )
                        button.bind(  # type: ignore
                            on_press=lambda x, improvement=_improvement: self.prepare_build_action(improvement, _unit)  # type: ignore
                        )
                        self.action_bar_frame.add_button(button)

    def clear_action_bar(self):
        if self.action_bar_frame is None:
            return

        self.action_bar_frame.clear_buttons()

    def prepare_build_action(self, improvement: Type[Improvement], unit: Unit):
        from gameplay.actions.unit.build import BuildAction

        action = BuildAction(improvement, unit)
        action.action_kwargs["unit"] = unit
        action.action_kwargs["improvement"] = improvement
        action.run()

        # this is to prevent the action bar having actions that are not valid anymore.
        self.clear_action_bar()
        self.generate_buttons_for_unit_actions(unit)

    def prepare_action(self, action: Action, unit: Unit, _):
        """Prepares an action and waits for the next tile click before executing."""
        if action.on_the_spot_action:
            action.action_kwargs["unit"] = unit
            action.run()
            if action.remove_actions_after_use:
                self.get_action_bar_frame().clear_widgets()  # type: ignore
            return

        self.wait_for_next_input_of_user = True
        self.wait_for_action_of_user = partial(self.execute_action, action, unit)  # type: ignore
        self.unit_waiting_for_action = unit
        self.waiting_for_world_input = True  # type: ignore # We know it exists because it's initialized in build_screen

    def execute_action(self, action: Action, unit: Unit, tile: Optional[Tile]):
        """Executes the action after tile selection (if required)."""
        action.action_kwargs["unit"] = unit

        if tile is not None:
            action.action_kwargs["tile"] = tile  # Assign the selected tile

        action.run()

        # Reset waiting state
        self.wait_for_next_input_of_user = False
        self.wait_for_action_of_user = None
        self.unit_waiting_for_action = None

        if action.remove_actions_after_use:
            self.clear_action_bar()

    def open_research(self):
        if self.research is None:
            self.research = self.build_research()
            self.register_non_collidable(self.research)
            if self.root_layout is None:
                raise AssertionError("Root layout is not initialized.")
            self.root_layout.add_widget(self.research)
            self.lock_input()

    def open_civics(self):
        if self.civics is None:
            self.civics = self.build_civics()
            self.register_non_collidable(self.civics)
            if self.root_layout is None:
                raise AssertionError("Root layout is not initialized.")
            self.root_layout.add_widget(self.civics)
            self.lock_input()

    def close_research(self):
        if self.research is not None:
            self.unregister_non_collidable(self.research)
            if self.root_layout is None:
                raise AssertionError("Root layout is not initialized.")
            self.root_layout.remove_widget(self.research)
            self.popup_disabled = True
            self.research = None
            self.unlock_input()

    def close_civics(self):
        if self.civics is not None:
            self.unregister_non_collidable(self.civics)
            if self.root_layout is None:
                raise AssertionError("Root layout is not initialized.")
            self.root_layout.remove_widget(self.civics)
            self.popup_disabled = True
            self.civics = None
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
