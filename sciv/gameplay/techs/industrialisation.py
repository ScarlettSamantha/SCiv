from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Industrialisation(Tech):
    key = "core.industrialisation"
    name = t_("tech.industrialisation.name")
    description = t_("tech.industrialisation.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
