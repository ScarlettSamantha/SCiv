from typing import TYPE_CHECKING, List, Set, cast
from weakref import ReferenceType, ref

if TYPE_CHECKING:
    from gameplay.player import Player
    from gameplay.tile import Tile


class Claims:
    def __init__(self, player: "Player"):
        self.player: ReferenceType["Player"] = ref(player)
        self._claimed_tiles: Set[ReferenceType["Tile"]] = set()

    def __len__(self) -> int:
        return len(self._claimed_tiles)

    def load_state(self, state: List[str]) -> None:
        from managers.entity import EntityManager, EntityType

        for tile_tag in state:
            tile_ref: ReferenceType["Tile"] | None = cast(
                ReferenceType["Tile"] | None,
                EntityManager.get_singleton_instance().get_ref_weak(EntityType.TILE, tile_tag),
            )
            if tile_ref is None:
                raise ValueError(f"Tile with tag {tile_tag} has been garbage collected.")
            tile: "Tile | None" = tile_ref()
            if tile is not None:
                self._claimed_tiles.add(ref(tile))

    def dump(self) -> List[str]:
        tiles: List[str] = []
        for tile_ref in self._claimed_tiles:
            tile: "Tile | None" = tile_ref()
            if tile is not None:
                tiles.append(tile.get_tag())
        return tiles
