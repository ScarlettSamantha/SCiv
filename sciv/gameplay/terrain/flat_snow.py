from typing import Any

from gameplay.terrain._base_terrain import BaseTerrain
from helpers.colors import Colors
from managers.i18n import t_


class FlatSnow(BaseTerrain):
    _name = t_("world.terrain.flatland_snow")
    movement_modifier = 1
    water_availability = 0.25
    _fallback_color = Colors.t4f_to_t3(Colors.WHITE)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self._texture = "flat_snow.png"
