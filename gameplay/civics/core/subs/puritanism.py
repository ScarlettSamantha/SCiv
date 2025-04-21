from typing import List, Type

from gameplay.civic import Civic, CivicCondition
from gameplay.civics.core.subs._base import BaseCoreSubtree
from managers.i18n import t_


class Puritanism(BaseCoreSubtree):
    key = "core.culture.subtrees.puritanism"
    name = t_("content.culture.subtrees.core.puritanism.name")
    description = t_("content.culture.subtrees.core.puritanism.description")
    order = 5

    def __init__(self):
        super().__init__()

    @classmethod
    def register_civics(cls) -> List[Type[Civic]]:
        from gameplay.civics.core.community_surveillance import CommunitySurveillance
        from gameplay.civics.core.moral_legislation import MoralLegislation
        from gameplay.civics.core.moral_purity import MoralPurity
        from gameplay.civics.core.religious_discipline import ReligiousDiscipline
        from gameplay.civics.core.religious_governance import ReligiousGovernance
        from gameplay.civics.core.simplified_living import SimplifiedLiving

        religious_discipline = ReligiousDiscipline
        religious_discipline.tier = 0
        religious_discipline.unlocks = [MoralPurity]
        cls.add_civic(religious_discipline)

        moral_purity = MoralPurity
        moral_purity.add_requirement(CivicCondition(religious_discipline))
        moral_purity.tier = 1
        moral_purity.unlocks = [SimplifiedLiving]
        cls.add_civic(moral_purity)

        community_surveillance = CommunitySurveillance
        community_surveillance.add_requirement(CivicCondition(religious_discipline))
        community_surveillance.tier = 1
        community_surveillance.unlocks = [SimplifiedLiving]
        cls.add_civic(community_surveillance)

        simplified_living = SimplifiedLiving
        simplified_living.add_requirement(CivicCondition(moral_purity))
        simplified_living.add_requirement(CivicCondition(community_surveillance))
        simplified_living.tier = 2
        simplified_living.unlocks = [ReligiousGovernance]
        cls.add_civic(simplified_living)

        religious_governance = ReligiousGovernance
        religious_governance.add_requirement(CivicCondition(simplified_living))
        religious_governance.tier = 3
        religious_governance.unlocks = [MoralLegislation]
        cls.add_civic(religious_governance)

        moral_legislation = MoralLegislation
        moral_legislation.add_requirement(CivicCondition(religious_governance))
        moral_legislation.tier = 4
        cls.add_civic(moral_legislation)

        return [
            religious_discipline,
            moral_purity,
            community_surveillance,
            simplified_living,
            religious_governance,
            moral_legislation,
        ]
