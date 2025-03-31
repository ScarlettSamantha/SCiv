from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class Propaganda(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.propaganda",
            name=t_("content.culture.civics.core.propaganda.name"),
            description=t_("content.culture.civics.core.propaganda.description"),
            *args,
            **kwargs,
        )
