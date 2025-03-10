from functools import partial
from logging import Logger
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional
from weakref import ReferenceType

from direct.showbase.MessengerGlobal import messenger
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from camera import CivCamera
from gameplay.city import City
from gameplay.tiles.base_tile import BaseTile
from gameplay.units.unit_base import UnitBaseClass
from managers.entity import EntityManager, EntityType
from managers.unit import Unit
from managers.world import World
from menus.kivy.mixins.collidable import CollisionPreventionMixin
from menus.kivy.parts.action_bar import ActionBar
from menus.kivy.parts.city import CityUI
from menus.kivy.parts.debug import DebugPanel
from menus.kivy.parts.debug_actions import DebugActions
from menus.kivy.parts.player_turn_control import PlayerTurnControl
from menus.kivy.parts.stats import StatsPanel
from system.actions import Action
from system.entity import BaseEntity

if TYPE_CHECKING:
    from main import Openciv


class GameUIScreen(Screen, CollisionPreventionMixin):
    debug_data: Dict[str, str] = {
        "state": "Playing",
    }

    def __init__(self, **kwargs: Any):
        if "base" not in kwargs:
            raise ValueError("GameUIScreen requires a 'base' keyword argument.")
        self._base: "Openciv" = kwargs.get("base", None)

        if self._base is None:
            raise AssertionError("Base is not initialized.")

        del kwargs["base"]
        from managers.ui import ui

        super().__init__(base=self._base, **kwargs)

        self.world_manager = World.get_instance()
        self.camera: CivCamera = CivCamera.get_instance()
        self.unit_manager: Unit = Unit.get_instance()
        self.ui_manager: ui = ui.get_instance()

        self.waiting_for_world_input: bool = False

        self.wait_for_next_input_of_user: bool = False
        self.wait_for_action_of_user: Optional[Callable] = None
        self.unit_waiting_for_action: Optional[UnitBaseClass] = None

        self.debug_panel: Optional[Label] = None
        self.camera_panel: Optional[Label] = None

        self.root_layout: Optional[FloatLayout] = None

        self.action_bar_frame: Optional[ActionBar] = None
        self.debug_frame: Optional[DebugPanel] = None
        self.stats_frame: Optional[StatsPanel] = None
        self.debug_actions: Optional[DebugActions] = None
        self.player_turn_control: Optional[PlayerTurnControl] = None
        self.city_ui: Optional[CityUI] = None
        self.logger: Logger = self._base.logger.graphics.getChild("ui.game_ui")

        self.showing_city: Optional[City] = None

        self.debug_panels_showing_state: Dict[str, bool] = {
            "stats": False,
            "actions": False,
            "debug": False,
        }

        self.logger.info("Game UI Screen initialized.")
        self.add_widget(self.build_screen())
        self.logger.info("Game UI Screen built.")
        self.register()

    def register(self):
        self.logger.info("Registering event listeners.")
        self._base.accept("ui.update.user.tile_clicked", self.process_tile_click)
        self._base.accept("ui.update.user.unit_clicked", self.process_unit_click)
        self._base.accept("ui.update.user.city_clicked", self.process_city_click)
        self._base.accept("ui.update.ui.unit_unselected", self.clear_action_bar)
        self._base.accept("system.unit.destroyed", self.clear_action_bar)
        self._base.accept("game.gameplay.unit.destroyed", self.on_unit_destroyed)
        self._base.accept("ui.update.user.enemey_city_clicked", self.process_enemy_city_click)

    def popup(self, name: str, header: str, text: str):
        messenger.send("ui.request.open.popup", [name, header, text])

    def on_unit_destroyed(self, unit: BaseEntity):
        self.clear_action_bar()

    def process_enemy_city_click(self, city: Any):
        self.popup("enemy_city_selected", "Enemy City", f"City: {city.name}\nOwner: {city.player.name}")

    def process_city_click(self, city: Any):
        if self.showing_city is None or city != self.showing_city:
            self.showing_city = city

            if self.city_ui is None or self.city_ui.city_label is None:
                raise AssertionError("City UI is not initialized.")

            self.city_ui.city_label.text = city.name
            self.get_city_ui().show()
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

    def build_screen(self):
        self.logger.info("Building game UI screen.")
        self.root_layout = FloatLayout(size_hint=(1, 1))

        self.root_layout.add_widget(self.build_action_bar())
        self.root_layout.add_widget(self.build_stats_frame())
        self.root_layout.add_widget(self.build_debug_frame())
        self.root_layout.add_widget(self.build_debug_actions())
        self.root_layout.add_widget(self.build_player_turn_control())
        self.root_layout.add_widget(self.build_city_ui())

        if (
            self.action_bar_frame is None
            or self.debug_frame is None
            or self.stats_frame is None
            or self.debug_actions is None
            or self.player_turn_control is None
            or self.city_ui is None
        ):
            raise AssertionError("Action bar, debug panel, or stats panel, player_turn_control is not initialized.")

        self.logger.info("Game UI screen built.")
        self.logger.info("Registering non-collidable UI elements.")

        self.register_non_collidable(self.action_bar_frame.frame)
        self.register_non_collidable(self.debug_frame.frame)
        self.register_non_collidable(self.stats_frame.frame)
        self.register_non_collidable(self.debug_actions.frame)
        self.register_non_collidable(self.player_turn_control.frame)
        self.register_non_collidable(self.city_ui.frame)

        self.logger.info("Non-collidable UI elements registered.")
        return self.root_layout

    def build_action_bar(self) -> BoxLayout:
        self.action_bar_frame = ActionBar(base=self._base)
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

    def build_player_turn_control(self) -> FloatLayout:
        self.player_turn_control = PlayerTurnControl(base=self._base)
        return self.player_turn_control.build_debug_frame()

    def build_city_ui(self) -> BoxLayout:
        self.city_ui = CityUI(base=self._base, name="City", background_color=(0, 0, 0, 1), border=(0, 0, 0, 1))
        result = self.city_ui.build()
        self.city_ui.hide()
        return result

    def toggle_debug_panels(self, debug: bool, stats: bool, actions: bool):
        if self.debug_actions is None or self.debug_frame is None or self.stats_frame is None:
            raise AssertionError("Debug actions, debug panel, or stats panel is not initialized.")

        self.get_debug_frame().get_frame().disabled = not debug
        self.get_debug_frame().get_frame().opacity = 0 if not debug else 1
        self.get_stats_frame().get_frame().disabled = not stats
        self.get_stats_frame().get_frame().opacity = 0 if not stats else 1

        if actions and not self.debug_panels_showing_state["actions"]:
            self.add_widget(self.debug_actions)
            self.register_non_collidable(self.debug_actions.frame)
        else:
            frame = self.get_action_bar_frame().get_frame()
            for child in frame.children:  # type: ignore
                frame.remove_widget(child)
            self.remove_widget(frame)
            self.remove_widget(self.debug_actions)
            self.unregister_non_collidable(self.debug_actions.frame)

        if debug and not self.debug_panels_showing_state["debug"]:
            self.add_widget(self.debug_frame)
            self._base.accept("ui.update.user.tile_clicked", self.process_tile_click)
            self._base.accept("ui.update.user.unit_clicked", self.process_unit_click)
            self.register_non_collidable(self.debug_frame.frame)
        else:
            frame = self.get_debug_frame()
            for child in frame.children:  # type: ignore
                frame.remove_widget(child)
            self.remove_widget(frame)
            self._base.ignore("ui.update.user.tile_clicked")
            self._base.ignore("ui.update.user.unit_clicked")
            self.unregister_non_collidable(self.debug_frame.frame)

        if stats and not self.debug_panels_showing_state["stats"]:
            frame = self.get_stats_frame().get_frame()
            self.add_widget(frame)
            self.register_non_collidable(self.stats_frame.frame)
        else:
            frame = self.get_stats_frame()
            frame.hide()
            self.register_non_collidable(self.stats_frame.frame)

    def process_tile_click(self, tile: str):
        _tile: Optional[BaseTile] = self.world_manager.lookup_on_tag(tile)

        if _tile is not None and _tile.city is None:
            self.get_city_ui().hide()
            self.showing_city = None

        self.clear_action_bar()

        if _tile is not None:
            self.debug_frame.update_debug_info("\n".join(f"{key}: {value}" for key, value in _tile.to_gui().items()))  # type: ignore # We know it exists because it's initialized in build_screen

            # If we are waiting for an action, execute it now
            if self.wait_for_next_input_of_user and self.wait_for_action_of_user:
                self.wait_for_action_of_user(_tile)  # Call the stored action with the tile
                self.wait_for_next_input_of_user = False
                self.wait_for_action_of_user = None  # Reset state

    def process_unit_click(self, unit: str):
        _unit: ReferenceType[BaseEntity] = EntityManager.get_instance().get_ref_weak(EntityType.UNIT, unit)

        if unit != self.ui_manager.current_unit:
            self.clear_action_bar()
            self.generate_buttons_for_unit_actions(unit)

        if self.showing_city is not None:
            self.get_city_ui().hide()
            self.showing_city = None

        if _unit is not None:
            self.debug_frame.update_debug_info("\n".join(f"{key}: {value}" for key, value in _unit().to_gui().items()))  # type: ignore # We know it exists because it's initialized in build_screen

    def generate_buttons_for_unit_actions(self, unit: str):
        if self.action_bar_frame is None:
            raise AssertionError("Action bar is not initialized.")

        _unit: Optional[UnitBaseClass] = self.unit_manager.find_unit(unit)
        if _unit is not None:
            self.action_bar_frame.clear_buttons()

            for action in _unit.get_actions():
                button = Button(
                    text=str(action.name),
                    size_hint=(None, None),
                    width=100,
                    height=75,
                )
                button.bind(on_press=partial(self.prepare_action, action, _unit))
                self.action_bar_frame.add_button(button)

    def clear_action_bar(self):
        if self.action_bar_frame is None:
            raise AssertionError("Action bar is not initialized.")

        self.action_bar_frame.clear_buttons()

    def prepare_action(self, action: Action, unit: UnitBaseClass, _instance):
        """Prepares an action and waits for the next tile click before executing."""
        if action.on_the_spot_action:
            action.action_kwargs["unit"] = unit
            action.run()
            if action.remove_actions_after_use:
                self.get_action_bar_frame().clear_widgets()
            return

        self.wait_for_next_input_of_user = True
        self.wait_for_action_of_user = partial(self.execute_action, action, unit)
        self.unit_waiting_for_action = unit
        self.waiting_for_world_input = True  # type: ignore # We know it exists because it's initialized in build_screen

    def execute_action(self, action: Action, unit: UnitBaseClass, tile: Optional[BaseTile]):
        """Executes the action after tile selection (if required)."""
        action.action_kwargs["unit"] = unit

        if tile is not None:
            action.action_kwargs["tile"] = tile  # Assign the selected tile

        if action.run() is False:
            self.debug_panel.text = "Action failed!"  # type: ignore # We know it exists because it's initialized in build_screen

        # Reset waiting state
        self.wait_for_next_input_of_user = False
        self.wait_for_action_of_user = None
        self.unit_waiting_for_action = None

        if action.remove_actions_after_use:
            self.clear_action_bar()
