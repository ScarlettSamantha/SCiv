from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Masonry(Tech):
    key = "core.masonry"
    name = t_("tech.masonry.name")
    description = t_("tech.masonry.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
