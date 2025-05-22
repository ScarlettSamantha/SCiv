from typing import Any

from helpers.colors import Colors

from ._base_terrain import BaseTerrain


class City(BaseTerrain):
    _name = "world.terrain.city"
    fallback_color = (0, 119, 255)
    movement_modifier = 0.5
    _model = "assets/models/tiles/town.glb"
    _fallback_color = Colors.ORANGE

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._texture = "city.png"
