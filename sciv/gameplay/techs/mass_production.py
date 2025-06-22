from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class MassProduction(Tech):
    key = "core.mass_production"
    name = t_("tech.mass_production.name")
    description = t_("tech.mass_production.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
