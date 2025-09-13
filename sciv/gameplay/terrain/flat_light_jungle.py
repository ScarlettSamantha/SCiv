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
    _model = "assets/models/terrain/flat_jungle.glb"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Farm)

        self.tile_yield_base = Yields(food=1, culture=1)
        self._texture = "flat_light_jungle.png"

    def register_bits(self) -> None:
        from gameplay.bits import Bit

        tree_1 = Bit("jungle_tree_4.glb", scale=0.60, offset=(0.0, 0.0, 0.02), hpr=(45.0, 0.0, 0.0))
        tree_trunk = Bit("jungle_tree_trunk.glb", scale=0.155, offset=(0.0, 0.0, 0.02), hpr=(45.0, 0.0, 0.0))
        tree_trunk_2 = Bit("jungle_tree_trunk_2.glb", scale=0.155, offset=(0.0, 0.0, 0.02), hpr=(45.0, 0.0, 0.0))
        leaves = Bit("jungle_leaves.glb", scale=0.60, offset=(0.0, 0.0, 0.02), hpr=(45.0, 0.0, 0.0))
        leaves_2 = Bit("jungle_leaves_2.glb", scale=0.60, offset=(0.0, 0.0, 0.02), hpr=(45.0, 0.0, 0.0))

        self.bits.mode = self.bits.mode.OR

        group_1 = self.bits.add_group("tree_1", mode=self.bits.mode.AND)
        group_1.add_bit(tree_1)
        group_1.add_bit(tree_1.rotate(90).copy())
        group_1.add_bit(tree_trunk.rotate(180).copy())
        group_1.add_bit(leaves.rotate(270).copy())
        group_1.add_bit(tree_1.rotate(310).copy())
        group_1.add_bit(leaves_2.rotate(45).copy())
        group_1.add_bit(tree_trunk_2.rotate(135).copy())

        group_2 = self.bits.add_group("tree_2", mode=self.bits.mode.AND)
        group_2.add_bit(tree_1)
        group_2.add_bit(tree_trunk.rotate(90).copy())
        group_2.add_bit(leaves.rotate(180).copy())
        group_2.add_bit(tree_1.rotate(270).copy())
        group_2.add_bit(tree_trunk.rotate(310).copy())
        group_2.add_bit(leaves_2.rotate(45).copy())
        group_2.add_bit(leaves.rotate(135).copy())
        group_2.add_bit(tree_trunk_2.rotate(225).copy())

        group_3 = self.bits.add_group("tree_3", mode=self.bits.mode.AND)
        group_3.add_bit(tree_1)
        group_3.add_bit(tree_trunk.rotate(90).copy())
        group_3.add_bit(leaves.rotate(180).copy())
        group_3.add_bit(tree_1.rotate(270).copy())
        group_3.add_bit(tree_trunk.rotate(310).copy())
        group_3.add_bit(leaves_2.rotate(45).copy())
        group_3.add_bit(tree_trunk_2.rotate(135).copy())
        group_3.add_bit(leaves.rotate(225).copy())
