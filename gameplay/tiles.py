from typing import Dict, Tuple, TYPE_CHECKING


if TYPE_CHECKING:
    from data.tiles.tile import Tile


class Tiles:
    def __init__(self):
        self.tiles: Dict[Tuple[int, int], "Tile"] = {}

    def add_tile(self, tile: "Tile"):
        self.tiles[(tile.x, tile.y)] = tile

    def get_tile(self, x: int, y: int) -> "Tile":
        return self.tiles[(x, y)]

    def get_tiles(self) -> Dict[Tuple[int, int], "Tile"]:
        return self.tiles

    def remove_tile(self, x: int, y: int):
        del self.tiles[(x, y)]
