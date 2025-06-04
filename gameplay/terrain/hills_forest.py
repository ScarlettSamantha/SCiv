from typing import Any

from gameplay.improvements.core.resources.logging_camp import LoggingCamp
from gameplay.improvements.core.resources.mine import Mine

from ._base_terrain import BaseTerrain


class HillsForest(BaseTerrain):
    _name = "world.terrain.hills_forest"
    movement_modifier = 0.5
    water_availability = 0.5

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)
        self.add_supported_improvement(LoggingCamp)
        self._texture = "hills_forest.png"
