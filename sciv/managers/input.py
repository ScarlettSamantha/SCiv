from enum import Enum
import time
from typing import TYPE_CHECKING, Any, Literal, Optional

from direct.interval.IntervalGlobal import Func, Sequence, Wait
from direct.showbase.DirectObject import DirectObject
from direct.showbase.MessengerGlobal import messenger
from direct.task import Task
from panda3d.core import (
    BitMask32,
    CollisionHandlerQueue,
    CollisionNode,
    CollisionRay,
    CollisionTraverser,
    NodePath,
)

from gameplay.repositories.tile import TileRepository
from managers.unit import UnitManager
from mixins.singleton import Singleton
from sciv.helpers.optimizations import throttle

if TYPE_CHECKING:
    from game import OpenCiv
    from gameplay.tile import Tile
    from gameplay.unit import Unit

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

        self.logger = self.base.logger.engine.getChild("manager.input")

        self.hovered_tile_id: Optional[str] = None
        self.selected_tile: Optional["Tile"] = None
        self.selected_unit: Optional["Unit"] = None
        self._last_pick_time: float = 0.0
        self.pick_timeout: float = 1 / 15

        self._last_mouse_pos: Optional[tuple[float, float]] = None
        self._hover_frame_skip = 10  # how many frames to skip before checking for hover

        self.register()

    def reset(self):
        self.active = False

    def register(self):
        # Left-click
        self.accept("mouse1", self.pick_object)
        self.accept("f7", self.run_analyze)

        self.accept("f2", self.activate)
        self.accept("f3", self.de_activate)

        self.accept("f9", self.force_render_selected_entity)
        self.accept("f12", self.inspect_element)

        # Escape key
        self.accept("escape", self.on_escape)

        self.accept("system.input.raycaster_on", self.activate)
        self.accept("system.input.raycaster_off", self.de_activate)
        self.accept("system.input.raycaster_on_delay", self.delay_activate)
        self.base.taskMgr.add(self.hover_task, "input-hover-task", delay=1)  # type: ignore

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

        picker_node = CollisionNode("mouseRay")
        self.pickerRay = CollisionRay()
        picker_node.addSolid(self.pickerRay)  # type: ignore

        picker_node.setFromCollideMask(BitMask32.bit(1))  # type: ignore

        self.pickerNP = self.base.camera.attachNewNode(picker_node)  # type: ignore
        self.picker.addCollider(self.pickerNP, self.pq)  # type: ignore
        self.register()  # Ensures key bindings are set

    def hover_task(self, task: Task.Task) -> Literal[1]:
        if not self.active or not self.base.mouseWatcherNode.hasMouse():  # type: ignore
            return task.cont

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

                selected_object = False
                if NET_TYPE.TILE.value == net_type:
                    # This is a tile
                    messenger.send("system.input.user.tile_hovered", [net_id])
                    selected_object = True

                if selected_object:
                    self.hovered_tile_id = net_id  # type: ignore
        else:
            if self.hovered_tile_id is not None:
                messenger.send("system.input.user.tile_unhovered", [self.hovered_tile_id])
                self.hovered_tile_id = None

        return task.cont

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
                    if (tile := TileRepository.get_tile(*map(int, net_id.split("_")[-2:]))) is None:
                        self.logger.warning(f"Tile with ID {net_id} not found.")
                        return None

                    if Game.get_singleton_instance().handle_tile_click(tile):
                        self.selected_tile = tile
                        self.selected_unit = None
                    else:
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
