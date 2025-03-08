from data.tiles.base_tile import BaseTile
from data.terrain.hills_snow import HillsSnow as HillSnowTerrain


class HillsSnow(BaseTile):
    _terrain = HillSnowTerrain
    _model = _terrain.model
    _cache_name = "HillsSnow"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(HillSnowTerrain())
