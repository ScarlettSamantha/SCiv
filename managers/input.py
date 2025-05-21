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

from mixins.singleton import Singleton

if TYPE_CHECKING:
    from main import SCIV


class Input(Singleton, DirectObject):
    def __init__(self, base: "SCIV"):
        super().__init__()
        self.base: "SCIV" = base
        self.active: bool = False
        self.sequence: Optional[Sequence] = None

        self.logger = self.base.logger.engine.getChild("manager.input")

        self.hovered_tile_id: Optional[str] = None
        self._last_mouse_pos: Optional[tuple[float, float]] = None
        self._hover_frame_skip = 10  # how many frames to skip before checking for hover

        self.register()

    def reset(self):
        self.active = False

    def register(self):
        # Left-click
        self.accept("mouse1", self.pick_object)
        self.accept("f7", self.run_analyze)

        # Escape key
        self.accept("escape", self.on_escape)

        self.accept("system.input.raycaster_on", self.activate)
        self.accept("system.input.raycaster_off", self.de_activate)
        self.accept("system.input.raycaster_on_delay", self.delay_activate)

        delay_seconds: float = self._hover_frame_skip / 60
        self.base.taskMgr.add(self.hover_task, "input-hover-task", delay=delay_seconds)

    def delay_activate(self, delay: int | float):
        self.sequence = Sequence(Wait(delay), Func(self.activate))  # type: ignore
        self.sequence.start()

    def de_activate(self):
        self.logger.info("Deactivating input raycaster.")
        self.active = False

    def activate(self):
        self.logger.info("Activating input raycaster.")
        self.active = True

    def __setup__(self, base: "SCIV", *args: Any, **kwargs: Any) -> None:
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
            entry = self.pq.getEntry(0)
            picked_obj = entry.getIntoNodePath()
            tile_id = picked_obj.getNetTag("tile_id")

            if tile_id.startswith("tile") and tile_id != self.hovered_tile_id:
                self.hovered_tile_id = tile_id
                messenger.send("system.input.user.tile_hovered", [tile_id])
        else:
            if self.hovered_tile_id is not None:
                messenger.send("system.input.user.tile_unhovered", [self.hovered_tile_id])
                self.hovered_tile_id = None

        return task.cont

    def run_analyze(self):
        render.analyze()

    def pick_object(self) -> NodePath | None:
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
            entry = self.pq.getEntry(0)  # type: ignore # closest collision
            picked_obj: NodePath = entry.getIntoNodePath()  # type: ignore
            tile_id = picked_obj.getNetTag("tile_id")  # type: ignore

            start_of_id = tile_id.split("_")[0]  # type: ignore
            if start_of_id == "unit":
                # This is a unit, not a tile
                messenger.send("system.input.user.unit_clicked", [tile_id])
            elif start_of_id == "tile":
                # This is a tile
                messenger.send("system.input.user.tile_clicked", [tile_id])

            return picked_obj  # type: ignore
        else:
            self.logger.debug("No object picked. Possibly between tiles or outside the game field.")
            return None

    def on_escape(self):
        """
        Method fires a message when the user presses the Escape key.

        You can handle this in your code by listening for
        'system.input.user.escaped' with an appropriate handler.
        """
        messenger.send("game.input.user.escape_pressed")
