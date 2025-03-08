from gameplay.terrain.flat_jungle import FlatJungle as FlatJungleTerrain
from gameplay.tiles.base_tile import BaseTile


class FlatJungle(BaseTile):
    _terrain = FlatJungleTerrain
    _model = _terrain.model
    _cache_name = "FlatJungle"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatJungleTerrain())
