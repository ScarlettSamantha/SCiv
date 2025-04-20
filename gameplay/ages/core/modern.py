from typing import Any

from gameplay.age import Age
from managers.i18n import t_


class Modern(Age):
    key = "modern"
    name = t_("content.ages.core.modern.name")
    description = t_("content.ages.core.modern.description")
    color = (0, 255, 0, 0)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
