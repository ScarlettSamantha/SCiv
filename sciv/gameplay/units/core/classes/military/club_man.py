from typing import TYPE_CHECKING, Any

from gameplay.civic import Conditions
from gameplay.condition import BuildCondition, ResearchCondition
from gameplay.improvements.core.city.barracks import Barracks
from gameplay.promotion import Promotion
from gameplay.units.core.classes.military._base import CoreMilitaryBaseClass
from managers.i18n import t_
from gameplay.techs.hunting_gathering import HuntingGathering

if TYPE_CHECKING:
    from gameplay.tile import Tile
    from gameplay.player import Player


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
    attack_power_mele = 3.5
    attack_power_ranged = 0

    def __init__(self, tile: "Tile", player: "Player", *args: Any, **kwargs: Any):
        super().__init__(
            tile=tile,
            player=player,
            *args,
            **kwargs,
        )
        self.build_conditions = Conditions(
            conditions=[
                BuildCondition(tile=tile, improvement=Barracks),
                ResearchCondition(tech=HuntingGathering, player=player),
            ],
            player=player,
        )
        self.unit_icons_z_offset = 3
        self.unit_icons_scale = 0.75

    def register_actions(self):
        return super().register_actions()

    @classmethod
    def on_tooltip(cls) -> str:
        return str(t_("content.units.core.units.military.clubman.tooltip"))
