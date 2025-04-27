from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class EfficientAdministration(Civic):
    key = "core.culture.civics.efficient_administration"
    name = t_("content.culture.civics.core.efficient_administration.name")
    description = t_("content.culture.civics.core.efficient_administration.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
