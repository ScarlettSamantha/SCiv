from typing import Any

from gameplay.age import Age
from gameplay.condition import Conditions, GlobalResearchCondition
from gameplay.techs.buttress import Buttress
from managers.i18n import t_


class Medieval(Age):
    key = "medieval"
    name = t_("content.ages.core.medieval.name")
    description = t_("content.ages.core.medieval.description")
    color = (0, 255, 0, 0)
    order: int = 3
    transition_image: str = "assets/images/ages/medieval_transition.png"
    progression_conditions = Conditions(conditions=[GlobalResearchCondition(tech=[Buttress])])

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
