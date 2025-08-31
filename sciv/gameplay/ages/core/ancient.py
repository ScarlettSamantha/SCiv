from typing import Any

from gameplay.age import Age
from gameplay.condition import Conditions, GlobalResearchCondition
from gameplay.techs.hunting_gathering import HuntingGathering
from managers.i18n import t_


class Ancient(Age):
    key = "ancient"
    name = t_("content.ages.core.ancient.name")
    description = t_("content.ages.core.ancient.description")
    color = (0, 255, 0, 0)
    order: int = 1
    progression_conditions = Conditions(conditions=[GlobalResearchCondition(tech=[HuntingGathering])])
    transition_image: str = "assets/images/ages/ancient_transition.png"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
