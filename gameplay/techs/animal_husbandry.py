from typing import Any

from gameplay.tech import Tech
from managers.i18n import t_


class AnimalHusbandry(Tech):
    key = "animal_husbandry"
    name = t_("tech.animal_husbandry.name")
    description = t_("tech.animal_husbandry.description")
    tech_points_required = 20

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
