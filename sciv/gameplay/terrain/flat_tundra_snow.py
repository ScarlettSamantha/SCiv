from typing import Any

from gameplay.improvements.core.resources.mine import Mine

from ._base_terrain import BaseTerrain


class FlatTundraSnow(BaseTerrain):
    _name = "world.terrain.flatland_tundra_snow"
    movement_modifier = 1
    water_availability = 0.25
    _fallback_color = (238, 238, 238)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)
        self._texture = "flat_tundra_snow.png"
