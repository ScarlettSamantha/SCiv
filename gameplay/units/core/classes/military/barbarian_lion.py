from typing import Any

from gameplay.tiles.base_tile import BaseTile
from gameplay.units.core.classes.military._base import CoreMilitaryBaseClass
from managers.i18n import t_


class BarbarianLion(CoreMilitaryBaseClass):
    _model = "assets/models/units/barbarian_lion.glb"
    buildable = False
    key = "core.units.military.barbarian.lion"
    name = t_("content.units.units.core.units.military.barbarian.lion.name")
    description = t_("content.units.units.core.units.military.barbarian.lion.name")
    icon = "assets/icons/lions.png"
    model_size = 0.03

    can_retaliate = True

    attack_power_mele = 2.0
    attack_power_ranged = 0.0
    attack_range = 1
    attack_armor_penetration = 1.0
    attack_points = 1.0
    attack_points_cost_mele = 1.0

    defense_mele = 0.0
    defense_ranged = 0.0

    def __init__(self, tile: "BaseTile", *args: Any, **kwargs: Any):
        super().__init__(
            tile=tile,
            *args,
            **kwargs,
        )
        self.model_position_offset = (0, 0, 0.01)
