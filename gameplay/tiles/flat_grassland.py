from typing import Any
from gameplay.terrain.flat_grass import FlatGrass as FlatGrassTerrain
from gameplay.tiles.base_tile import BaseTile
from helpers.colors import Colors


class FlatGrass(BaseTile):
    _terrain = FlatGrassTerrain
    _model = _terrain.model
    _cache_name = "FlatGrass"
    _fallback_color = Colors.GREEN

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(FlatGrassTerrain())
