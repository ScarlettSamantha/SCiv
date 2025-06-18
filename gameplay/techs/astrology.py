from typing import TYPE_CHECKING, Any

from gameplay.tech import Tech
from managers.i18n import t_
from gameplay.effects.techs.astrology import Astrology as AstrologyEffect

if TYPE_CHECKING:
    from gameplay.player import Player


class Astrology(Tech):
    key = "core.astrology"
    name = t_("tech.astrology.name")
    description = t_("tech.astrology.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

    def on_unlock(self, player: "Player") -> None:
        AstrologyEffect.apply_to_entity(player=player, base_object=player)

        super().on_unlock(player)

    @classmethod
    def unlocks(cls) -> list[type]:
        from gameplay.effects.techs.astrology import Astrology

        return [Astrology] + super().unlocks()
