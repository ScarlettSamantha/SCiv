from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Buttress(Tech):
    key = "core.buttress"
    name = t_("tech.buttress.name")
    description = t_("tech.buttress.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(

            *args,
            **kwargs,
        )
