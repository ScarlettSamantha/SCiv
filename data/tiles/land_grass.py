from __future__ import annotations
from world.tiles._base_tile import BaseTile
from world.terrain.flat_grass import FlatGrass


class LandGrass(BaseTile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(FlatGrass())
