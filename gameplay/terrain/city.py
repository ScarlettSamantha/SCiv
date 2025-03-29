from typing import Any

from ._base_terrain import BaseTerrain


class City(BaseTerrain):
    _name = "world.terrain.city"
    fallback_color = (0, 119, 255)
    movement_modifier = 0.5
    _model = "assets/models/tiles/town.glb"
    _texture = "assets/models/tiles/water2.png"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
