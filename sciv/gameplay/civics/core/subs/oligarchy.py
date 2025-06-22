from typing import List, Type

from gameplay.civic import Civic, CivicCondition
from gameplay.civics.core.subs._base import BaseCoreSubtree
from managers.i18n import t_


class Oligarchy(BaseCoreSubtree):
    key = "core.culture.subtrees.oligarchy"
    name = t_("content.culture.subtrees.core.oligarchy.name")
    description = t_("content.culture.subtrees.core.oligarchy.description")
    order = 9

    def __init__(self):
        super().__init__()

    @classmethod
    def register_civics(cls) -> List[Type[Civic]]:
        from gameplay.civics.core.economic_control import EconomicControl
        from gameplay.civics.core.elite_rule import EliteRule
        from gameplay.civics.core.exclusive_networks import ExclusiveNetworks
        from gameplay.civics.core.limited_participation import LimitedParticipation
        from gameplay.civics.core.political_manipulation import PoliticalManipulation
        from gameplay.civics.core.wealth_accumulation import WealthAccumulation

        elite_rule = EliteRule
        elite_rule.tier = 0
        elite_rule.unlocks = [EconomicControl]
        cls.add_civic(elite_rule)

        economic_control = EconomicControl
        economic_control.set_requirements([CivicCondition(elite_rule)])
        economic_control.tier = 1
        economic_control.unlocks = [WealthAccumulation]
        cls.add_civic(economic_control)

        limited_participation = LimitedParticipation
        limited_participation.set_requirements([CivicCondition(elite_rule)])
        limited_participation.tier = 1
        limited_participation.unlocks = [WealthAccumulation]
        cls.add_civic(limited_participation)

        wealth_accumulation = WealthAccumulation
        wealth_accumulation.set_requirements([CivicCondition(economic_control), CivicCondition(limited_participation)])
        wealth_accumulation.tier = 2
        wealth_accumulation.unlocks = [ExclusiveNetworks]
        cls.add_civic(wealth_accumulation)

        exclusive_networks = ExclusiveNetworks
        exclusive_networks.set_requirements([CivicCondition(wealth_accumulation)])
        exclusive_networks.tier = 3
        exclusive_networks.unlocks = [PoliticalManipulation]
        cls.add_civic(exclusive_networks)

        political_manipulation = PoliticalManipulation
        political_manipulation.set_requirements([CivicCondition(exclusive_networks)])
        political_manipulation.tier = 4
        cls.add_civic(political_manipulation)

        return [
            elite_rule,
            economic_control,
            limited_participation,
            wealth_accumulation,
            exclusive_networks,
            political_manipulation,
        ]
