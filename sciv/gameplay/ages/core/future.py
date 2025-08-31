from typing import Any

from gameplay.age import Age
from managers.i18n import t_


class Future(Age):
    key = "future"
    name = t_("content.ages.core.future.name")
    description = t_("content.ages.core.future.description")
    color = (0, 255, 0, 0)
    order: int = 8
    transition_image: str = "assets/images/ages/future_transition.png"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
