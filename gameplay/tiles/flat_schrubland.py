from data.terrain.flat_schrubland import FlatSchrubland as FlatSchrublandTerrain
from data.tiles.base_tile import BaseTile


class FlatSchrubland(BaseTile):
    _terrain = FlatSchrublandTerrain
    _model = _terrain.model

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatSchrublandTerrain())
