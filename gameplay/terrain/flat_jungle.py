from gameplay.improvements.core.resources.farm import Farm
from gameplay.improvements.core.resources.logging_camp import LoggingCamp
from gameplay.terrain.traits.land import buildable_flat_land

from ._base_terrain import BaseTerrain


class FlatJungle(BaseTerrain):
    _name = "world.terrain.flatland_jungle"
    movement_modifier = 0.5
    water_availability = 0
    _model = "assets/models/tiles/flat_jungle2.glb"
    _texture = "assets/models/tiles/dessert2.png"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_modifiers(buildable_flat_land)

        self.add_supported_improvement(Farm)
        self.add_supported_improvement(LoggingCamp)
