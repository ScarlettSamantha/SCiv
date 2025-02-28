from data.tiles.base_tile import BaseTile
from data.terrain.flat_grass import FlatGrass


class LandGrass(BaseTile):
    _terrain = FlatGrass
    _model = _terrain.model
    _cache_name = "LandGrass"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(self._terrain())
