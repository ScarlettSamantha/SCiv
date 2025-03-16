from gameplay.improvements.core.resources.mine import Mine

from ._base_terrain import BaseTerrain


class HillsDesert(BaseTerrain):
    _name = "world.terrain.hills_desert"
    movement_modifier = 0.5
    water_availability = 0.25
    radatiation = 1.0  # Note: "radatiation" is used as in the original code.
    _model = "assets/models/tiles/hills_desert.glb"
    _texture = "assets/models/tiles/grass2.png"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)
