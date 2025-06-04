from typing import Any

from gameplay.improvements.core.resources.mine import Mine

from ._base_terrain import BaseTerrain


class HillsDesert(BaseTerrain):
    _name = "world.terrain.hills_desert"
    movement_modifier = 0.5
    water_availability = 0.25

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)
        self._texture = "hills_desert.png"
