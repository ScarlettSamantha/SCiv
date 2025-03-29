from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class SiegeTactics(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.siege_tactics",
            t_("tech.siege_tactics.name"),
            t_("tech.siege_tactics.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
