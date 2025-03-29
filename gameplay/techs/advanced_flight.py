from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class AdvancedFlight(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.advanced_flight",
            t_("tech.advanced_flight.name"),
            t_("tech.advanced_flight.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
