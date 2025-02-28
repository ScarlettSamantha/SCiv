from data.tiles.base_tile import BaseTile
from data.terrain.hills_grass import HillsGrass


class HillsGrassland(BaseTile):
    _terrrain = HillsGrass
    _model = _terrrain.model
    _cache_name = "HillsGrassland"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(HillsGrass())
