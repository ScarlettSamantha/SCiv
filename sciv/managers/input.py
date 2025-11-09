import time
from enum import Enum
from logging import Logger
from typing import TYPE_CHECKING, Any, List, Literal, Optional

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
    Vec3,
    WindowProperties,
)

if TYPE_CHECKING:
    from game import OpenCiv
    from gameplay.tile import Tile
    from gameplay.unit import Unit
    from managers.game import Game
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
        self._last_right_click_time: float = 0.0
        self._last_right_release_time: float = 0.0
        self._right_button_held: bool = False
        self.pick_timeout: float = 1 / 15
        self.long_press_time: float = 0.5
        self.ranged_targeting: RangedTargeting | None = None
        self.game_ui: "GameUIScreen | None" = None
        self.unit_manager: "UnitManager | None" = None
        self._long_press_task_name: Optional[str] = None
        self.game: "Game | None" = None
        self.unit_manager: UnitManager | None = None

        self.long_right_click: bool | None = None

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
        self.accept("mouse3-up", self.on_right_click)
        self.accept("mouse3", self.on_right_down)

        if Debug.is_debug():
            self.accept("f2", self.activate)
            self.accept("f3", self.de_activate)

            self.accept("f5", self.toggle_tile_yield_icons)
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

    def on_right_down(self):
        if self._right_button_held or self.game_ui is None:
            return

        self._right_button_held = True
        self._last_right_click_time = time.time()
        clicked_object: NodePath | None = self.pick_object(dont_select=True)
        self.long_right_click = False
        tile: Optional["Tile"] = None
        if clicked_object and clicked_object.getNetTag(NET_TYPE_FIELD) == NET_TYPE.TILE.value:
            if self.selected_unit is None:
                return

            target: str = clicked_object.getNetTag(NET_NODE_TAG_ID_FIELD)
            if (tile := TileRepository.get_tile(*map(lambda s: int(s), target.split("_")[-2:]))) is None:
                self.logger.warning(f"Tile with ID {target} not found.")
                return

        if clicked_object and clicked_object.getNetTag(NET_TYPE_FIELD) == NET_TYPE.BIT.value:
            node_tag = clicked_object.getNetTag(NET_NODE_TAG_ID_FIELD)
            tile_cords: List[str] = node_tag.split("_")[:2]
            if (tile := TileRepository.get_tile(*map(lambda s: int(s), tile_cords))) is None:
                self.logger.warning(f"Tile with ID {node_tag} not found.")
                return

        if self.game_ui.wait_for_action is None and tile is not None and self.selected_unit is not None:
            self.game_ui.open_unit_path_renderer(self.selected_unit, tile)

        self._long_press_task_name = "input-long-right-click"
        self.base.taskMgr.doMethodLater(
            self.long_press_time,
            self._check_long_right_click,
            self._long_press_task_name,
        )

    def toggle_tile_yield_icons(self):
        if self.game_ui is None:
            self.game_ui = self.base.ui_manager.get_main_game_ui()
        self.game_ui.toggle_tile_yield_icons()

    def _check_long_right_click(self, task: Task.Task) -> int:
        if self.base.mouseWatcherNode.isButtonDown("mouse3"):  # type: ignore
            self.long_right_click = True
            self.on_long_right_click()
        else:
            self.long_right_click = False
        return Task.done

    def on_long_right_click(self) -> None:
        if self._last_right_release_time > self._last_right_click_time:
            return  # Ignore if the button was released before the long click was registered.

        MessengerGlobal.messenger.send("mouse3-down-long")

        assert self.game_ui is not None, "Game UI should be initialized."

        target: NodePath | None = self.pick_object(dont_select=True)
        if target is None:
            return

        net_type: str = target.getNetTag(NET_TYPE_FIELD)  # type: ignore
        net_id = target.getNetTag(NET_NODE_TAG_ID_FIELD)

        if NET_TYPE.UNIT.value == net_type:
            if (
                (unit := UnitManager.get_singleton_instance().find_unit(net_id)) is not None
                and self.selected_unit is not None
                and self.game_ui.action_waiting_for is None
            ):
                self.game_ui.open_player_attack_info(self.selected_unit, unit)

    def is_long_right_click(self) -> bool:
        return self.long_right_click is True

    def on_right_click(self):
        from gameplay.unit import CantMoveReason

        self._last_right_release_time = time.time()
        self._right_button_held = False

        if self._long_press_task_name:
            self.base.taskMgr.remove(self._long_press_task_name)
            self._long_press_task_name = None

        messenger.send("ui.update.ui.close_player_attack_info")

        if self.game_ui is None:
            return

        self.cancel_user_action()

        clicked_object: NodePath | None = self.pick_object(dont_select=True)
        if clicked_object is None:
            self.game_ui.close_unit_path_renderer()
            return

        net_type: str = clicked_object.getNetTag(NET_TYPE_FIELD)  # type: ignore
        net_id = clicked_object.getNetTag(NET_NODE_TAG_ID_FIELD)

        if self.selected_unit is None:
            self.game_ui.close_unit_path_renderer()
            return

        if net_type in (NET_TYPE.TILE.value, NET_TYPE.BIT.value, NET_TYPE.GEOM.value):
            if NET_TYPE.BIT.value == net_type:
                _net_id: List[str] = net_id.split("_")[:2]  # type: ignore
            else:
                _net_id = net_id.split("_")[-2:]  # type: ignore

            if not self.is_long_right_click():
                tile: "Tile | None" = TileRepository.get_tile(*map(lambda s: int(s), _net_id))
                if tile is None:
                    self.logger.warning(f"Tile with ID {_net_id} not found.")
                else:
                    if (
                        self.game_ui.wait_for_next_input_of_user is False
                        and self.game_ui.wait_for_action_of_user is None
                        and self.selected_unit.can_move_to_tile(tile, get_tiles=False) == CantMoveReason.COULD_MOVE
                    ):
                        self.move_selected_unit_to_tile(tile)

        self.game_ui.close_unit_path_renderer()
        self.game_ui.refresh_action_bar()

    def move_selected_unit_to_tile(self, tile: "Tile") -> None:
        from gameplay.unit import CantMoveReason

        if self.selected_unit is None:
            self.logger.warning("No unit selected to move.")
            return

        if self.selected_unit.can_move_to_tile(tile=tile, get_tiles=False) != CantMoveReason.COULD_MOVE:
            self.logger.warning(f"Selected unit cannot move to tile {tile.tag}.")
            return

        self.selected_unit.move(tile)

    def cancel_user_action(self):
        if self.game_ui is None:
            self.game_ui = self.base.ui_manager.get_main_game_ui()

        assert self.game_ui is not None, "Game UI should be initialized."

        if self.game_ui.wait_for_action_of_user is not None:
            self.game_ui.wait_for_action_of_user.cancel()
            self.game_ui.wait_for_action_of_user = None
            self.unhover_all()
            messenger.send("ui.update.ui.close_player_attack_info")
        self.game_ui.waiting_for_world_input = False
        self.game_ui.wait_for_next_input_of_user = False

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

    def setup(self, base: "OpenCiv", *args: Any, **kwargs: Any) -> None:
        from managers.world import World

        self.base = base
        self.map = World.get_singleton_instance()
        self.unit_manager = UnitManager.get_singleton_instance()

    def inject_into_camera(self) -> None:
        self._pick_mask = BitMask32.bit(1)
        self.picker = CollisionTraverser()
        self.pq = CollisionHandlerQueue()

        picker_node = CollisionNode("inputSystemMouseRayCollisionNode")
        self.pickerRay = CollisionRay()
        picker_node.addSolid(self.pickerRay)  # type: ignore
        picker_node.setFromCollideMask(self._pick_mask)  # type: ignore

        self.pickerNP: NodePath[CollisionNode] = self.base.camera.attachNewNode(picker_node)  # type: ignore
        self.picker.addCollider(self.pickerNP, self.pq)  # type: ignore

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

    def hide_targeting(self):
        if self.ranged_targeting is None:
            return
        self.ranged_targeting.hide()
        self.ranged_targeting.destroy()
        self.ranged_targeting = None
        MessengerGlobal.messenger.send("ui.update.ui.close_player_attack_info")

    def hover_task(self, task: Task.Task) -> Literal[1]:
        if not self.active or not self.base.mouseWatcherNode.hasMouse():  # type: ignore
            return task.cont

        if self._hover_frame_skip > 0:
            self._hover_frame_skip -= 1
            return task.cont

        if self.game_ui is None:
            self.game_ui = self.base.ui_manager.get_main_game_ui()

        if self.unit_manager is None:
            self.unit_manager = UnitManager.get_singleton_instance()

        assert self.game_ui is not None, "Game UI should be initialized."

        mpos = self.base.mouseWatcherNode.getMouse()  # type: ignore
        current_pos = (mpos.getX(), mpos.getY())  # type: ignore
        if self._last_mouse_pos is not None and all(
            abs(self._last_mouse_pos[i] - current_pos[i]) < 0.001 for i in range(2)
        ):
            return task.cont  # mouse didn't move significantly

        self._last_mouse_pos = current_pos
        self.pq.clearEntries()
        self.pickerRay.setFromLens(self.base.camNode, *current_pos)  # type: ignore
        self.picker.traverse(self.base.render)  # type: ignore

        if self.pq.getNumEntries() > 0:
            self.pq.sortEntries()
            for entry in self.pq.getEntries():
                picked_obj: NodePath = entry.getIntoNodePath()  # type: ignore
                net_type: str = picked_obj.getNetTag(NET_TYPE_FIELD)  # type: ignore
                net_id = picked_obj.getNetTag(NET_NODE_TAG_ID_FIELD)

                if NET_TYPE.TILE.value == net_type:
                    self.unhover_all()
                    messenger.send("system.input.user.tile_hovered", [net_id])
                    self.hovered_tile_id = net_id

                    tile: "Tile | None" = TileRepository.get_tile(*map(lambda s: int(s), net_id.split("_")[-2:]))

                    if tile is None:
                        self.logger.warning(f"Tile with ID {net_id} not found.")
                        return task.cont

                    if (
                        self.game_ui.unit_path_renderer is not None
                        and self.game_ui.unit_path_renderer.is_visible()
                        and self.game_ui.unit_path_renderer.target_tile is not None
                        and self.game_ui.unit_path_renderer.target_tile is not tile
                        and self.game_ui.unit_path_renderer.source_tile is not None
                    ):
                        tiles: List["Tile"] | None = TileRepository.astar(
                            self.game_ui.unit_path_renderer.source_tile, tile, 1.0
                        )

                        if tiles is None:
                            self.game_ui.unit_path_renderer.hide()
                            return task.cont

                        path: List[Vec3] = TileRepository.tile_list_to_vec3(tiles)
                        self.game_ui.unit_path_renderer.set_path(path)

                if NET_TYPE.UNIT.value == net_type:
                    if self.hovered_unit_id == net_id:
                        break
                    self.unhover_all()
                    if (unit := self.unit_manager.find_unit(net_id)) is None:
                        self.logger.warning(f"Unit with ID {net_id} not found.")
                        return task.cont
                    if (
                        self.game_ui.wait_for_action_of_user
                        and self.game_ui.wait_for_action_of_user.targeting_unit_action
                    ):
                        if self.game_ui.wait_for_action_of_user.use_target_arrow and self.ranged_targeting is None:
                            self.ranged_targeting = RangedTargeting(parent=self.base.render)
                            executor: "Unit" = self.game_ui.wait_for_action_of_user.executor  # type: ignore

                            assert executor is not None, "Executor should not be None when using ranged targeting."

                            if executor.attack_range >= unit.get_distance_to(executor):
                                self.ranged_targeting.show(
                                    source=self.game_ui.wait_for_action_of_user.executor, target=unit
                                )
                                MessengerGlobal.messenger.send("ui.update.ui.open_player_attack_info", [executor, unit])

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
        self.hide_targeting()

    def run_analyze(self):
        self.base.render.analyze()  # type: ignore

    def pick_object(self, dont_select: bool = False) -> NodePath | None:
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
        self.pq.clearEntries()
        self.pickerRay.setFromLens(self.base.camNode, mpos.getX(), mpos.getY())  # type: ignore
        self.picker.traverse(self.base.render)  # type: ignore
        assert self.game is not None, "Game instance should be initialized."
        assert self.unit_manager is not None, "UnitManager instance should be initialized."

        if self.pq.getNumEntries() > 0:  # type: ignore
            self.pq.sortEntries()  # type: ignore

            for entry in self.pq.getEntries():
                picked_obj: NodePath = entry.getIntoNodePath()  # type: ignore
                net_type: str = picked_obj.getNetTag(NET_TYPE_FIELD)  # type: ignore
                net_id = picked_obj.getNetTag(NET_NODE_TAG_ID_FIELD)

                if dont_select:
                    return picked_obj

                selected_object = False
                if net_type in (NET_TYPE.MODEL.value, NET_TYPE.UNIT.value):
                    if (unit := self.unit_manager.find_unit(net_id)) is None:
                        self.logger.warning(f"Unit with ID {net_id} not found.")
                        return None
                    messenger.send("system.input.user.unit_clicked", [net_id])
                    if self.game.handle_unit_click(unit):
                        selected_object = True
                        self.selected_tile = None
                        self.selected_unit = unit
                    else:
                        return None

                elif net_type in (NET_TYPE.TILE.value, NET_TYPE.BIT.value, NET_TYPE.GEOM.value):
                    if NET_TYPE.BIT.value == net_type:
                        net_id = net_id.split("_")[:2]
                    else:
                        net_id = net_id.split("_")[-2:]
                    if (tile := TileRepository.get_tile(*map(lambda s: int(s), net_id))) is None:
                        self.logger.warning(f"Tile with ID {net_id} not found.")
                        return None

                    self.game.handle_tile_click(tile)
                    self.selected_tile = tile
                    if not self.is_long_right_click():
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
