from typing import Any

from gameplay.bits import Bit
from gameplay.improvements.core.resources.mine import Mine
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import t_


class FlatDesert(BaseTerrain):
    _name = t_("world.terrain.flatland_desert")
    _model = "assets/models/terrain/flat_desert.glb"
    movement_modifier = 0.5
    water_availability = 0
    _fallback_color = (128, 128, 40)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._texture = "flat_dessert.png"
        self.add_supported_improvement(Mine)

    def register_bits(self) -> None:
        rocks = Bit(
            "desert_rocks.glb", scale=1.3, preferred_slot="center", offset=(0.0, 0.0, -0.05), hpr=(45.0, 0.0, 0.0)
        )
        self.bits.add_bit(rocks)
