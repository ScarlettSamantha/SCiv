from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class StealthTechnology(Tech):
    key = "core.stealth_technology"
    name = t_("tech.stealth_technology.name")
    description = t_("tech.stealth_technology.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
