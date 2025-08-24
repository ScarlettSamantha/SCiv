from typing import Any

from _base_terrain import BaseTerrain
from helpers.colors import Colors
from managers.i18n import t_


class City(BaseTerrain):
    _name = t_("world.terrain.city")
    fallback_color = (0, 119, 255)
    movement_modifier = 0.5
    _model = "assets/models/tiles/town.glb"
    _fallback_color = Colors.t4f_to_t3(Colors.ORANGE)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._texture = "city.png"

    def register_bits(self) -> None:
        return super().register_bits()
