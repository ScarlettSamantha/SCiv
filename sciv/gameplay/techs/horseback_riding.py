from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class HorsebackRiding(Tech):
    key = "core.horseback_riding"
    name = t_("tech.horseback_riding.name")
    description = t_("tech.horseback_riding.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
