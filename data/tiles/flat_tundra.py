from data.terrain.flat_tundra import FlatTundra as FlatTundraTerrain
from data.tiles.tile import Tile


class FlatTundra(Tile):
    _terrain = FlatTundraTerrain
    _model = _terrain.model
    _cache_name = "FlatTundra"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatTundraTerrain())
