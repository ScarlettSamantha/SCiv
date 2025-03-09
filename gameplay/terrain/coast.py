from ._base_terrain import BaseTerrain


class Coast(BaseTerrain):
    _name = "world.terrain.coast"
    fallback_color = (0, 119, 255)
    movement_modifier = 0.5
    _model = "assets/models/tiles/coast.glb"
    _texture = "assets/models/tiles/water2.png"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.passable: bool = False
        self.passable_without_tech: bool = False
