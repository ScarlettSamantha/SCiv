from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class ReplacableParts(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.replcable_parts",
            t_("tech.replcable_parts.name"),
            t_("tech.replcable_parts.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
