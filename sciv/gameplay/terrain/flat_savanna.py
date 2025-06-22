from typing import Any

from ._base_terrain import BaseTerrain
from helpers.colors import Colors


class FlatSavanna(BaseTerrain):
    _name = "world.terrain.flatland_savanna"
    movement_modifier = 0.5
    water_availability = 0
    _fallback_color = Colors.t4f_to_t3(Colors.YELLOW)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
