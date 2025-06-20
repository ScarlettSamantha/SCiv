from typing import TYPE_CHECKING, Dict, Tuple
import weakref

if TYPE_CHECKING:
    from gameplay.tile import Tile


class PlayerTiles:
    def __init__(self):
        self.tiles: Dict[Tuple[int, int], weakref.ReferenceType["Tile"]] = {}

    def add_tile(self, tile: "Tile"):
        _tile = weakref.ref(tile)
        self.tiles[(tile.x, tile.y)] = _tile

    def get_tile(self, x: int, y: int) -> "Tile":
        tile_ref = self.tiles[(x, y)]
        tile = tile_ref()
        if tile is None:
            raise ValueError(f"Tile at position ({x}, {y}) has been garbage collected.")
        return tile

    def get_tiles(self) -> Dict[Tuple[int, int], "Tile"]:
        tiles: Dict[Tuple[int, int], "Tile"] = {}
        for key, ref in self.tiles.items():
            tile = ref()
            if tile is not None:
                tiles[key] = tile
        return tiles

    def remove_tile(self, x: int, y: int):
        del self.tiles[(x, y)]

    def add(self, tile: "Tile"):
        self.add_tile(tile)

    def remove(self, tile: "Tile"):
        self.remove_tile(tile.x, tile.y)
