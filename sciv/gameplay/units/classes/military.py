from typing import TYPE_CHECKING, Any

from gameplay.unit import Unit

if TYPE_CHECKING:
    from gameplay.tile import Tile
    from gameplay.player import Player


class MilitaryBaseClass(Unit):
    def __init__(self, tile: "Tile", player: "Player", *args: Any, **kwargs: Any):
        super().__init__(tile=tile, player=player, *args, **kwargs)
