from typing import List, Type

from gameplay.civic import Civic, CivicCondition
from gameplay.civics.core.subs._base import BaseCoreSubtree
from managers.i18n import t_


class Monarchy(BaseCoreSubtree):
    key = "core.culture.subtrees.monarchy"
    name = t_("content.culture.subtrees.core.monarchy.name")
    description = t_("content.culture.subtrees.core.monarchy.description")
    order = 3

    def __init__(self):
        super().__init__()

    @classmethod
    def register_civics(cls) -> List[Type[Civic]]:
        from gameplay.civics.core.centralized_authority import CentralizedAuthority
        from gameplay.civics.core.divine_right import DivineRight
        from gameplay.civics.core.feudal_obligations import FeudalObligations
        from gameplay.civics.core.hereditary_rule import HereditaryRule
        from gameplay.civics.core.nobility_system import NobilitySystem
        from gameplay.civics.core.royal_patronage import RoyalPatronage

        hereditary_rule = HereditaryRule
        hereditary_rule.tier = 0
        hereditary_rule.unlocks = [DivineRight]
        cls.add_civic(hereditary_rule)

        divine_right = DivineRight
        divine_right.set_requirements([CivicCondition(hereditary_rule)])
        divine_right.tier = 1
        divine_right.unlocks = [NobilitySystem]
        cls.add_civic(divine_right)

        nobility_system = NobilitySystem
        nobility_system.set_requirements([CivicCondition(divine_right)])
        nobility_system.tier = 2
        nobility_system.unlocks = [FeudalObligations]
        cls.add_civic(nobility_system)

        feudal_obligations = FeudalObligations
        feudal_obligations.set_requirements([CivicCondition(nobility_system)])
        feudal_obligations.tier = 3
        feudal_obligations.unlocks = [CentralizedAuthority]
        cls.add_civic(feudal_obligations)

        centralized_authority = CentralizedAuthority
        centralized_authority.set_requirements([CivicCondition(feudal_obligations)])
        centralized_authority.tier = 4
        centralized_authority.unlocks = [RoyalPatronage]
        cls.add_civic(centralized_authority)

        royal_patronage = RoyalPatronage
        royal_patronage.set_requirements([CivicCondition(centralized_authority)])
        royal_patronage.tier = 5
        cls.add_civic(royal_patronage)

        return [
            hereditary_rule,
            divine_right,
            nobility_system,
            feudal_obligations,
            centralized_authority,
            royal_patronage,
        ]
