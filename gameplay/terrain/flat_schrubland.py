from gameplay.improvements.core.resources.mine import Mine
from gameplay.terrain.traits.land import buildable_flat_land

from ._base_terrain import BaseTerrain


class FlatSchrubland(BaseTerrain):
    _name = "world.terrain.flatland_schrubland"
    movement_modifier = 0.5
    water_availability = 0.75
    _model = "assets/models/tiles/flat_shrubland.glb"
    _texture = "assets/models/tiles/forrest3.png"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_modifiers(buildable_flat_land)

        self.add_supported_improvement(Mine)
