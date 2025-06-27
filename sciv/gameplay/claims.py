from typing import TYPE_CHECKING, Set
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
