from typing import Any

from gameplay.yields import Yields

from ._base_terrain import BaseTerrain


class Coast(BaseTerrain):
    _name = "world.terrain.coast"
    fallback_color = (0, 119, 255)
    movement_modifier = 0.5

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.passable: bool = False
        self.passable_without_tech: bool = False
        self._texture = "coast.png"

        self.tile_yield_base = Yields(food=1)
