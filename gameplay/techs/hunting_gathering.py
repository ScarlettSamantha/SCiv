from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class HuntingGathering(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.hunting_gathering",
            t_("tech.hunting_gathering.name"),
            t_("tech.hunting_gathering.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
