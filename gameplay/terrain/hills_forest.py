from gameplay.improvements.core.resources.logging_camp import LoggingCamp
from gameplay.improvements.core.resources.mine import Mine
from gameplay.terrain.traits.land import buildable_flat_land

from ._base_terrain import BaseTerrain


class HillsForest(BaseTerrain):
    _name = "world.terrain.hills_forest"
    movement_modifier = 0.5
    water_availability = 0.5
    _model = "assets/models/tiles/forest.glb"
    _texture = "assets/models/tiles/grass2.png"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_modifiers(buildable_flat_land)

        self.add_supported_improvement(Mine)
        self.add_supported_improvement(LoggingCamp)
