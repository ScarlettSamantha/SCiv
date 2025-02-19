from data.tiles.tile import Tile
from data.terrain.hills_snow import HillsSnow as HillSnowTerrain


class HillsSnow(Tile):
    _terrain = HillSnowTerrain
    _model = _terrain.model
    _cache_name = "HillsSnow"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(HillSnowTerrain())
