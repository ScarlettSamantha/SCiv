from typing import TYPE_CHECKING, Any, Optional

from direct.interval.IntervalGlobal import Func, Sequence, Wait
from direct.showbase.DirectObject import DirectObject
from direct.showbase.MessengerGlobal import messenger
from panda3d.core import (
    BitMask32,
    CollisionHandlerQueue,
    CollisionNode,
    CollisionRay,
    CollisionTraverser,
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

        self.register()

    def register(self):
        """
        Bind relevant mouse or keyboard events here.
        """
        # Left-click
        self.accept("mouse1", self.pick_object)

        # Escape key
        self.accept("escape", self.on_escape)

        self.accept("system.input.raycaster_on", self.activate)
        self.accept("system.input.raycaster_off", self.de_activate)
        self.accept("system.input.raycaster_on_delay", self.delay_activate)

    def delay_activate(self, delay: int | float):
        self.sequence = Sequence(Wait(delay), Func(self.activate))
        self.sequence.start()

    def de_activate(self):
        self.logger.info("Deactivating input raycaster.")
        self.active = False

    def activate(self):
        self.logger.info("Activating input raycaster.")
        self.active = True

    def __setup__(self, base, *args: Any, **kwargs: Any) -> None:
        from managers.world import World

        self.base = base
        self.map = World.get_instance()

        return super().__setup__(*args, **kwargs)

    def inject_into_camera(self):
        self.picker = CollisionTraverser()
        self.pq = CollisionHandlerQueue()

        picker_node = CollisionNode("mouseRay")
        self.pickerRay = CollisionRay()
        picker_node.addSolid(self.pickerRay)

        picker_node.setFromCollideMask(BitMask32.bit(1))

        self.pickerNP = self.base.camera.attachNewNode(picker_node)
        self.picker.addCollider(self.pickerNP, self.pq)
        self.register()  # Ensures key bindings are set

    def pick_object(self):
        if not self.active:
            return  # Input is disabled

        if not self.base.mouseWatcherNode.hasMouse():
            print("No mouse in window, cannot pick.")
            return

        mpos = self.base.mouseWatcherNode.getMouse()
        self.pickerRay.setFromLens(self.base.camNode, mpos.getX(), mpos.getY())
        self.picker.traverse(self.base.render)  # type: ignore
        if self.pq.getNumEntries() > 0:
            self.pq.sortEntries()
            entry = self.pq.getEntry(0)  # closest collision
            picked_obj = entry.getIntoNodePath()
            tile_id = picked_obj.getNetTag("tile_id")

            start_of_id = tile_id.split("_")[0]
            if start_of_id == "unit":
                # This is a unit, not a tile
                messenger.send("system.input.user.unit_clicked", [tile_id])
            elif start_of_id == "tile":
                # This is a tile
                messenger.send("system.input.user.tile_clicked", [tile_id])

            return picked_obj
        else:
            self.logger.debug("No object picked. Possibly between tiles or outside the game field.")
            return None

    def on_escape(self):
        """
        This method fires a message when the user presses the Escape key.
        You can handle this in your code by listening for
        'system.input.user.escaped' with an appropriate handler.
        """
        messenger.send("game.input.user.escape_pressed")
