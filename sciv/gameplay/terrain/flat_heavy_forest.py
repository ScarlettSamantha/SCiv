from typing import Any

from gameplay.bits import Bit, GroupMode
from gameplay.improvements.core.resources.farm import Farm
from gameplay.improvements.core.resources.logging_camp import LoggingCamp
from gameplay.improvements.core.resources.mine import Mine
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.yields import Yields
from managers.i18n import t_


class FlatHeavyForest(BaseTerrain):
    _name = t_("world.terrain.flatland_heavy_forest")
    movement_modifier = 0.5
    water_availability = 0.75
    _fallback_color = (91, 128, 64)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)
        self.add_supported_improvement(Farm)
        self.add_supported_improvement(LoggingCamp)

        self.tile_yield_base = Yields(production=1)

        self._texture = "flat_heavy_forest.png"

    def register_bits(self) -> None:
        small_pine: Bit = Bit(model="tree_pine_green_small.glb", scale=0.45, offset=(0, 0, 0.05))
        medium_pine: Bit = Bit(model="tree_pine_green_middle.glb", scale=0.45, offset=(0, 0, 0.05))
        large_pine: Bit = Bit(model="tree_pine_green_large.glb", scale=0.45, offset=(0, 0, 0.05))

        self.bits.mode = GroupMode.OR

        one_tree_group = self.bits.add_group("one_tree", mode=GroupMode.OR)
        one_tree_group.add_bit(small_pine)
        one_tree_group.add_bit(medium_pine)
        one_tree_group.add_bit(large_pine)

        two_tree_group = self.bits.add_group("two_tree", mode=GroupMode.OR)
        two_varient = two_tree_group.add_group("two_tree_varient", mode=GroupMode.OR)
        two_varient_two = two_tree_group.add_group("two_tree_varient_two", mode=GroupMode.OR)
        two_varient.add_bit(small_pine)
        two_varient.add_bit(large_pine)

        two_varient_two.add_bit(small_pine)
        two_varient_two.add_bit(medium_pine)

        three_tree_group = self.bits.add_group("three_tree", mode=GroupMode.AND)
        three_tree_group.add_bit(small_pine)
        three_tree_group.add_bit(medium_pine)
        three_tree_group.add_bit(large_pine)
