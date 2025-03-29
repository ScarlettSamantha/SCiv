from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class NuclearFusion(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.nuclear_fusion",
            t_("tech.nuclear_fusion.name"),
            t_("tech.nuclear_fusion.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
