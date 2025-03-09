from gameplay.terrain.flat_snow import FlatSnow as FlatSnowTerrain
from gameplay.tiles.base_tile import BaseTile


class FlatSnow(BaseTile):
    _terrain = FlatSnowTerrain
    _model = _terrain.model
    _cache_name = "FlatSnow"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatSnowTerrain())
