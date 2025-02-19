from __future__ import annotations
from world.tiles._base_tile import BaseTile
from world.terrain.flat_desert import FlatDessert


class LandDesert(BaseTile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatDessert)
