from typing import Any

from gameplay.improvements.core.resources.farm import Farm
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.yields import Yields
from managers.i18n import t_


class FlatLightJungle(BaseTerrain):
    _name = t_("world.terrain.flatland_light_jungle")
    movement_modifier = 0.5
    water_availability = 0
    _fallback_color = (91, 128, 64)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Farm)

        self.tile_yield_base = Yields(food=1, culture=1)
        self._texture = "flat_light_jungle.png"

    def register_bits(self) -> None:
        from gameplay.bits import Bit

        tree_1 = Bit("jungle_tree_1.glb", scale=0.3, offset=(0.0, 0.0, -0.05), hpr=(45.0, 0.0, 0.0))
        tree_2 = Bit("jungle_tree_2.glb", scale=0.3, offset=(0.0, 0.0, -0.05), hpr=(45.0, 0.0, 0.0))
        tree_3 = Bit("jungle_tree_3.glb", scale=0.3, offset=(0.0, 0.0, -0.05), hpr=(45.0, 0.0, 0.0))

        self.bits.mode = self.bits.mode.OR

        group_1 = self.bits.add_group("tree_1")
        group_1.add_bit(tree_1)

        group_2 = self.bits.add_group("tree_2")
        group_2.add_bit(tree_2)

        group_3 = self.bits.add_group("tree_3")
        group_3.add_bit(tree_3)
