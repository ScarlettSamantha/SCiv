from typing import Any

from gameplay.terrain._base_terrain import BaseTerrain
from helpers.colors import Colors
from managers.i18n import t_

from gameplay.bits import Bit


class FlatSavanna(BaseTerrain):
    _name = t_("world.terrain.flatland_savanna")
    movement_modifier = 0.5
    water_availability = 0
    model_pos_z_offset = 0.0
    _fallback_color = Colors.t4f_to_t3(Colors.YELLOW)
    _model = "assets/models/terrain/savanna.glb"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

    def register_bits(self) -> None:
        bits = Bit(
            "savanna_bits_1.glb", scale=1.0, preferred_slot="center", offset=(0.0, 0.0, -0.05), hpr=(45.0, 0.0, 0.0)
        )

        self.bits.add_bit(bits)
