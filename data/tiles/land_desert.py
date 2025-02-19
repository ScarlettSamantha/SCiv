from data.tiles.tile import Tile
from data.terrain.flat_desert import FlatDessert


class LandDesert(Tile):
    _terrain = FlatDessert
    _model = _terrain.model
    _cache_name = "LandDesert"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(self._terrain())
