from typing import Any
from gameplay.yields import Yields

from ._base_terrain import BaseTerrain, rgb


class Volcano(BaseTerrain):
    _name = "world.terrain.volcano"
    _model = "assets/models/tiles/volcano.glb"

    _fallback_color = rgb(0, 119, 255)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.name = "world.terrain.volcano"
        self.movement_modifier = 0.5

        self.passable: bool = False
        self.passable_without_tech: bool = False

        self.tile_yield_base.add(Yields.nullYield())
