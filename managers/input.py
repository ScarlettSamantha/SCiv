from panda3d.core import (
    CollisionRay,
    CollisionNode,
    CollisionTraverser,
    CollisionHandlerQueue,
    BitMask32
)
from typing import Any
from mixins.singleton import Singleton

class Input(Singleton):
    
    def __init__(self):
        self.base: Any = None
        self.active: bool = True
        
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

        # 2) Create a collision node containing a ray solid
        picker_node = CollisionNode('mouseRay')
        self.pickerRay = CollisionRay()
        picker_node.addSolid(self.pickerRay)

        # Set the "from" collide mask to match whatever geometry we want to pick
        picker_node.setFromCollideMask(BitMask32.bit(1))

        # 3) Attach the collision node to the camera
        self.pickerNP = self.base.camera.attachNewNode(picker_node)

        # 4) Add the collider to the traverser
        self.picker.addCollider(self.pickerNP, self.pq)
        self.register()
    
    def pick_object(self):
        """
        Cast a ray from the camera using the current mouse position
        and return (print) whichever object is hit first (closest).
        """
        if not self.base.mouseWatcherNode.hasMouse():
            print("No mouse in window, cannot pick.")
            return

        # 1) Get the mouse position in normalized -1..1 range
        mpos = self.base.mouseWatcherNode.getMouse()

        # 2) Position the collision ray to match the lens
        self.pickerRay.setFromLens(self.base.camNode, mpos.getX(), mpos.getY())
        # 3) Traverse the scene for collisions
        self.picker.traverse(self.base.render)

        # 4) If any hits, sort them and pick the closest
        if self.pq.getNumEntries() > 0:
            self.pq.sortEntries()
            entry = self.pq.getEntry(0)  # closest collision
            picked_obj = entry.getIntoNodePath()
            # If you stored a tag (like tile_id), you can retrieve it:
            tile_id = picked_obj.getNetTag("tile_id")
            print(self.map.map[tile_id])
            if tile_id:
                print(f"You picked tile: {tile_id}")
            else:
                print("You picked (no tile_id tag):", picked_obj)
            return picked_obj
        else:
            print("No object picked.")
            return None
        
    def register(self):
        # Example key to test picking (when 'p' is pressed)
        self.base.accept("p", self.pick_object)