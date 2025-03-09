from gameplay.terrain.traits.land import buildable_flat_land

from ._base_terrain import BaseTerrain


class HillsGrass(BaseTerrain):
    _name = "world.terrain.hills_gras"
    _model = "assets/models/tiles/hills_grass2.glb"
    _texture = "assets/models/tiles/hills_grass.png"
    movement_modifier = 0.75
    water_availability = 0.75

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_modifiers(buildable_flat_land)
