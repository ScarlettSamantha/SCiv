from ._base_terrain import BaseTerrain


class FlatIce(BaseTerrain):
    _name = "world.terrain.flatland_ice"
    movement_modifier = 1
    water_availability = 0.25
    _model = "assets/models/tiles/flat_ice.glb"
    _texture = "assets/models/tiles/grass2.png"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
