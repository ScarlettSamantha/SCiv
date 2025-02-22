from ._base_terrain import BaseTerrain
from data.terrain.traits.land import buildable_flat_land


class FlatIce(BaseTerrain):
    _name = "world.terrain.flatland_ice"
    movement_modifier = 1
    water_availability = 0.25
    _model = "assets/models/tiles/flat_ice.glb"
    _texture = "assets/models/tiles/grass2.png"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_modifiers(buildable_flat_land)
