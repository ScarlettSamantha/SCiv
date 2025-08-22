from typing import TYPE_CHECKING, Any

from gameplay.civic import Conditions
from gameplay.condition import BuildCondition, ResearchCondition
from gameplay.improvements.core.city.barracks import Barracks
from gameplay.techs.hunting_gathering import HuntingGathering
from gameplay.units.core.classes.military._base import RangedUnit
from managers.i18n import t_

if TYPE_CHECKING:
    from gameplay.player import Player
    from gameplay.tile import Tile


class Slinger(RangedUnit):
    _model = "assets/models/units/axemen.glb"
    buildable = True

    key = "core.unit.class.slinger"
    name = t_("content.units.core.units.military.slinger.name")
    description = t_("content.units.core.units.military.slinger.description")
    icon = "units/ancient_slinger.png"
    model_size: float = 0.33

    attack_points: float = 1.0
    attack_armor_penetration: float = 1.0
    attack_power_mele: float = 0.0
    attack_power_ranged: float = 4.0

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
        self.unit_icons_z_offset: float = 3.0
        self.unit_icons_scale: float = 0.75

    def register_actions(self):
        return super().register_actions()

    @classmethod
    def on_tooltip(cls) -> str:
        return str(t_("content.units.core.units.military.slinger.tooltip"))
