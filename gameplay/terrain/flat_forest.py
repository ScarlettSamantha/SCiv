from gameplay.improvements.core.resources.farm import Farm
from gameplay.improvements.core.resources.logging_camp import LoggingCamp
from gameplay.improvements.core.resources.mine import Mine
from gameplay.yields import Yields

from ._base_terrain import BaseTerrain


class FlatForest(BaseTerrain):
    _name = "world.terrain.flatland_forest"
    movement_modifier = 0.5
    water_availability = 0.75
    _model = "assets/models/tiles/flat_woodlands3.glb"
    _texture = "assets/models/tiles/forrest3.png"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tile_yield_base = Yields(production=2)

        self.add_supported_improvement(Mine)
        self.add_supported_improvement(Farm)
        self.add_supported_improvement(LoggingCamp)
