from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Machinery(Tech):
    key = "core.machinery"
    name = t_("tech.machinery.name")
    description = t_("tech.machinery.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
