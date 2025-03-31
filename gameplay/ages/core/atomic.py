from typing import Any

from gameplay.age import Age
from managers.i18n import t_


class Atomic(Age):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="ancient",
            name=t_("content.ages.core.atomic.name"),
            description=t_("content.ages.core.atomic.description"),
            color=(0, 255, 0, 0),
            *args,
            **kwargs,
        )
