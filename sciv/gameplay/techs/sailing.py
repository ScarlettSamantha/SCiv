from typing import TYPE_CHECKING, Any, List, Type

from gameplay.tech import Tech
from managers.i18n import t_

if TYPE_CHECKING:
    from system.entity import BaseEntity


class Sailing(Tech):
    key = "core.sailing"
    name = t_("tech.sailing.name")
    description = t_("tech.sailing.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

    @classmethod
    def unlocks(cls) -> List[Type["BaseEntity"] | Type["Tech"]]:
        from gameplay.improvements.core.resources.fishing_boats import FishingBoats

        return [FishingBoats] + super().unlocks()  # type: ignore
