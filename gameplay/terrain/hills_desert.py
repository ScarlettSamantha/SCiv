from ._base_terrain import BaseTerrain
from data.terrain.traits.land import buildable_flat_land


class HillsDesert(BaseTerrain):
    _name = "world.terrain.hills_desert"
    movement_modifier = 0.5
    water_availability = 0.25
    radatiation = 1.0  # Note: "radatiation" is used as in the original code.
    _model = "assets/models/tiles/hills_desert.glb"
    _texture = "assets/models/tiles/grass2.png"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_modifiers(buildable_flat_land)
