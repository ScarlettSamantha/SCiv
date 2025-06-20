from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class CommunalLiving(Civic):
    key = "core.culture.civics.communal_living"
    name = t_("content.culture.civics.core.communal_living.name")
    description = t_("content.culture.civics.core.communal_living.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
