from typing import Any

from gameplay.age import Age
from gameplay.condition import Conditions
from managers.i18n import t_


class Prehistoric(Age):
    key = "Prehistoric"
    name = t_("content.ages.core.prehistoric.name")
    description = t_("content.ages.core.prehistoric.description")
    color = (0, 255, 0, 0)
    order: int = 0
    progression_conditions = Conditions()

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
