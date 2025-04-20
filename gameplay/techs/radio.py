from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Radio(Tech):
    key = "core.radio"
    name = t_("tech.radio.name")
    description = t_("tech.radio.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
