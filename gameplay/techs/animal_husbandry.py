from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class AnimalHusbandry(Tech):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            "core.animal_husbandry",
            t_("tech.animal_husbandry.name"),
            t_("tech.animal_husbandry.description"),
            tech_points_required=20,
            *args,
            **kwargs,
        )
