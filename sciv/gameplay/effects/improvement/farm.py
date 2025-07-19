from typing import TYPE_CHECKING, Any

from gameplay.effect import Effect
from gameplay.yields import Yields
from system.effects import EffectPlacers

if TYPE_CHECKING:
    from gameplay.improvement import Improvement
    from gameplay.player import Player


class FarmEffect(Effect):
    def __init__(self, base_object: "Improvement", player: "Player", *args: Any, **kwargs: Any):
        super().__init__(player=player, *args, **kwargs)

        self.base_object = base_object
        self.place_method = EffectPlacers.PLACE_ON_IMPROVEMENT
        self.yield_impact = Yields(food=1, mode=Yields.ADDITIVE)

    def register_events_handlers(self) -> None: ...

    def on_place(self) -> None:
        return super().on_place()
