from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class HuntingGethering(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.hunting_gethering",
            t_("tech.hunting_gethering.name"),
            t_("tech.hunting_gethering.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
