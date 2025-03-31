from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class LobbyingPower(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.lobbying_power",
            name=t_("content.culture.civics.core.lobbying_power.name"),
            description=t_("content.culture.civics.core.lobbying_power.description"),
            *args,
            **kwargs,
        )
