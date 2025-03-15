from gameplay.improvements.core.resources.mine import Mine
from gameplay.terrain.traits.land import buildable_flat_land

from ._base_terrain import BaseTerrain


class FlatTundraSnow(BaseTerrain):
    _name = "world.terrain.flatland_tundra_snow"
    movement_modifier = 1
    water_availability = 0.25
    _model = "assets/models/tiles/flat_tundra_snow.glb"
    _texture = "assets/models/tiles/grass2.png"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_modifiers(buildable_flat_land)

        self.add_supported_improvement(Mine)