from gameplay.terrain.flat_tundra import FlatTundra as FlatTundraTerrain
from gameplay.tiles.base_tile import BaseTile


class FlatTundra(BaseTile):
    _terrain = FlatTundraTerrain
    _model = _terrain.model
    _cache_name = "FlatTundra"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_terrain(FlatTundraTerrain())
