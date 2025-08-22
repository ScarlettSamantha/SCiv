import time
from enum import Enum
from logging import Logger
from typing import TYPE_CHECKING, Any, Literal, Optional

from direct.interval.IntervalGlobal import Func, Sequence, Wait
from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from direct.showbase.MessengerGlobal import messenger
from direct.task import Task
from gameplay.ranged_targeting import RangedTargeting
from gameplay.repositories.tile import TileRepository
from helpers.debug import Debug
from helpers.optimizations import throttle
from managers.unit import UnitManager
from mixins.singleton import Singleton
from panda3d.core import (
    BitMask32,
    CollisionHandlerQueue,
    CollisionNode,
    CollisionRay,
    CollisionTraverser,
    NodePath,
    WindowProperties,
)

if TYPE_CHECKING:
    from game import OpenCiv
    from gameplay.tile import Tile
    from gameplay.unit import Unit
    from menus.screens.game_ui import GameUIScreen

NET_NODE_TAG_ID_FIELD: str = "net_node_tag_id"  # tag for the node path to identify it as a net node
NET_TYPE_FIELD: str = "net_type"  # tag for the node path to identify it as a net node


class NET_TYPE(Enum):
    MODEL = "model"
    TILE = "tile"
    IMPROVEMENT = "improvement"
    RESOURCE = "resource"
    BIT = "bit"
    GEOM = "geom"
    ANCHOR = "anchor"
    UNIT = "unit"


class Input(Singleton, DirectObject):
    def __init__(self, base: "OpenCiv"):
        super().__init__()
        self.base: "OpenCiv" = base
        self.active: bool = False
        self.sequence: Optional[Sequence] = None

        self.logger: Logger = self.base.logger.engine.getChild("manager.input")

        self.hovered_tile_id: Optional[str] = None
        self.hovered_unit_id: Optional[str] = None
        self.selected_tile: Optional["Tile"] = None
        self.selected_unit: Optional["Unit"] = None
        self._last_pick_time: float = 0.0
        self.pick_timeout: float = 1 / 15
        self.ranged_targeting: RangedTargeting | None = None

        self._last_mouse_pos: Optional[tuple[float, float]] = None
        self._hover_frame_skip = 10  # how many frames to skip before checking for hover

        self.register()

        if self.base.config_manager.get_mouse_lock():
            self.activate_mouse_lock()
        else:
            self.de_activate_mouse_lock()

    def activate_mouse_lock(self):
        props = WindowProperties()
        props.setMouseMode(WindowProperties.M_confined)
        self.base.window().requestProperties(props)

    def de_activate_mouse_lock(self):
        props = WindowProperties()
        props.setMouseMode(WindowProperties.M_relative)
        self.base.window().requestProperties(props)

    def reset(self):
        self.active = False

    def register(self):
        self.accept("mouse1", self.pick_object)

        if Debug.is_debug():
            self.accept("f2", self.activate)
            self.accept("f3", self.de_activate)

            self.accept("f6", self.on_trigger_sentry_message)
            self.accept("f7", self.on_toggle_log)
            self.accept("f8", self.on_debug_actions_toggle)
            self.accept("f9", self.force_render_selected_entity)
            self.accept("f10", self.on_inspect_entity)
            self.accept("f11", self.on_inspect_players)
            self.accept("f12", self.inspect_element)

        self.accept("escape", self.on_escape)
        self.accept("space", self.on_space)

        self.accept("system.input.raycaster_on", self.activate)
        self.accept("system.input.raycaster_off", self.de_activate)
        self.accept("system.input.raycaster_on_delay", self.delay_activate)
        self.base.taskMgr.add(self.hover_task, "input-hover-task", delay=1)  # type: ignore

    def on_trigger_sentry_message(self):
        from helpers.debug import Debug

        if not Debug.is_debug():
            self.logger.warning("Debug mode is not enabled. Cannot trigger sentry message.")
            return

        Debug.trigger_sentry_dump()

    def on_toggle_log(self):
        self.base.ui_manager.get_main_game_ui().toggle_log()

    def on_debug_actions_toggle(self):
        from menus.screens.game_ui import GameUIScreen

        screen: GameUIScreen = self.base.ui_manager.get_main_game_ui()
        if screen.debug_actions is not None and screen.debug_actions.is_open:
            screen.close_debug_actions()
        else:
            screen.open_debug_actions()

    def force_render_selected_entity(self) -> None:
        if self.selected_tile is None and self.selected_unit is None:
            self.logger.warning("No selected tile/unit to render.")
            return

        selected_entity = self.selected_tile if self.selected_tile else None

        if selected_entity is not None and hasattr(selected_entity, "tag"):
            self.logger.info(f"Rendering selected entity: {selected_entity.tag}")
            selected_entity.render()  # type: ignore

    def inspect_element(self, element: Optional[NodePath] = None) -> None:
        from direct.tkpanels.Inspector import inspect

        if element is None:
            if self.selected_tile is not None:
                element = self.selected_tile.get_node()
            else:
                self.logger.warning("No element to inspect. Please select a tile or unit.")
                return
        inspect(element)

    def delay_activate(self, delay: int | float):
        self.sequence = Sequence(Wait(delay), Func(self.activate))  # type: ignore
        self.sequence.start()

    @throttle(0.25)
    def de_activate(self):
        self.logger.info("Deactivating input raycaster.")
        self.active = False

    @throttle(0.25)
    def activate(self):
        self.logger.info("Activating input raycaster.")
        self.active = True

    def __setup__(self, base: "OpenCiv", *args: Any, **kwargs: Any) -> None:
        from managers.world import World

        self.base = base
        self.map = World.get_singleton_instance()

        return super().__setup__(*args, **kwargs)

    def inject_into_camera(self):
        self.picker = CollisionTraverser()
        self.pq = CollisionHandlerQueue()

        picker_node = CollisionNode("inputSystemMouseRayCollisionNode")
        self.pickerRay = CollisionRay()
        picker_node.addSolid(self.pickerRay)  # type: ignore

        picker_node.setFromCollideMask(BitMask32.bit(1))  # type: ignore

        self.pickerNP: NodePath[CollisionNode] = self.base.camera.attachNewNode(picker_node)  # type: ignore
        self.picker.addCollider(self.pickerNP, self.pq)  # type: ignore
        self.register()  # Ensures key bindings are set

    def on_inspect_entity(self) -> None:
        if self.selected_tile is None and self.selected_unit is None:
            self.logger.warning("No selected tile/unit to inspect.")
            return

        selected_entity: "Tile | Unit | None" = self.selected_tile if self.selected_tile else self.selected_unit

        if selected_entity is not None and hasattr(selected_entity, "tag"):
            self.logger.info(f"Inspecting selected entity: {selected_entity.tag}")

        self.base.ui_manager.inspect_element(selected_entity)  # type: ignore

    def on_inspect_players(self) -> None:
        from managers.player import PlayerManager
        from menus.kivy.parts.inspect_entity import PlayersWrapper

        players_wrapper: PlayersWrapper = PlayersWrapper(list(PlayerManager.all(add_mechanic_players=True).values()))

        self.base.ui_manager.inspect_element(players_wrapper)

    def hover_task(self, task: Task.Task) -> Literal[1]:
        if not self.active or not self.base.mouseWatcherNode.hasMouse():  # type: ignore
            return task.cont

        game_ui: "GameUIScreen" = self.base.ui_manager.get_main_game_ui()
        mpos = self.base.mouseWatcherNode.getMouse()  # type: ignore
        current_pos = (mpos.getX(), mpos.getY())  # type: ignore

        if self._last_mouse_pos == current_pos:
            return task.cont  # mouse didn't move

        self._last_mouse_pos = current_pos

        self.pickerRay.setFromLens(self.base.camNode, *current_pos)  # type: ignore
        self.picker.traverse(self.base.render)  # type: ignore

        if self.pq.getNumEntries() > 0:
            self.pq.sortEntries()
            for entry in self.pq.getEntries():
                picked_obj: NodePath = entry.getIntoNodePath()  # type: ignore
                net_type: str = picked_obj.getNetTag(NET_TYPE_FIELD)  # type: ignore
                net_id = picked_obj.getNetTag(NET_NODE_TAG_ID_FIELD)

                if NET_TYPE.TILE.value == net_type:
                    if self.ranged_targeting is not None:
                        self.ranged_targeting.hide()
                    self.unhover_all()
                    messenger.send("system.input.user.tile_hovered", [net_id])
                    self.hovered_tile_id = net_id
                if NET_TYPE.UNIT.value == net_type:
                    if self.ranged_targeting is not None:
                        self.ranged_targeting.hide()
                    self.unhover_all()
                    if (unit := UnitManager.get_singleton_instance().find_unit(net_id)) is None:
                        self.logger.warning(f"Unit with ID {net_id} not found.")
                        return task.cont
                    if game_ui.wait_for_action_of_user and game_ui.wait_for_action_of_user.targeting_unit_action:
                        if game_ui.wait_for_action_of_user.use_target_arrow:
                            self.ranged_targeting = RangedTargeting(parent=self.base.render)
                            executor: "Unit" = game_ui.wait_for_action_of_user.executor  # type: ignore

                            assert executor is not None, "Executor should not be None when using ranged targeting."

                            if executor.attack_range >= unit.get_distance_to(executor):
                                self.ranged_targeting.show(source=game_ui.wait_for_action_of_user.executor, target=unit)

                        unit.hover()
                        self.hovered_unit_id = net_id
                        break
        else:
            self.unhover_all()

        return task.cont

    def unhover_all(self) -> None:
        if self.hovered_tile_id is not None:
            messenger.send("system.input.user.tile_unhovered", [self.hovered_tile_id])
            self.hovered_tile_id = None
        if self.hovered_unit_id is not None:
            if (unit := UnitManager.get_singleton_instance().find_unit(self.hovered_unit_id)) is not None:
                unit.unhover()
                self.hovered_unit_id = None

    def run_analyze(self):
        self.base.render.analyze()  # type: ignore

    def pick_object(self) -> NodePath | None:
        from managers.game import Game

        now = time.time()
        if now - self._last_pick_time < self.pick_timeout:
            return None

        self._last_pick_time = now
        if not self.active:
            return  # Input is disabled

        if not self.base.mouseWatcherNode.hasMouse():  # type: ignore
            self.logger.warning("No mouse in window, cannot pick.")
            return

        mpos = self.base.mouseWatcherNode.getMouse()  # type: ignore
        self.pickerRay.setFromLens(self.base.camNode, mpos.getX(), mpos.getY())  # type: ignore
        self.picker.traverse(self.base.render)  # type: ignore

        if self.pq.getNumEntries() > 0:  # type: ignore
            self.pq.sortEntries()  # type: ignore

            for entry in self.pq.getEntries():
                picked_obj: NodePath = entry.getIntoNodePath()  # type: ignore
                net_type: str = picked_obj.getNetTag(NET_TYPE_FIELD)  # type: ignore
                net_id = picked_obj.getNetTag(NET_NODE_TAG_ID_FIELD)

                selected_object = False
                if net_type in (NET_TYPE.MODEL.value, NET_TYPE.UNIT.value):
                    if (unit := UnitManager.get_singleton_instance().find_unit(net_id)) is None:
                        self.logger.warning(f"Unit with ID {net_id} not found.")
                        return None
                    messenger.send("system.input.user.unit_clicked", [net_id])
                    if Game.get_singleton_instance().handle_unit_click(unit):
                        selected_object = True
                        self.selected_tile = None
                        self.selected_unit = unit
                    else:
                        return None

                elif NET_TYPE.TILE.value == net_type:
                    if (tile := TileRepository.get_tile(*map(lambda s: int(s), net_id.split("_")[-2:]))) is None:
                        self.logger.warning(f"Tile with ID {net_id} not found.")
                        return None

                    Game.get_singleton_instance().handle_tile_click(tile)
                    self.selected_tile = tile
                    self.selected_unit = None
                    selected_object = True
                    messenger.send("system.input.user.tile_clicked", [tile.tag])
                else:
                    self.selected_tile = None

                if selected_object:
                    return picked_obj  # type: ignore

            return None
        else:
            self.logger.debug("No object picked. Possibly between tiles or outside the game field.")
            return None

    def on_escape(self):
        messenger.send("game.input.user.escape_pressed")

    def on_space(self):
        MessengerGlobal.messenger.send("game.turn.request_end")
