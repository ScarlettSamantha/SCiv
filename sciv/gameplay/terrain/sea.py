from typing import Any

from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.yields import Yields
from helpers.colors import Colors
from managers.i18n import t_


class Sea(BaseTerrain):
    _name = t_("world.terrain.sea_water")
    _fallback_color = Colors.t4f_to_t3(Colors.BLUE)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.name = "world.terrain.sea_water"
        self.movement_modifier = 0.5

        self.passable: bool = False
        self.passable_without_tech: bool = False
        self._texture = "deepsea.png"

        self.tile_yield_base.add(Yields(food=1, gold=1))
