from typing import TYPE_CHECKING, Any

from gameplay.improvement import Improvement, ImprovementBuildTurnMode

if TYPE_CHECKING:
    from gameplay.tile import Tile
    from gameplay.player import Player


class BaseCityImprovement(Improvement):
    def __init__(self, tile: "Tile", owner: "Player", *args: Any, **kwargs: Any):
        super().__init__(tile=tile, owner=owner, *args, **kwargs)

        self.constructable_on_tile = False
        self.constructable_builder = False
        self.placeable_on_city = True
        self.placeable_by_player = True
        self.placeable_on_tiles = False
        self.multi_turn_mode = ImprovementBuildTurnMode.MULTI_TURN_RESOURCE
