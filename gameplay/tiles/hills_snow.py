from gameplay.terrain.hills_snow import HillsSnow as HillSnowTerrain
from gameplay.tiles.base_tile import BaseTile


class HillsSnow(BaseTile):
    _terrain = HillSnowTerrain
    _model = _terrain.model
    _cache_name = "HillsSnow"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(HillSnowTerrain())
