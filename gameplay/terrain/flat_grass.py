from ._base_terrain import BaseTerrain
from data.terrain.traits.land import buildable_flat_land


class FlatGrass(BaseTerrain):
    _name = "world.terrain.flatland_grass"
    movement_modifier = 0.5
    water_availability = 1
    _model = "assets/models/tiles/grass.glb"
    _texture = "assets/models/tiles/grass2.png"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_modifiers(buildable_flat_land)
