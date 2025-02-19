from panda3d.core import (
    CollisionRay,
    CollisionNode,
    CollisionTraverser,
    CollisionHandlerQueue,
    BitMask32,
)
from typing import Any
from mixins.singleton import Singleton
from direct.showbase.MessengerGlobal import messenger


class Input(Singleton):
    def __init__(self, base):
        self.base: Any = base
        self.active: bool = False

    def de_activate(self):
        self.active = False

    def activate(self):
        self.active = True

    def __setup__(self, base, *args: Any, **kwargs: Any) -> None:
        from managers.world import World

        self.base = base
        self.map = World.get_instance(self.base)

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
        self.picker.traverse(self.base.render)

        if self.pq.getNumEntries() > 0:
            self.pq.sortEntries()
            entry = self.pq.getEntry(0)  # closest collision
            picked_obj = entry.getIntoNodePath()
            tile_id = picked_obj.getNetTag("tile_id")
            messenger.send("system.input.user.tile_clicked", [tile_id])
            return picked_obj
        else:
            print("No object picked. Possibly between tiles or outside the game field.")
            return None

    def register(self):
        """
        Bind relevant mouse or keyboard events here.
        """
        # Left-click
        self.base.accept("mouse1", self.pick_object)

        # Escape key
        self.base.accept("escape", self.on_escape)

    def on_escape(self):
        """
        This method fires a message when the user presses the Escape key.
        You can handle this in your code by listening for
        'system.input.user.escaped' with an appropriate handler.
        """
        messenger.send("game.input.user.escape_pressed")
