import random
from typing import Any

from gameplay.bits import Bit, GroupMode
from gameplay.improvements.core.resources.farm import Farm
from gameplay.improvements.core.resources.logging_camp import LoggingCamp
from gameplay.improvements.core.resources.mine import Mine
from gameplay.yields import Yields

from ._base_terrain import BaseTerrain


class FlatForest(BaseTerrain):
    _name = "world.terrain.flatland_forest"
    movement_modifier = 0.5
    water_availability = 0.75
    _fallback_color = (91, 128, 64)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.tile_yield_base = Yields(production=2)

        self.add_supported_improvement(Mine)
        self.add_supported_improvement(Farm)
        self.add_supported_improvement(LoggingCamp)

        self._texture = "flat_light_forest.png"

    def register_bits(self) -> None:
        tree_bit = Bit(model="large_tree_green.glb", scale=random.uniform(0.20, 0.35), offset=(0, 0, -0.3))
        bush_bit = Bit(
            model="bush_small_green.glb",
            scale=0.25,
            offset=(0, 0, -0.3),
        )
        bush2 = bush_bit.copy()

        # make sure the *root* is OR (if you really want only one of the top‐level groups)
        self.bits.mode = GroupMode.OR

        tree_group = self.bits.add_group("tree")
        tree_group.add_bit(tree_bit)

        bush_group = self.bits.add_group("bush", mode=GroupMode.AND)
        bush_group.add_bit(tree_bit)
        bush_group.add_bit(bush_bit)

        alternate_bush = self.bits.add_group("alternate_bush", mode=GroupMode.AND)
        alternate_bush.add_bit(tree_bit)
        alternate_bush.add_bit(bush2)
