from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class CelestialNavigation(Tech):
    key = "core.celestial_navigation"
    name = t_("tech.celestial_navigation.name")
    description = t_("tech.celestial_navigation.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
