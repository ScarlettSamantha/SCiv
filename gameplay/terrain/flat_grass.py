from gameplay.improvements.core.resources.farm import Farm
from gameplay.improvements.core.resources.mine import Mine
from gameplay.improvements.core.resources.pasture import Pasture

from ._base_terrain import BaseTerrain


class FlatGrass(BaseTerrain):
    _name = "world.terrain.flatland_grass"
    movement_modifier = 0.5
    water_availability = 1
    _model = "assets/models/tiles/grass.glb"
    _texture = "assets/models/tiles/grass2.png"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)
        self.add_supported_improvement(Farm)
        self.add_supported_improvement(Pasture)
