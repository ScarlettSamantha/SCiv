from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Butress(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.butress",
            t_("tech.butress.name"),
            t_("tech.butress.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
