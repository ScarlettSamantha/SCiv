from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class GuidanceSystems(Tech):
    key = "core.guidance_systems"
    name = t_("tech.guidance_systems.name")
    description = t_("tech.guidance_systems.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
