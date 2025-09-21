from typing import Any

from gameplay.age import Age
from managers.i18n import t_

from gameplay.condition import Conditions, GlobalResearchCondition
from gameplay.techs.cartography import Cartography


class Renaissance(Age):
    key = "renaissance"
    name = t_("content.ages.core.renaissance.name")
    description = t_("content.ages.core.renaissance.description")
    color = (0, 255, 0, 0)
    order: int = 4
    transition_image: str = "assets/images/ages/renaissance_transition.png"
    progression_conditions = Conditions(conditions=[GlobalResearchCondition(tech=[Cartography])])

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
