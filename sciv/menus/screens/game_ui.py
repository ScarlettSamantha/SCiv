from logging import Logger
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type, Union, cast

from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from direct.showbase.MessengerGlobal import messenger
from gameplay.age import Age
from gameplay.city import City
from gameplay.civic import CivicTree
from gameplay.improvement import Improvement
from gameplay.player import Player
from gameplay.repositories.tile import TileRepository
from gameplay.tile import Tile
from gameplay.unit import Unit
from gameplay.unit_path import MovementPathBlocksRenderer
from helpers.debug import Debug
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from managers.ages import AgesManager
from managers.combat import T_TARGET
from managers.combat_log import CombatLog, CombatLogEntry
from managers.config import ConfigManager
from managers.entity import EntityManager, EntityType
from managers.log import LogManager
from managers.player import PlayerManager
from managers.unit import UnitManager
from managers.world import World
from menus.kivy.elements.layout_debug import DraggableLayoutWrapper, LayoutDebugPosition
from menus.kivy.elements.log_popup import LogPopup
from menus.kivy.elements.message import MessageRenderer
from menus.kivy.elements.modal import ModalImagePopup
from menus.kivy.mixins.collidable import CollisionPreventionMixin
from menus.kivy.parts.action_bar import PlayerActionBar
from menus.kivy.parts.city import CityUI
from menus.kivy.parts.civics import Civics
from menus.kivy.parts.debug import DebugPanel
from menus.kivy.parts.debug_actions import DebugActions
from menus.kivy.parts.debug_map_stats import DebugMapStats
from menus.kivy.parts.inspect_entity import InspectEntity
from menus.kivy.parts.minimap import Minimap
from menus.kivy.parts.player_attack import TargetingDuelPanel
from menus.kivy.parts.player_combat_log import PlayerCombatLog
from menus.kivy.parts.player_info import PlayerInfo
from menus.kivy.parts.player_list import PlayerList
from menus.kivy.parts.player_select import TargetPanel
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
        self.action_waiting_for: Optional[Action] = None

        self.debug_panel: Optional[Label] = None
        self.camera_panel: Optional[Label] = None

        self.root_layout: Optional[FloatLayout] = None

        self.action_bar: Optional[PlayerActionBar] = None
        self.debug_frame: Optional[DebugPanel] = None
        self.stats_frame: Optional[StatsPanel] = None
        self.debug_actions: Optional[DebugActions] = None
        self.debug_map_stats: Optional[DebugMapStats] = None
        self.player_turn_control: Optional[PlayerTurnControl] = None
        self.city_ui: Optional[CityUI] = None
        self.top_bar: Optional[TopBar] = None
        self.research: Optional[Research] = None
        self.age_popup: Optional[ModalImagePopup] = None
        self.civics: Optional[Civics] = None
        self.player_list: Optional[PlayerList] = None
        self.player_info: Optional[PlayerInfo] = None
        self.player_combat_log: Optional[PlayerCombatLog] = None
        self.minimap: Optional[Minimap] = None
        self.messenger: Optional[MessageRenderer] = None
        self.inspect: Optional[InspectEntity] = None
        self.player_attack_info: Optional[TargetingDuelPanel] = None
        self.unit_path_renderer: Optional[MovementPathBlocksRenderer] = None
        self.player_target_info: Optional[TargetPanel] = None
        self.logger: Logger = self._base.logger.graphics.getChild("ui.game_ui")
        self.log: LogPopup = LogPopup(handler=LogManager.get_singleton_instance().ui_handler)
        self.config_manager: ConfigManager = ConfigManager.get_singleton_instance()
        self.layout_debug_widgets: Dict[str, DraggableLayoutWrapper] = {}

        self.showing_tile_yield_icons: bool = True

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

    @staticmethod
    def _is_attached(widget: Widget | None) -> bool:
        return widget is not None and getattr(widget, "parent", None) is not None

    def on_game_start(self, *args: Any):
        self.player = PlayerManager.session_player()
        if not self._is_attached(self.player_list):
            self.build_player_list()
        elif self.player_list is not None:
            self.register_non_collidable(self.player_list)

        if not self._is_attached(self.player_combat_log):
            self.build_combat_log()
        elif self.player_combat_log is not None:
            self.player_combat_log.update()

        if not self._is_attached(self.messenger):
            self.build_messenger()
        else:
            self.refresh_messenger()

        if Debug.debug and not self._is_attached(self.stats_frame):
            self.add_widget(self.build_stats_frame())
            if (wrapper := self.layout_debug_widgets.get("stats_panel")) is not None:
                self.register_non_collidable(wrapper)

        if not self._is_attached(self.top_bar):
            self.add_widget(self.build_top_bar())  # type: ignore
        elif self.top_bar is not None:
            self.top_bar.update()

        if not self._is_attached(self.minimap):
            self.add_widget(self.build_minimap())  # type: ignore
        elif self.minimap is not None:
            self.minimap.refresh_full()

        if self.player_combat_log is not None:
            if (wrapper := self.layout_debug_widgets.get("combat_log")) is not None:
                self.register_non_collidable(wrapper)
        if self.player_list is not None:
            self.register_non_collidable(self.player_list)
        if self.minimap is not None:
            self.register_non_collidable(self.minimap)  # type: ignore
        self.apply_layout_debug_settings()
        self.accept(
            "escape", self.on_escape
        )  # this is to prevent the pause menu from being opened before the game starts
        MessengerGlobal.messenger.send("ui.update.ui.hide_pause")

    def on_game_end(self, *args: Any):
        self.ignore("escape")
        manager = self.manager
        if manager is None:
            return

        manager.current = "main_menu"

    def reset(self):
        self.logger.info("Resetting game UI screen.")
        self.clear_action_bar()
        self.update_ui_geometry_cache()
        if self.top_bar is not None:
            self.top_bar.update()
        if self.minimap is not None:
            self.minimap.refresh_full()

    def register(self):
        self.logger.info("Registering event listeners.")

        self.accept("ui.request.action.stage", self.request_action_stage)

        self.accept("ui.update.user.city_clicked", self.process_city_click)
        self.accept("ui.update.user.enemy_city_clicked", self.process_enemy_city_click)

        self.accept("ui.update.ui.unit_unselected", self.clear_action_bar)

        self.accept("game.era.progressing", self.open_age_popup)

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
        self.accept("ui.update.ui.layout_debug_changed", self.on_layout_debug_changed)

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
            self.city_ui.show(city)

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

    def process_turn(self):
        self.refresh_city()
        self.refresh_action_bar()

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

    def get_action_bar_frame(self) -> PlayerActionBar:
        if self.action_bar is None:
            raise AssertionError("Action bar is not initialized.")
        return self.action_bar

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
        if self.root_layout is not None and getattr(self.root_layout, "parent", None) is not None:
            return

        self.root_layout = FloatLayout(size_hint=(1, 1))

        action_bar_frame = self.build_action_bar()
        action_bar_wrapper = self._register_layout_debug_widget(
            "action_bar",
            action_bar_frame,
            default_position=(float(action_bar_frame.x), float(action_bar_frame.y)),
        )

        turn_control_frame = self.build_player_turn_control()
        turn_control_wrapper = self._register_layout_debug_widget(
            "turn_control",
            turn_control_frame,
            default_position=(float(turn_control_frame.x), float(turn_control_frame.y)),
        )

        self.root_layout.add_widget(action_bar_wrapper)  # type: ignore[arg-type]
        self.root_layout.add_widget(turn_control_wrapper)  # type: ignore[arg-type]

        if self.action_bar is None or self.player_turn_control is None:
            raise AssertionError("Action bar, debug panel, or stats panel, player_turn_control is not initialized.")

        self.logger.info("Game UI screen built.")
        self.logger.info("Registering non-collidable UI elements.")

        self.register_non_collidable(action_bar_wrapper)
        self.register_non_collidable(turn_control_wrapper)

        self.logger.info("Non-collidable UI elements registered.")
        self.add_widget(self.root_layout)
        self.apply_layout_debug_settings()

    def _window_size(self) -> tuple[float, float]:
        return (float(self._base.win.getXSize()), float(self._base.win.getYSize()))  # type: ignore[attr-defined]

    def _layout_debug_enabled(self) -> bool:
        return self.config_manager.get_debug_mode()

    def _layout_debug_drag_enabled(self) -> bool:
        return self._layout_debug_enabled() and self.config_manager.get_ui_layout_drag_enabled()

    def _layout_debug_overlay_enabled(self) -> bool:
        return self._layout_debug_enabled() and self.config_manager.get_ui_layout_overlay_enabled()

    def _should_apply_saved_layout_positions(self) -> bool:
        return self._layout_debug_drag_enabled() or self._layout_debug_overlay_enabled()

    @staticmethod
    def _coerce_layout_position(data: dict[str, float] | None) -> LayoutDebugPosition | None:
        if data is None:
            return None
        return LayoutDebugPosition(x=float(data.get("x", 0.0)), y=float(data.get("y", 0.0)))

    def _register_layout_debug_widget(
        self,
        item_id: str,
        content: Widget,
        default_position: tuple[float, float],
    ) -> DraggableLayoutWrapper:
        wrapper = self.layout_debug_widgets.get(item_id)
        if wrapper is None:
            wrapper = DraggableLayoutWrapper(
                base=self._base,
                item_id=item_id,
                content=content,
                on_drag_end=self._on_layout_debug_position_committed,
            )
            self.layout_debug_widgets[item_id] = wrapper
        else:
            wrapper.set_content(content)

        wrapper.set_default_position(default_position)
        stored_position = self._coerce_layout_position(self.config_manager.get_ui_layout_position(item_id))
        if not self._should_apply_saved_layout_positions() or stored_position is None:
            wrapper.reset_to_default_position()
        else:
            wrapper.apply_normalized_position(stored_position)

        wrapper.set_drag_enabled(self._layout_debug_drag_enabled())
        wrapper.set_overlay_enabled(self._layout_debug_overlay_enabled())
        return wrapper

    def _on_layout_debug_position_committed(self, item_id: str, position: tuple[float, float]) -> None:
        window_width, window_height = self._window_size()
        safe_width = max(window_width, 1.0)
        safe_height = max(window_height, 1.0)
        self.config_manager.set_ui_layout_position(item_id, position[0] / safe_width, position[1] / safe_height)
        self.update_ui_geometry_cache()

    def on_layout_debug_changed(self, reset_positions: bool = False) -> None:
        self.apply_layout_debug_settings(reset_positions=reset_positions)

    def apply_layout_debug_settings(self, reset_positions: bool = False) -> None:
        drag_enabled = self._layout_debug_drag_enabled()
        overlay_enabled = self._layout_debug_overlay_enabled()
        use_saved_positions = drag_enabled or overlay_enabled

        for item_id, wrapper in self.layout_debug_widgets.items():
            wrapper.set_drag_enabled(drag_enabled)
            wrapper.set_overlay_enabled(overlay_enabled)

            if reset_positions or not use_saved_positions:
                wrapper.reset_to_default_position()
                continue

            stored_position = self._coerce_layout_position(self.config_manager.get_ui_layout_position(item_id))
            if stored_position is None:
                wrapper.reset_to_default_position()
            else:
                wrapper.apply_normalized_position(stored_position)

        if self.minimap is not None:
            minimap_position = None if reset_positions or not use_saved_positions else self._coerce_layout_position(
                self.config_manager.get_ui_layout_position("minimap")
            )
            self.minimap.set_layout_debug_state(
                drag_enabled=drag_enabled,
                overlay_enabled=overlay_enabled,
                position=minimap_position,
                reset_position=reset_positions or not use_saved_positions,
            )

        self.update_ui_geometry_cache()

    def bring_to_front(self, widget: Widget):
        parent: Widget | None = widget.parent
        if parent is not None and widget in parent.children:
            parent.remove_widget(widget)
            parent.add_widget(widget)
        elif widget in self.children:
            self.remove_widget(widget)
            self.add_widget(widget)

    def send_to_back(self, widget: Widget):
        parent: Widget | None = widget.parent
        if parent is not None and widget in parent.children:
            parent.remove_widget(widget)
            parent.add_widget(widget, len(parent.children) - 1)
        elif widget in self.children:
            self.remove_widget(widget)
            self.add_widget(widget, index=len(self.children) - 1)

    def build_inspect_entity(self) -> InspectEntity:
        self.inspect = InspectEntity(self)
        return self.inspect

    def build_action_bar(self) -> GridLayout:
        self.action_bar = PlayerActionBar(self._base)
        return self.action_bar.build()

    def build_stats_frame(self) -> FloatLayout:
        self.stats_frame = StatsPanel(base=self._base)
        frame = self.stats_frame.build()
        window_width, window_height = self._window_size()
        default_position = (window_width - float(frame.width), window_height * 0.975 - float(frame.height))
        return self._register_layout_debug_widget("stats_panel", frame, default_position)

    def build_debug_frame(self) -> FloatLayout:
        self.debug_frame = DebugPanel(base=self._base)
        frame = self.debug_frame.build_debug_frame()
        window_width, window_height = self._window_size()
        default_position = (window_width - float(frame.width), window_height * 0.975 - float(frame.height))
        return self._register_layout_debug_widget("debug_panel", frame, default_position)

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

    def build_minimap(self) -> Minimap:
        if self.minimap is None:
            self.minimap = Minimap(base=self._base)
        self.minimap.set_layout_debug_callback(self._on_layout_debug_position_committed)
        self.minimap.register()
        return self.minimap

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
        old_wrapper = self.layout_debug_widgets.pop("player_list", None)
        if old_wrapper is not None:
            self.unregister_non_collidable(old_wrapper)
            old_parent = getattr(old_wrapper, "parent", None)
            if old_parent is not None:
                old_parent.remove_widget(old_wrapper)

        self.player_list = PlayerList(base=self._base)
        self.player_list.build()
        self.add_widget(self.player_list)
        self.register_non_collidable(self.player_list)
        return self.player_list

    def build_player_info(self) -> PlayerInfo:
        self.player_info = PlayerInfo()
        self.player_info.build()
        self.add_widget(self.player_info)
        return self.player_info

    def build_combat_log(self) -> PlayerCombatLog:
        combat_log = CombatLog()
        logs: List[CombatLogEntry] = combat_log.get_entries(PlayerManager.session_player())
        self.player_combat_log = PlayerCombatLog(log=logs, base=self._base)
        self.player_combat_log.build()
        self.player_combat_log.update()
        wrapper = self._register_layout_debug_widget(
            "combat_log",
            self.player_combat_log,
            default_position=(float(self.player_combat_log.x), float(self.player_combat_log.y)),
        )
        self.add_widget(wrapper)
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

    def refresh_minimap_overlay(self) -> None:
        if self.minimap is not None:
            self.minimap.schedule_overlay_refresh()

    def clear_selected_unit(self):
        self.clear_action_bar()
        self.ui_manager.clear_selected_unit()
        self.close_target_panel()

    def clear_selected_tile(self):
        self.ui_manager.clear_selected_tile()
        self.close_city_ui()
        self.refresh_minimap_overlay()

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

        debug_wrapper = self.layout_debug_widgets.get("debug_panel")
        stats_wrapper = self.layout_debug_widgets.get("stats_panel")

        if debug and debug_wrapper is not None and not self.debug_panels_showing_state["debug"]:
            self.add_widget(debug_wrapper)
            self.register_non_collidable(debug_wrapper)
            self.debug_panels_showing_state["debug"] = True
        elif not debug and debug_wrapper is not None:
            if getattr(debug_wrapper, "parent", None) is not None:
                self.remove_widget(debug_wrapper)
            self.unregister_non_collidable(debug_wrapper)
            self.debug_panels_showing_state["debug"] = False

        if stats and stats_wrapper is not None and not self.debug_panels_showing_state["stats"]:
            self.add_widget(stats_wrapper)
            self.register_non_collidable(stats_wrapper)
            self.debug_panels_showing_state["stats"] = True
        elif not stats and stats_wrapper is not None:
            if getattr(stats_wrapper, "parent", None) is not None:
                self.remove_widget(stats_wrapper)
            self.unregister_non_collidable(stats_wrapper)
            self.debug_panels_showing_state["stats"] = False

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

        if self.wait_for_next_input_of_user is False:
            self.clear_selected_unit()

        generate_buttons: bool = True
        if self.wait_for_next_input_of_user and self.wait_for_action_of_user is not None:
            self.run_prepared_action(tile=tile)  # type: ignore
            self.wait_for_action_of_user = None
            self.wait_for_next_input_of_user = False

            if self.wait_for_action is not None and self.wait_for_action.keep_targeting_after_use is False:
                if self.ui_manager.select_tile(_tile):
                    tile_change = True
            else:
                generate_buttons = False

            self.wait_for_action_of_user = None
            self.action_waiting_for = None

        else:
            self.open_target_panel(_tile)
            self.ui_manager.select_tile(_tile)
            tile_change = True

        if (unit := self.ui_manager.current_unit) is not None and generate_buttons is True:
            self.generate_buttons_for_unit_actions(unit)  # Update

        if tile_change:
            self.refresh_minimap_overlay()

        return tile_change

    def process_unit_click(self, unit: Optional[Union[str, "Tile"]] = None) -> bool:
        self.logger.debug(f"Unit clicked: {unit}")
        if isinstance(unit, str):
            _unit: Optional[BaseEntity] = cast(
                Optional[BaseEntity], EntityManager.get_singleton_instance().get(EntityType.UNIT, unit)
            )
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
            self.action_waiting_for = None

        if should_select_unit is True and _unit.is_alive():
            self.ui_manager.select_unit(_unit)  # type: ignore # We know it exists but because its a weak reference, mypy doesn't know it exists
            self.open_target_panel(_unit)
            self.refresh_minimap_overlay()
        else:
            self.close_target_panel()

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

        self.generate_buttons_for_unit_actions(self.ui_manager.current_unit)

    def generate_buttons_for_unit_actions(self, unit: str | BaseEntity):
        _unit: Optional[Unit] = None
        if isinstance(unit, str):
            _unit: Optional[Unit] = self.unit_manager.find_unit(unit)
        else:
            _unit: Optional[Unit] = unit if isinstance(unit, Unit) else None

        if _unit is not None:
            if self.action_bar is None:
                raise AssertionError("Action bar frame is not initialized.")

            self.action_bar.generate(
                unit=_unit,
                action_preparer=self.prepare_action,
                build_action_preparer=self.prepare_build_action,
                current_action=self.wait_for_action_of_user,
            )

    def update_ui_elements(self):
        self.refresh_action_bar()
        self.refresh_targeting_ui()
        self.refresh_combat_log()

    def refresh_combat_log(self):
        if self.player_combat_log is not None:
            self.player_combat_log.update()

    def refresh_targeting_ui(self):
        if self.player_attack_info is not None:
            self.player_attack_info.update()
        if self.player_target_info is not None:
            self.player_target_info.update()

    def clear_action_bar(self):
        if self.action_bar is None:
            return
        self.action_bar.clear_buttons()

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

    def open_target_panel(self, entity: Unit | Tile):
        if self.player_target_info is None:
            self.player_target_info = TargetPanel()
            self.add_widget(self.player_target_info)
            self.send_to_back(self.player_target_info)
        self.player_target_info.show_for(entity)

    def close_target_panel(self):
        if self.player_target_info is not None:
            self.remove_widget(self.player_target_info)
            self.player_target_info = None

    def open_age_popup(self, age_name: "str | Age", *args: Any, **kwargs: Any):
        if isinstance(age_name, str):
            age: Age = AgesManager.get_singleton_instance().get_age(age_name)
        else:
            age: Age = age_name
        if self.age_popup is not None:
            self.age_popup.dismiss()
            self.age_popup = None

        self.age_popup = ModalImagePopup(
            title=f"{age.get_name()} Age Reached!",
            message=f"You have entered the {age.get_name()} era.",
            image_source=age.get_transition_image(),
            size_hint=(0.5, 0.5),
        )
        self.age_popup.open()

    def close_age_popup(self):
        if self.age_popup is not None:
            self.age_popup.dismiss()
            self.age_popup = None

    def open_log(self):
        self.log.open()
        self.lock_input()

    def close_log(self):
        self.unregister_non_collidable(self.log)
        self.log.done()
        self.unlock_input()

    def open_city_ui(self, city: City):
        self.close_city_ui()
        self.city_ui = CityUI(
            screen=self,
            base=self._base,
            name="",
        )

        assert self.city_ui is not None, "City UI is not initialized."
        assert self.root_layout is not None, "Root layout is not initialized."

        self.city_ui.show(city)
        self.root_layout.add_widget(self.city_ui)

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
            debug_actions_wrapper = self._register_layout_debug_widget(
                "debug_actions",
                self.debug_actions.frame,
                default_position=(float(self.debug_actions.frame.x), float(self.debug_actions.frame.y)),
            )
            self.register_non_collidable(debug_actions_wrapper)
            assert self.root_layout is not None, "Root layout is not initialized."
            self.root_layout.add_widget(debug_actions_wrapper)  # type: ignore[arg-type]
            self.apply_layout_debug_settings()
        self.lock_input()

    def close_debug_actions(self):
        if self.debug_actions is not None:
            debug_actions_wrapper = self.layout_debug_widgets.get("debug_actions")
            if debug_actions_wrapper is not None:
                self.unregister_non_collidable(debug_actions_wrapper)
            assert self.root_layout is not None, "Root layout is not initialized."
            self.debug_actions.hide()
            if debug_actions_wrapper is not None and getattr(debug_actions_wrapper, "parent", None) is self.root_layout:
                self.root_layout.remove_widget(debug_actions_wrapper)  # type: ignore[arg-type]
            self.popup_disabled = True
            self.debug_actions = None
        self.unlock_input()

    def open_inspect(self):
        if self.inspect is None:
            self.inspect = self.build_inspect_entity()
            self.inspect.show()
            inspect_wrapper = self._register_layout_debug_widget(
                "inspect_panel",
                self.inspect.frame,
                default_position=(float(self.inspect.frame.x), float(self.inspect.frame.y)),
            )
            self.register_non_collidable(inspect_wrapper)
            assert self.root_layout is not None, "Root layout is not initialized."
            self.root_layout.add_widget(inspect_wrapper)  # type: ignore[arg-type]
            self.apply_layout_debug_settings()
        self.lock_input()

    def close_inspect(self):
        if self.inspect is not None:
            inspect_wrapper = self.layout_debug_widgets.get("inspect_panel")
            if inspect_wrapper is not None:
                self.unregister_non_collidable(inspect_wrapper)
            assert self.root_layout is not None, "Root layout is not initialized."
            self.inspect.hide()
            if inspect_wrapper is not None and getattr(inspect_wrapper, "parent", None) is self.root_layout:
                self.root_layout.remove_widget(inspect_wrapper)  # type: ignore[arg-type]
            self.popup_disabled = True
            self.inspect = None
        self.unlock_input()

    def close_before_fullscreen(self):
        if self.player_target_info:
            self.close_target_panel()

    def open_research(self):
        if self.research is None:
            self.close_before_fullscreen()

            self.research = self.build_research()
            self.register_non_collidable(self.research)
            assert self.root_layout is not None, "Root layout is not initialized."
            self.root_layout.add_widget(self.research)
        self.lock_input()

    def open_civics(self):
        if self.civics is None:
            self.close_before_fullscreen()

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
            self.research.destroy()
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
        if self.minimap is not None:
            self.unregister_non_collidable(self.minimap)
            if getattr(self.minimap, "parent", None) is not None:
                self.remove_widget(self.minimap)
            self.minimap.destroy()
            self.minimap = None
        self.unregister()
        self.clear_action_bar()
        self.clear_selected_unit()
        self.ignore_all()

    def toggle_tile_yield_icons(self) -> None:
        self.set_tile_yield_icons(not self.showing_tile_yield_icons)
        self.showing_tile_yield_icons = not self.showing_tile_yield_icons

    def set_tile_yield_icons(self, show: bool) -> None:
        from gameplay.repositories.tile import TileRepository

        if self.showing_tile_yield_icons == show:
            return

        for tile in TileRepository.get_tiles():
            if show:
                tile.disable_icons()
            else:
                tile.enable_icons()

            tile.render()
