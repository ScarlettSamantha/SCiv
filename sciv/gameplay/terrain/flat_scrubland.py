from typing import Any

from gameplay.bits import Bit, GroupMode
from gameplay.improvements.core.resources.mine import Mine
from gameplay.yields import Yields

from ._base_terrain import BaseTerrain


class FlatScrubland(BaseTerrain):
    _name = "world.terrain.flatland_scrubland"
    movement_modifier = 0.5
    water_availability = 0.75
    _fallback_color = (127, 179, 90)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)

        self.tile_yield_base = Yields(food=1)
        self._texture = "flat_scrubland.png"

    def register_bits(self) -> None:
        grass_bit = Bit(
            model="cluster_grass_one.glb",
            scale=0.5,
            offset=(0, 0, 0),
            allow_auto_scale=False,
            preferred_slot="center",
        )
        grass_bit2 = Bit(
            model="cluster_grass_two.glb",
            scale=0.5,
            offset=(0, 0, 0),
            allow_auto_scale=False,
            preferred_slot="center",
        )
        self.bits.mode = GroupMode.OR

        group_one = self.bits.add_group("grass_group_one", mode=GroupMode.OR)
        group_one.add_bit(grass_bit)

        group_two = self.bits.add_group("grass_group_two", mode=GroupMode.OR)
        group_two.add_bit(grass_bit2)
        return super().register_bits()
