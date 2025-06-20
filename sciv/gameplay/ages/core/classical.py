from typing import Any

from gameplay.age import Age
from managers.i18n import t_


class Classical(Age):
    key = "classical"
    name = t_("content.ages.core.classical.name")
    description = t_("content.ages.core.classical.description")
    color = (0, 255, 0, 0)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
