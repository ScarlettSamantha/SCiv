from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class HorsebackRiding(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.horseback_riding",
            t_("tech.horseback_riding.name"),
            t_("tech.horseback_riding.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
