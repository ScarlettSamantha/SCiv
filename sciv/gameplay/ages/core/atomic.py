from typing import Any

from gameplay.age import Age
from managers.i18n import t_


class Atomic(Age):
    key = "atomic"
    name = t_("content.ages.core.atomic.name")
    description = t_("content.ages.core.atomic.description")
    color = (0, 255, 0, 0)
    order: int = 6
    transition_image: str = "assets/images/ages/atomic_transition.png"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
