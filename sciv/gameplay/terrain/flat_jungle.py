from typing import Any

from gameplay.improvements.core.resources.farm import Farm
from gameplay.improvements.core.resources.logging_camp import LoggingCamp
from gameplay.yields import Yields

from ._base_terrain import BaseTerrain


class FlatJungle(BaseTerrain):
    _name = "world.terrain.flatland_jungle"
    movement_modifier = 0.5
    water_availability = 0
    _fallback_color = (45, 64, 32)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Farm)
        self.add_supported_improvement(LoggingCamp)

        self.tile_yield_base = Yields(food=1)
        self._texture = "flat_jungle.png"
