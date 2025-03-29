from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Apprenticeship(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.apprenticeship",
            t_("tech.apprenticeship.name"),
            t_("tech.apprenticeship.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
