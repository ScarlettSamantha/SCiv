from typing import TYPE_CHECKING, Any

from gameplay.yields import Yields
from gameplay.effect import Effect

from managers.i18n import t_
from system.effects import EffectPlacers

if TYPE_CHECKING:
    from gameplay.player import Player


class DivineRightEffect(Effect):
    name = t_("effects.civics.divine_right.name")
    description = t_(
        "effects.civics.divine_right.description", {"effects": "\n".join(["+2 Religion from your capital"])}
    )
    place_method = EffectPlacers.PLACE_ON_IMPROVEMENT

    def __init__(self, player: "Player", *args: Any, **kwargs: Any):
        super().__init__(player=player, *args, **kwargs)

        self.needs_turn_processing = False
        self.is_timed = False
        self.yield_impact = Yields(faith=2, mode=Yields.ADDITIVE)

    def on_place(self) -> None:
        if not self.is_registered:
            self.register()
        return super().on_place()

    def register_events_handlers(self) -> None: ...
