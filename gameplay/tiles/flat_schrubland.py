from gameplay.terrain.flat_schrubland import FlatSchrubland as FlatSchrublandTerrain
from gameplay.tiles.base_tile import BaseTile


class FlatSchrubland(BaseTile):
    _terrain = FlatSchrublandTerrain
    _model = _terrain.model

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_terrain(FlatSchrublandTerrain())
