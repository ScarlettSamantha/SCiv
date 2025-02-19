from ._base_terrain import BaseTerrain
from data.terrain.traits.land import buildable_flat_land


class HillsForest(BaseTerrain):
    _name = "world.terrain.hills_forest"
    movement_modifier = 0.5
    water_availability = 0.5
    _model = "assets/models/tiles/grass2.obj"
    _texture = "assets/models/tiles/grass2.png"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_modifiers(buildable_flat_land)
