from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class ReplaceableParts(Tech):
    key = "core.replaceable_parts"
    name = t_("tech.replaceable.name")
    description = t_("tech.replaceable_parts.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
