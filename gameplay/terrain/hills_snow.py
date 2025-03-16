from gameplay.improvements.core.resources.mine import Mine

from ._base_terrain import BaseTerrain


class HillsSnow(BaseTerrain):
    _name = "world.terrain.hills_snow"
    _model = "assets/models/tiles/mountains2.glb"
    _texture = "assets/models/tiles/hills_grass.png"
    movement_modifier = 0.5
    water_availability = 0.25

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)
