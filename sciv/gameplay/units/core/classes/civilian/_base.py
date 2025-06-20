from typing import TYPE_CHECKING, Any


from gameplay.units.classes.civilian import CivilianBaseClass

if TYPE_CHECKING:
    from gameplay.player import Player
    from gameplay.tile import Tile


class CoreCivilianBaseClass(CivilianBaseClass):
    def __init__(self, tile: "Tile", player: "Player", *args: Any, **kwargs: Any):
        super().__init__(tile, player, *args, **kwargs)
