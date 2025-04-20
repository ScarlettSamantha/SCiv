from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Apprenticeship(Tech):
    key = "apprenticeship"
    name = t_("tech.apprenticeship.name")
    description = t_("tech.apprenticeship.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
