from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class MassProduction(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.mass_production",
            t_("tech.mass_production.name"),
            t_("tech.mass_production.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
