from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class NuclearFusion(Tech):
    key = "core.nuclear_fusion"
    name = t_("tech.nuclear_fusion.name")
    description = t_("tech.nuclear_fusion.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
