from gameplay.terrain.flat_tundra_snow import FlatTundraSnow as FlatTundraSnowTerrain
from gameplay.tiles.base_tile import BaseTile


class FlatTundraSnow(BaseTile):
    _terrain = FlatTundraSnowTerrain
    _model = _terrain.model
    _cache_name = "FlatTundraSnow"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_terrain(self._terrain())
