from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class NuclearFission(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.nuclear_fission",
            t_("tech.nuclear_fission.name"),
            t_("tech.nuclear_fission.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
