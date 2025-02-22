from data.terrain.flat_jungle import FlatJungle as FlatJungleTerrain
from data.tiles.tile import Tile


class FlatJungle(Tile):
    _terrain = FlatJungleTerrain
    _model = _terrain.model
    _cache_name = "FlatJungle"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatJungleTerrain())
