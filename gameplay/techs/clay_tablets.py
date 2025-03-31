from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class ClayTablets(Tech):
    key = "core.clay_tablets"
    name = t_("tech.clay_tablets.name")
    description = t_("tech.clay_tablets.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
