from gameplay.improvements.core.resources.logging_camp import LoggingCamp
from gameplay.terrain.traits.land import buildable_flat_land

from ._base_terrain import BaseTerrain


class FlatPineForest(BaseTerrain):
    _name = "world.terrain.flat_pine_forest"
    movement_modifier = 0.5
    water_availability = 0.75
    _model = "assets/models/tiles/flat_pine.glb"
    _texture = "assets/models/tiles/forrest3.png"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_modifiers(buildable_flat_land)

        self.add_supported_improvement(LoggingCamp)
