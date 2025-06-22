from typing import Any

from gameplay.improvements.core.city.library import Library
from gameplay.tech import Tech
from managers.i18n import t_
from system.entity import BaseEntity


class Writing(Tech):
    key = "core.writing"
    name = t_("tech.writing.name")
    description = t_("tech.writing.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

    @classmethod
    def unlocks(cls) -> list[type[BaseEntity] | type[Tech] | type[Library]]:
        from gameplay.improvements.core.city.library import Library

        return [Library] + super().unlocks()
