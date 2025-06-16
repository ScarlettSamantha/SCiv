from typing import Any

from gameplay.promotion import Promotion
from gameplay.units.core.classes.military._base import CoreMilitaryBaseClass
from managers.i18n import t_


class MelePromotion(Promotion):
    pass


class Beserk(MelePromotion):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(
            key="core.unit.promotion.berserk",
            name=t_("content.units.core.promotions.mele.berserk.name"),
            description=t_("content.units.core.promotions.mele.berserk.description"),
            *args,
            **kwargs,
        )


class ClubMan(CoreMilitaryBaseClass):
    _model = "assets/models/units/axemen.glb"
    buildable = True
    key = "core.unit.class.clubman"
    name = t_("content.units.core.units.military.clubman.name")
    description = t_("content.units.core.units.military.clubman.description")
    icon = "units/clubman.png"
    model_size = 0.33

    attack_points = 1
    attack_armor_penetration = 1
    attack_power_mele = 2
    attack_power_ranged = 0

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

    def register_actions(self):
        return super().register_actions()
