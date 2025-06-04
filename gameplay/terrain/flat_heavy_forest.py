from typing import Any

from gameplay.improvements.core.resources.farm import Farm
from gameplay.improvements.core.resources.logging_camp import LoggingCamp
from gameplay.improvements.core.resources.mine import Mine
from gameplay.yields import Yields
from helpers.colors import Colors
from ._base_terrain import BaseTerrain


class FlatHeavyForest(BaseTerrain):
    _name = "world.terrain.flat_heavy_forest"
    movement_modifier = 0.5
    water_availability = 0.75
    _fallback_color = Colors.t4f_to_t3(Colors.DARK_GREEN)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)
        self.add_supported_improvement(Farm)
        self.add_supported_improvement(LoggingCamp)

        self.tile_yield_base = Yields(production=1)

        self._texture = "flat_heavy_forest.png"
