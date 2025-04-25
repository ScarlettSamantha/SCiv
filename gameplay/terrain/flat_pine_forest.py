from typing import Any

from gameplay.improvements.core.resources.logging_camp import LoggingCamp
from gameplay.yields import Yields

from ._base_terrain import BaseTerrain


class FlatPineForest(BaseTerrain):
    _name = "world.terrain.flat_pine_forest"
    movement_modifier = 0.5
    water_availability = 0.75
    _model = "assets/models/tiles/flat_pine.glb"
    _texture = "assets/models/tiles/forrest3.png"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(LoggingCamp)

        self.tile_yield_base = Yields(production=1)
