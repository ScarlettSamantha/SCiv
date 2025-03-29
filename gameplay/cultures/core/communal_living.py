from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class CommunalLiving(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.communal_living",
            name=t_("content.culture.civics.core.communal_living.name"),
            description=t_("content.culture.civics.core.communal_living.description"),
            *args,
            **kwargs,
        )
