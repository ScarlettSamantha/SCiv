from typing import Any

from gameplay.player import Player
from gameplay.tile import Tile
from gameplay.units.classes.military import MilitaryBaseClass
from helpers.colors import Colors


class CoreMilitaryBaseClass(MilitaryBaseClass):
    def __init__(self, tile: Tile, player: Player, *args: Any, **kwargs: Any):
        super().__init__(tile=tile, player=player, *args, **kwargs)

        self.icon_border_color = Colors.YELLOW


class RangedUnit(CoreMilitaryBaseClass):
    attack_range: int = 2

    def __init__(self, tile: Tile, player: Player, *args: Any, **kwargs: Any):
        super().__init__(tile=tile, player=player, *args, **kwargs)
        self.attack_points_left = self.attack_points
        self.attack_power_mele = 0.0
        self.attack_power_ranged = 4.0
