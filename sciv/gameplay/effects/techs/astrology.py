from typing import TYPE_CHECKING, Any

from gameplay.improvements.core.resources.farm import Farm
from gameplay.yields import Yields
from gameplay.effect import Effect

from managers.i18n import t_
from system.effects import EffectPlacers

if TYPE_CHECKING:
    from gameplay.player import Player
    from gameplay.improvement import Improvement
    from gameplay.unit import Unit


class AstrologyFarmEffect(Effect):
    name = None
    description = None
    place_method = EffectPlacers.PLACE_ON_IMPROVEMENT

    def __init__(self, player: "Player", base_object: "Improvement", *args: Any, **kwargs: Any):
        super().__init__(player=player, *args, **kwargs)

        self.yield_impact = Yields(food=1, mode=Yields.ADDITIVE)

    def register_events_handlers(self) -> None: ...


class Astrology(Effect):
    name = t_("effects.techs.astrology.name")
    description = t_("effects.techs.astrology.description", {"effects": "\n".join(["- +1 Food from Farms"])})
    place_method = EffectPlacers.PLACE_ON_PLAYER

    def __init__(self, player: "Player", *args: Any, **kwargs: Any):
        super().__init__(player=player, *args, **kwargs)

        self.needs_turn_processing = False
        self.is_timed = False

    def register_events_handlers(self) -> None:
        self.accept("game.gameplay.unit.build_improvement_success", self.on_build_improvement_success)

    def on_place(self) -> None:
        self._place_on_all_farms()
        if not self.is_registered:
            self.register()
        return super().on_place()

    def _place_on_all_farms(self) -> None:
        for tile in self.get_owner().get_all_tiles().values():
            for improvement in tile.get_improvements().all():
                if isinstance(improvement, Farm) and not improvement.effects.has(AstrologyFarmEffect):
                    AstrologyFarmEffect.apply_to_entity(
                        player=self.get_owner(),
                        base_object=improvement,
                    )

    def on_build_improvement_success(self, improvement: "Improvement", unit: "Unit") -> None:
        AstrologyFarmEffect.apply_to_entity(
            player=self.get_owner(),
            base_object=improvement,
        )
