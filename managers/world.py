import random
from math import sqrt
from typing import Optional, Tuple, Dict, Type

from mixins.singleton import Singleton
from system.generators.base import BaseGenerator
from data.tiles.tile import Tile


class World(Singleton):
    def __setup__(self, base):
        self.base = base
        self.hex_radius: float = 0.5
        self.col_spacing: float = 1.4
        self.cols: int = 5
        self.rows: int = 5
        self.middle_x: Optional[float] = None
        self.middle_y: Optional[float] = None
        # Key is the tag, value is the tile.
        self.map: Dict[str, Tile] = {}
        # Key is the (col, row) tuple, value is the tile.
        self.grid: Dict[Tuple[int, int], Tile] = {}
        self.generator: Optional[Type[BaseGenerator]] = None

    def __init__(self, base):
        self.base = base

    def generate(self, cols: int, rows: int, radius: float, spacing: float = 1.5):
        self.hex_radius = radius
        self.col_spacing = spacing * self.hex_radius
        self.row_spacing = sqrt(3) * self.hex_radius
        self.cols = cols
        self.rows = rows

        # Compute the middle of the grid.
        self.middle_x = ((cols - 1) * self.col_spacing) / 2.0
        self.middle_y = ((rows - 1) * self.row_spacing) / 2.0

    def lookup_on_tag(self, tag: str) -> Optional[Tile]:
        return self.map.get(tag, None)

    def get_generator(self) -> Optional[Type[BaseGenerator]]:
        if self.generator and issubclass(self.generator, BaseGenerator):
            return self.generator
        return None

    def lookup(self, tag):
        return self.map[tag]

    def random_tile(self) -> Tile:
        return self.grid[random.choice(list(self.grid.keys()))]

    def get_grid(self) -> Dict[Tuple[int, int], Tile]:
        return self.grid
