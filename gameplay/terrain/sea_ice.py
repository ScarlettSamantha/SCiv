from gameplay.terrain._base_terrain import BaseTerrain


class SeaIce(BaseTerrain):
    _name = "world.terrain.flatland_grass"
    movement_modifier = 1
    water_availability = 0.25
    _model = "assets/models/tiles/sea_ice.glb"
    _texture = "assets/models/tiles/grass2.png"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
