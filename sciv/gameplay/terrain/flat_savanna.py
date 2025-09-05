from typing import Any

from gameplay.terrain._base_terrain import BaseTerrain
from helpers.colors import Colors
from managers.i18n import t_


class FlatSavanna(BaseTerrain):
    _name = t_("world.terrain.flatland_savanna")
    movement_modifier = 0.5
    water_availability = 0
    _fallback_color = Colors.t4f_to_t3(Colors.YELLOW)
    _model = "assets/models/terrain/savanna.glb"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
