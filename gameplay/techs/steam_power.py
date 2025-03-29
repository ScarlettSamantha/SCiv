from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class SteamPower(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.steam_power",
            t_("tech.steam_power.name"),
            t_("tech.steam_power.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
