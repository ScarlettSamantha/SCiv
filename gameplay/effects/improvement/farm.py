from typing import TYPE_CHECKING, Any

from gameplay.yields import Yields
from system.effects import Effect

if TYPE_CHECKING:
    from gameplay.tile import Tile
    from gameplay.player import Player


class FarmEffect(Effect):
    def __init__(self, tile: "Tile", owner: "Player", *args: Any, **kwargs: Any):
        super().__init__(tile=tile, player=owner, *args, **kwargs)

        self.yield_impact = Yields(food=1, mode=Yields.ADDITIVE)
