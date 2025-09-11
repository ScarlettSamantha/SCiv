from typing import Any

from gameplay.bits import GroupMode
from gameplay.improvements.core.resources.farm import Farm
from gameplay.improvements.core.resources.logging_camp import LoggingCamp
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.yields import Yields
from managers.i18n import t_


class FlatJungle(BaseTerrain):
    _name = t_("world.terrain.flatland_jungle")
    movement_modifier = 0.5
    water_availability = 0
    _fallback_color = (45, 64, 32)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Farm)
        self.add_supported_improvement(LoggingCamp)

        self.tile_yield_base = Yields(food=1)
        self._texture = "flat_jungle.png"

    def register_bits(self) -> None:
        from gameplay.bits import Bit

        jungle_tree_1 = Bit(
            model="jungle_tree_1.glb",
            scale=0.5,
            offset=(0, 0, 0),
            allow_auto_scale=False,
            preferred_slot="center",
        )
        jungle_tree_2 = Bit(
            model="jungle_tree_2.glb",
            scale=0.5,
            offset=(0, 0, 0),
            allow_auto_scale=False,
            preferred_slot="center",
        )
        jungle_tree_3 = Bit(
            model="jungle_tree_3.glb",
            scale=0.5,
            offset=(0, 0, 0),
            allow_auto_scale=False,
            preferred_slot="center",
        )

        self.bits.mode = GroupMode.OR

        group_one = self.bits.add_group("jungle_tree_group_one", mode=GroupMode.OR)
        group_one.add_bit(jungle_tree_1)

        group_two = self.bits.add_group("jungle_tree_group_two", mode=GroupMode.OR)
        group_two.add_bit(jungle_tree_2)

        group_three = self.bits.add_group("jungle_tree_group_three", mode=GroupMode.OR)
        group_three.add_bit(jungle_tree_3)
