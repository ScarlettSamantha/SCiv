from typing import Any
from gameplay.player import Player
from gameplay.tile import Tile
from gameplay.units.classes.military import MilitaryBaseClass
from helpers.colors import Colors


class CoreMilitaryBaseClass(MilitaryBaseClass):
    def __init__(self, tile: Tile, player: Player, *args: Any, **kwargs: Any):
        super().__init__(tile, player, *args, **kwargs)

        self.icon_border_color = Colors.YELLOW
