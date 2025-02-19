from __future__ import annotations
from world.tiles._base_tile import BaseTile
from world.terrain.flat_forest import FlatForest


class LandForest(BaseTile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatForest)
