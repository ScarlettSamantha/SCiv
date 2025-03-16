from ._base_terrain import BaseTerrain


class FlatSavanna(BaseTerrain):
    _name = "world.terrain.flatland_savanna"
    movement_modifier = 0.5
    water_availability = 0
    _model = "assets/models/tiles/flat_savanna.glb"
    _texture = "assets/models/tiles/dessert2.png"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
