from math import sqrt
from typing import Optional, Tuple, Dict, Type
from mixins.singleton import Singleton
from system.generators.base import BaseGenerator
from system.pyload import PyLoad
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
        self.map: Dict[str, Tile] = {}
        self.grid: Dict[Tuple[int, int], Tile] = {}

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

    def get_generators(self) -> Dict[str, Type[BaseGenerator]]:
        from system.generators.base import BaseGenerator

        return PyLoad.load_classes("system/generators", base_classes=BaseGenerator)

    def delegate_to_generator(self):
        _generators = []
        for name, instance in self.get_generators().items():
            if issubclass(instance, BaseGenerator):
                _generators.append(instance(self))
        if not _generators:
            raise ValueError("No generators found")

        if len(_generators) == 1:
            _generators[0].generate()
        else:
            raise ValueError(
                "Multiple generators found"
            )  # @todo implement a way to select a generator

    def lookup(self, tag):
        return self.map[tag]
