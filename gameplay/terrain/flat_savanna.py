from typing import Any

from ._base_terrain import BaseTerrain


class FlatSavanna(BaseTerrain):
    _name = "world.terrain.flatland_savanna"
    movement_modifier = 0.5
    water_availability = 0
    _model = {0: "assets/models/tiles/flat_savanna.glb"}

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
