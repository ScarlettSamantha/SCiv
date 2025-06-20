from typing import List, Type

from gameplay.civic import Civic, CivicCondition
from gameplay.civics.core.subs._base import BaseCoreSubtree
from managers.i18n import t_


class Dictatorship(BaseCoreSubtree):
    key = "core.culture.subtrees.dictatorship"
    name = t_("content.culture.subtrees.core.dictatorship.name")
    description = t_("content.culture.subtrees.core.dictatorship.description")
    order = 6

    def __init__(self):
        super().__init__()

    @classmethod
    def register_civics(cls) -> List[Type[Civic]]:
        from gameplay.civics.core.autocratic_rule import AutocraticRule
        from gameplay.civics.core.censorship import Censorship
        from gameplay.civics.core.centralized_power import CentralizedPower
        from gameplay.civics.core.propaganda import Propaganda
        from gameplay.civics.core.repression import Repression
        from gameplay.civics.core.state_surveillance import StateSurveillance

        autocratic_rule = AutocraticRule
        autocratic_rule.tier = 0
        autocratic_rule.unlocks = [StateSurveillance, Repression]
        cls.add_civic(autocratic_rule)

        state_surveillance = StateSurveillance
        state_surveillance.set_requirements([CivicCondition(autocratic_rule)])
        state_surveillance.unlocks = [Censorship]
        state_surveillance.tier = 1
        cls.add_civic(state_surveillance)

        censorship = Censorship
        censorship.set_requirements([CivicCondition(state_surveillance)])
        censorship.tier = 2
        censorship.unlocks = [Repression]
        cls.add_civic(censorship)

        repression = Repression
        repression.set_requirements([CivicCondition(autocratic_rule), CivicCondition(censorship)])
        repression.tier = 3
        repression.unlocks = [Propaganda]
        cls.add_civic(repression)

        propaganda = Propaganda
        propaganda.set_requirements([CivicCondition(repression)])
        propaganda.tier = 4
        propaganda.unlocks = [CentralizedPower]
        cls.add_civic(propaganda)

        centralized_power = CentralizedPower
        centralized_power.set_requirements([CivicCondition(propaganda)])
        centralized_power.tier = 5
        cls.add_civic(centralized_power)

        return [
            autocratic_rule,
            state_surveillance,
            censorship,
            repression,
            propaganda,
            centralized_power,
        ]
