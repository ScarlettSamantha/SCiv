from __future__ import annotations
from world.tiles._base_tile import BaseTile
from world.terrain.coast import Coast as CoastTerrain


class Coast(BaseTile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(CoastTerrain)
