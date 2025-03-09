from gameplay.terrain.flat_grass import FlatGrass
from gameplay.tiles.base_tile import BaseTile


class LandGrass(BaseTile):
    _terrain = FlatGrass
    _model = _terrain.model
    _cache_name = "LandGrass"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(self._terrain())
