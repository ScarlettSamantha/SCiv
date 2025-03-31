from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Machinery(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.machinery",
            t_("tech.machinery.name"),
            t_("tech.machinery.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
