from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class MetalCasting(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.metal_casting",
            t_("tech.metal_casting.name"),
            t_("tech.metal_casting.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
