from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class ClayTablets(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.clay_tablets",
            t_("tech.clay_tablets.name"),
            t_("tech.clay_tablets.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
