from typing import Any

from gameplay.age import Age
from managers.i18n import t_


class Renaissance(Age):
    key = "renaissance"
    name = t_("content.ages.core.renaissance.name")
    description = t_("content.ages.core.renaissance.description")
    color = (0, 255, 0, 0)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
