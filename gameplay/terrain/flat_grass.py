import random
from typing import Any

from gameplay.bits import GroupMode, Bit
from gameplay.improvements.core.resources.farm import Farm
from gameplay.improvements.core.resources.mine import Mine
from gameplay.improvements.core.resources.pasture import Pasture
from gameplay.yields import Yields

from ._base_terrain import BaseTerrain


class FlatGrass(BaseTerrain):
    _name = "world.terrain.flatland_grass"
    movement_modifier = 0.5
    water_availability = 1
    _fallback_color = (106, 255, 0)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)
        self.add_supported_improvement(Farm)
        self.add_supported_improvement(Pasture)
        self._texture = "flat_grass.png"

        self.tile_yield_base = Yields(food=1)

    def register_bits(self) -> None:
        tree_bit = Bit(
            model="large_tree_green.glb",
            scale=random.uniform(0.1, 0.35),
            hpr=(0, 0, 0),
            offset=(0, 0, 0.00),
        )
        bush_bit = Bit(
            model="bush_small_green.glb",
            scale=0.25,
            hpr=(0, 0, 0),
            offset=(-0.25, 0.25, 0.00),
        )
        bush2 = bush_bit.copy()
        bush2.offset = (0.25, -0.25, 0.00)

        self.bits.mode = GroupMode.OR

        tree_group = self.bits.add_group("tree")
        tree_group.add_bit(tree_bit)

        bush_group = self.bits.add_group("bush", mode=GroupMode.AND)
        bush_group.add_bit(bush_bit)
        bush_group.add_bit(bush2)

        alternate_bush = self.bits.add_group("alternate_bush", mode=GroupMode.OR)
        alternate_bush.add_bit(bush_bit)
        alternate_bush.add_bit(bush2)
