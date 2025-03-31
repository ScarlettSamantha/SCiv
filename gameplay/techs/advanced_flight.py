from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class AdvancedFlight(Tech):
    key = "advanced_flight"
    name = t_("tech.advanced_flight.name")
    description = t_("tech.advanced_flight.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
