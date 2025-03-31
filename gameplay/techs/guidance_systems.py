from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class GuidanceSystems(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.guidance_systems",
            t_("tech.guidance_systems.name"),
            t_("tech.guidance_systems.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
