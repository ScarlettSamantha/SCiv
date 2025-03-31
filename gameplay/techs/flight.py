from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Flight(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.flight",
            t_("tech.flight.name"),
            t_("tech.flight.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
