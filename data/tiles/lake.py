from data.tiles.tile import Tile
from data.terrain.lake import Lake as LakeTerrain


class Lake(Tile):
    _terrain = LakeTerrain
    _model = _terrain.model
    _cache_name = "Lake"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(LakeTerrain())
