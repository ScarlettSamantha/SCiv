from typing import Any

from gameplay.improvements.core.resources.mine import Mine

from ._base_terrain import BaseTerrain


class FlatDesert(BaseTerrain):
    _name = "world.terrain.flatland_desert"
    movement_modifier = 0.5
    water_availability = 0
    _model = {0: "assets/models/tiles/flat_dessert1.glb", 10: "assets/models/tiles/flat_dessert2.glb"}

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.add_supported_improvement(Mine)
