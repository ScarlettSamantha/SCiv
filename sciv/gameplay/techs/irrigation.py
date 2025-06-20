from typing import TYPE_CHECKING, Any, List, Type

from gameplay.tech import Tech
from managers.i18n import t_

if TYPE_CHECKING:
    from system.entity import BaseEntity


class Irrigation(Tech):
    key = "core.irrigation"
    name = t_("tech.irrigation.name")
    description = t_("tech.irrigation.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

    @classmethod
    def unlocks(cls) -> List[Type["BaseEntity"] | Type["Tech"]]:
        from gameplay.improvements.core.resources.plantation import Plantation

        return [Plantation] + super().unlocks()  # type: ignore
