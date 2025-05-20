from typing import Any

from ._base_terrain import BaseTerrain
from helpers.colors import Colors


class FlatIce(BaseTerrain):
    _name = "world.terrain.flatland_ice"
    movement_modifier = 1
    water_availability = 0.25
    _model = "assets/models/tiles/flat_ice.glb"
    _fallback_color = Colors.WHITE

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
