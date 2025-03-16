from gameplay.improvements.core.resources.mine import Mine

from ._base_terrain import BaseTerrain


class FlatTundra(BaseTerrain):
    _name = "world.terrain.flatland_grass"
    movement_modifier = 1
    water_availability = 0.25
    _model = "assets/models/tiles/tundra.glb"
    _texture = "assets/models/tiles/grass2.png"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)
