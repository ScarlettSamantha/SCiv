from panda3d.core import NodePath
from typing import Any

class Tile:
    
    def __init__(self, id: Any, x: int, y: int, node: NodePath):
        self.id = id
        self.x: int = x
        self.y: int = y
        self.node: NodePath = node
        
        self.terrain: Terrain
        
    def __repr__(self) -> str:
        return f"{str(self.id)}@{str(self.x)},{str(self.y)}"
