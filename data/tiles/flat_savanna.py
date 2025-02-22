from data.terrain.flat_savanna import FlatSavanna as FlatSavannaTerrain
from data.tiles.tile import Tile


class FlatSavanna(Tile):
    _terrain = FlatSavannaTerrain
    _model = _terrain.model
    _cache_name = "FlatSavanna"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatSavannaTerrain())
