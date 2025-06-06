from typing import Any, List, Type, TYPE_CHECKING

from gameplay.tech import Tech
from managers.i18n import t_

if TYPE_CHECKING:
    from system.entity import BaseEntity


class Construction(Tech):
    key = "core.construction"
    name = t_("tech.construction.name")
    description = t_("tech.construction.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

    @classmethod
    def unlocks(cls) -> List[Type["BaseEntity"] | Type["Tech"]]:
        from gameplay.improvements.core.resources.logging_camp import LoggingCamp

        return [LoggingCamp] + super().unlocks()
