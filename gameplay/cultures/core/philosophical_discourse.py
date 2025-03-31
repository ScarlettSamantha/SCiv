from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class PhilosophicalDiscourse(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.philosophical_discourse",
            name=t_("content.culture.civics.core.philosophical_discourse.name"),
            description=t_("content.culture.civics.core.philosophical_discourse.description"),
            *args,
            **kwargs,
        )
