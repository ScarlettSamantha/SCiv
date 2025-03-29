from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Printing(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.printing",
            t_("tech.printing.name"),
            t_("tech.printing.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
