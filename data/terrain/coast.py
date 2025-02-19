from ._base_terrain import BaseTerrain


class Coast(BaseTerrain):
    _name = "world.terrain.coast"
    fallback_color = (0, 119, 255)
    movement_modifier = 0.5
    _model = None  # Final assignment: _model is set to None.
    _texture = "assets/models/tiles/water2.png"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
