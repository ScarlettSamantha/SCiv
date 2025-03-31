from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class ReplaceableParts(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.replaceable_parts",
            t_("tech.replaceable.name"),
            t_("tech.replaceable_parts.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
