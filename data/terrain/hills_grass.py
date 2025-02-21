from ._base_terrain import BaseTerrain
from data.terrain.traits.land import buildable_flat_land


class HillsGrass(BaseTerrain):
    _name = "world.terrain.hills_gras"
    _model = "assets/models/tiles/hills_grass.glb"
    _texture = "assets/models/tiles/hills_grass.png"
    movement_modifier = 0.75
    water_availability = 0.75

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_modifiers(buildable_flat_land)
