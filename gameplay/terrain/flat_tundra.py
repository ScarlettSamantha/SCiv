from typing import Any

from gameplay.improvements.core.resources.mine import Mine

from ._base_terrain import BaseTerrain
from helpers.colors import Colors


class FlatTundra(BaseTerrain):
    _name = "world.terrain.flatland_grass"
    movement_modifier = 1
    water_availability = 0.25
    _fallback_color = Colors.t4f_to_t3(Colors.GREY)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)
        self._texture = "flat_tundra.png"
