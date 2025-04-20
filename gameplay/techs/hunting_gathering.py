from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class HuntingGathering(Tech):
    key = "core.hunting_gathering"
    name = t_("tech.hunting_gathering.name")
    description = t_("tech.hunting_gathering.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
