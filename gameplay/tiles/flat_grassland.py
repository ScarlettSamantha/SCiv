from data.terrain.flat_grass import FlatGrass as FlatGrassTerrain
from data.tiles.base_tile import BaseTile


class FlatGrass(BaseTile):
    _terrain = FlatGrassTerrain
    _model = _terrain.model
    _cache_name = "FlatGrass"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatGrassTerrain())
