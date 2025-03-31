from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class Masonry(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.masonry",
            t_("tech.masonry.name"),
            t_("tech.masonry.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
