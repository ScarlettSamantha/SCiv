from typing import Any

from gameplay.age import Age
from gameplay.condition import Conditions, GlobalResearchCondition
from gameplay.techs.iron_working import IronWorking
from managers.i18n import t_


class Classical(Age):
    key = "classical"
    name = t_("content.ages.core.classical.name")
    description = t_("content.ages.core.classical.description")
    color = (0, 255, 0, 0)
    order: int = 2
    progression_conditions = Conditions(conditions=[GlobalResearchCondition(tech=[IronWorking])])
    transition_image: str = "assets/images/ages/classical_transition.png"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )
