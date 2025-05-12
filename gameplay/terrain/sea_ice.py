from typing import Any
from gameplay.terrain._base_terrain import BaseTerrain


class SeaIce(BaseTerrain):
    _name = "world.terrain.flatland_grass"
    movement_modifier = 1
    water_availability = 0.25
    _model = {
        20: "assets/models/tiles/sea_ice.glb",
        30: "assets/models/tiles/sea_ice2.glb",
        25: "assets/models/tiles/sea_ice3.glb",
        0: "assets/models/tiles/sea_ice4.glb",
    }

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
