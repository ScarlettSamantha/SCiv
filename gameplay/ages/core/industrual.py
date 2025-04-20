from typing import Any

from gameplay.age import Age
from managers.i18n import t_


class Industrial(Age):
    key = "industrial"
    name = t_("content.ages.core.industrial.name")
    description = t_("content.ages.core.industrial.description")
    color = (0, 255, 0, 0)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
