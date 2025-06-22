from typing import Any, List, Type

from gameplay.tech import Tech
from managers.entity import BaseEntity
from managers.i18n import t_


class Mining(Tech):
    key = "core.mining"
    name = t_("tech.mining.name")
    description = t_("tech.mining.description")
    tech_points_required = 10

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

    @classmethod
    def unlocks(cls) -> List[Type["BaseEntity"] | Type["Tech"]]:
        from gameplay.improvements.core.resources.mine import Mine

        return [Mine] + super().unlocks()  # type: ignore
