from typing import Any

from gameplay.improvements.core.resources.mine import Mine

from ._base_terrain import BaseTerrain


class FlatDesert(BaseTerrain):
    _name = "world.terrain.flatland_desert"
    movement_modifier = 0.5
    water_availability = 0
    _fallback_color = (253, 255, 128)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._texture = "flat_dessert.png"
        self.add_supported_improvement(Mine)
