from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Flight(Tech):
    key = "core.flight"
    name = t_("tech.flight.name")
    description = t_("tech.flight.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
