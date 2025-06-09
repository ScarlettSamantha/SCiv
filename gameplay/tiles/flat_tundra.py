from typing import Any

from gameplay.terrain.flat_tundra import FlatTundra as FlatTundraTerrain
from gameplay.tiles.base_tile import Tile
from helpers.colors import Colors


class FlatTundra(Tile):
    _terrain = FlatTundraTerrain
    _model = _terrain.model
    _cache_name = "FlatTundra"
    _fallback_color = Colors.GREY

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(FlatTundraTerrain())
