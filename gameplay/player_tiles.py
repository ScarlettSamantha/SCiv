from typing import TYPE_CHECKING, Dict, Tuple

if TYPE_CHECKING:
    from gameplay.tiles.base_tile import BaseTile


class PlayerTiles:
    def __init__(self):
        self.tiles: Dict[Tuple[int, int], "BaseTile"] = {}

    def add_tile(self, tile: "BaseTile"):
        self.tiles[(tile.x, tile.y)] = tile

    def get_tile(self, x: int, y: int) -> "BaseTile":
        return self.tiles[(x, y)]

    def get_tiles(self) -> Dict[Tuple[int, int], "BaseTile"]:
        return self.tiles

    def remove_tile(self, x: int, y: int):
        del self.tiles[(x, y)]

    def add(self, tile: "BaseTile"):
        self.add_tile(tile)

    def remove(self, tile: "BaseTile"):
        self.remove_tile(tile.x, tile.y)
