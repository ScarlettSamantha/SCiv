from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Currency(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.currency",
            t_("tech.currency.name"),
            t_("tech.currency.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
