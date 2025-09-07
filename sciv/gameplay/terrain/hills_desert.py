from typing import Any

from gameplay.bits import Bit
from gameplay.improvements.core.resources.mine import Mine
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import t_


class HillsDesert(BaseTerrain):
    _name = t_("world.terrain.hills_desert")
    movement_modifier = 0.5
    water_availability = 0.25
    _fallback_color = (255, 226, 128)
    _model = "assets/models/terrain/hill_desert.glb"
    model_pos_z_offset = -0.0

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)
        self._texture = "hills_desert.png"

    def register_bits(self) -> None:
        hill = Bit(
            "desert_hills.glb", scale=1.32, preferred_slot="center", offset=(0.0, 0.0, -0.05), hpr=(45.0, 0.0, 0.0)
        )
        self.bits.add_bit(hill)
