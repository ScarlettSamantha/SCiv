from typing import TYPE_CHECKING, Dict, List, Tuple, cast
from weakref import ReferenceType, ref

if TYPE_CHECKING:
    from gameplay.tile import Tile


class PlayerTiles:
    def __init__(self):
        self.tiles: Dict[Tuple[int, int], ReferenceType["Tile"]] = {}

    def add_tile(self, tile: "Tile"):
        self.tiles[(tile.x, tile.y)] = ref(tile)

    def get_tile(self, x: int, y: int) -> "Tile":
        tile_ref: ReferenceType["Tile"] = self.tiles[(x, y)]
        tile: "Tile | None" = tile_ref()
        if tile is None:
            raise ValueError(f"Tile at position ({x}, {y}) has been garbage collected.")
        return tile

    def get_tiles(self) -> Dict[Tuple[int, int], "Tile"]:
        tiles: Dict[Tuple[int, int], "Tile"] = {}
        for key, _ref in self.tiles.items():
            tile: "Tile | None" = _ref()
            if tile is not None:
                tiles[key] = tile
        return tiles

    def remove_tile(self, x: int, y: int):
        del self.tiles[(x, y)]

    def add(self, tile: "Tile"):
        self.add_tile(tile)

    def remove(self, tile: "Tile"):
        self.remove_tile(tile.x, tile.y)

    def __len__(self) -> int:
        return len(self.tiles)

    def dump(self) -> Dict[Tuple[int, int], str]:
        tiles_dump: Dict[Tuple[int, int], str] = {}
        for (x, y), tile_ref in self.tiles.items():
            tile: "Tile | None" = tile_ref()
            if tile is not None:
                tiles_dump[(x, y)] = tile.get_tag()
        return tiles_dump

    def load_state(self, state: List[str]) -> None:
        from managers.entity import EntityManager, EntityType

        self.tiles = {}
        for _ref in state:
            tile: ReferenceType["Tile"] | None = cast(
                ReferenceType["Tile"] | None, EntityManager.get_singleton_instance().get_ref_weak(EntityType.TILE, _ref)
            )
            if tile is None:
                raise ValueError(f"Tile at position {_ref} has been garbage collected.")

            _tile: "Tile | None" = tile()

            if _tile is not None:
                self.tiles[(_tile.x, _tile.y)] = tile
