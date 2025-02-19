from panda3d.core import NodePath
from typing import Any, Optional
from data.terrain._base_terrain import BaseTerrain


class Tile:
    def __init__(self, id: Any, x: int, y: int, node: NodePath):
        self.id = id
        self.x: int = x
        self.y: int = y
        self.node: NodePath = node
        self.terrain: Optional[BaseTerrain] = None

    def __repr__(self) -> str:
        return f"{str(self.id)}@{str(self.x)},{str(self.y)}"

    def set_color(self, color: tuple[float, float, float, float]):
        self.node.setColor(*color)

    def get_node(self) -> NodePath:
        return self.node

    def set_terrain(self, terrain: BaseTerrain):
        self.terrain = terrain

    def get_terrain(self) -> Optional[BaseTerrain]:
        return self.terrain
