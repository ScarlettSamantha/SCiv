from typing import TYPE_CHECKING, Dict, Tuple

if TYPE_CHECKING:
    from gameplay.tile import Tile


class PlayerTiles:
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

    def add(self, tile: "Tile"):
        self.add_tile(tile)

    def remove(self, tile: "Tile"):
        self.remove_tile(tile.x, tile.y)
