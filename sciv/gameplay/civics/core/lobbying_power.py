from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class LobbyingPower(Civic):
    key = "core.culture.civics.lobbying_power"
    name = t_("content.culture.civics.core.lobbying_power.name")
    description = t_("content.culture.civics.core.lobbying_power.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
