from typing import Any

from gameplay.age import Age
from managers.i18n import t_


class Classical(Age):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "classical",
            t_("content.ages.core.classical.name"),
            t_("content.ages.core.classical.description"),
            color=(255, 0, 0, 0),
            *args,
            **kwargs,
        )
