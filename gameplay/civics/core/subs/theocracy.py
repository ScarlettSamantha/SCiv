from typing import Any, List, Type

from gameplay.civic import Civic, CivicCondition
from gameplay.civics.core.subs._base import BaseCoreSubtree
from managers.i18n import t_


class Theocracy(BaseCoreSubtree):
    key = "core.culture.subtrees.theocracy"
    name = t_("content.culture.subtrees.core.theocracy.name")
    description = t_("content.culture.subtrees.core.theocracy.description")
    order = 2

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

    @classmethod
    def register_civics(cls) -> List[Type[Civic]]:
        from gameplay.civics.core.clerical_rule import ClericalRule
        from gameplay.civics.core.divine_governance import DivineGovernance
        from gameplay.civics.core.faith_based_education import FaithBasedEducation
        from gameplay.civics.core.moral_policing import MoralPolicing
        from gameplay.civics.core.religious_law import ReligiousLaw
        from gameplay.civics.core.religious_unity import ReligiousUnity

        religious_law = ReligiousLaw
        religious_law.tier = 0
        religious_law.unlocks = [ClericalRule]
        cls.add_civic(religious_law)

        clerical_rule = ClericalRule
        clerical_rule.add_requirement(CivicCondition(religious_law))
        clerical_rule.tier = 1
        clerical_rule.unlocks = [FaithBasedEducation]
        cls.add_civic(clerical_rule)

        moral_policing = MoralPolicing
        moral_policing.add_requirement(CivicCondition(religious_law))
        moral_policing.tier = 1
        moral_policing.unlocks = [FaithBasedEducation]
        cls.add_civic(moral_policing)

        faith_based_education = FaithBasedEducation
        faith_based_education.add_requirement(CivicCondition(clerical_rule))
        faith_based_education.add_requirement(CivicCondition(moral_policing))
        faith_based_education.tier = 2
        faith_based_education.unlocks = [DivineGovernance]
        cls.add_civic(faith_based_education)

        divine_governance = DivineGovernance
        divine_governance.add_requirement(CivicCondition(faith_based_education))
        divine_governance.tier = 3
        divine_governance.unlocks = [ReligiousUnity]
        cls.add_civic(divine_governance)

        religious_unity = ReligiousUnity
        religious_unity.add_requirement(CivicCondition(divine_governance))
        religious_unity.tier = 4
        cls.add_civic(religious_unity)

        return [
            religious_law,
            clerical_rule,
            moral_policing,
            faith_based_education,
            divine_governance,
            religious_unity,
        ]
