from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class ShipBuilding(Tech):
    key = "core.ship_building"
    name = t_("tech.ship_building.name")
    description = t_("tech.ship_building.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
