from gameplay.terrain.flat_savanna import FlatSavanna as FlatSavannaTerrain
from gameplay.tiles.base_tile import BaseTile


class FlatSavanna(BaseTile):
    _terrain = FlatSavannaTerrain
    _model = _terrain.model
    _cache_name = "FlatSavanna"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_terrain(FlatSavannaTerrain())
