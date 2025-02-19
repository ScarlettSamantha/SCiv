from data.tiles.tile import Tile
from data.terrain.mountain import Mountain as MountainTerrain


class Mountain(Tile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTerrain(MountainTerrain())
