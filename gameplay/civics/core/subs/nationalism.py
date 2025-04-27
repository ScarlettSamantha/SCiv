from typing import Any, List, Type

from gameplay.civic import Civic, CivicCondition
from gameplay.civics.core.subs._base import BaseCoreSubtree
from managers.i18n import t_


class Nationalism(BaseCoreSubtree):
    key = "core.culture.subtrees.nationalism"
    name = t_("content.culture.subtrees.core.nationalism.name")
    description = t_("content.culture.subtrees.core.nationalism.description")
    order = 5

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

    @classmethod
    def register_civics(cls) -> List[Type[Civic]]:
        from gameplay.civics.core.cultural_preservation import CulturalPreservation
        from gameplay.civics.core.economic_nationalism import EconomicNationalism
        from gameplay.civics.core.military_strength import MilitaryStrength
        from gameplay.civics.core.national_sovereignty import NationalSovereignty
        from gameplay.civics.core.national_unity import NationalUnity
        from gameplay.civics.core.patriotic_education import PatrioticEducation

        patriotic_education = PatrioticEducation
        patriotic_education.tier = 0
        patriotic_education.unlocks = [CulturalPreservation]
        cls.add_civic(patriotic_education)

        cultural_preservation = CulturalPreservation
        cultural_preservation.add_requirement(CivicCondition(patriotic_education))
        cultural_preservation.tier = 1
        cultural_preservation.unlocks = [EconomicNationalism]
        cls.add_civic(cultural_preservation)

        economic_nationalism = EconomicNationalism
        economic_nationalism.add_requirement(CivicCondition(patriotic_education))
        economic_nationalism.tier = 1
        economic_nationalism.unlocks = [NationalSovereignty]
        cls.add_civic(economic_nationalism)

        military_strength = MilitaryStrength
        military_strength.add_requirement(CivicCondition(cultural_preservation))
        military_strength.tier = 2
        military_strength.unlocks = [NationalSovereignty]
        cls.add_civic(military_strength)

        national_sovereignty = NationalSovereignty
        national_sovereignty.add_requirement(CivicCondition(economic_nationalism))
        national_sovereignty.add_requirement(CivicCondition(military_strength))
        national_sovereignty.tier = 3
        national_sovereignty.unlocks = [NationalUnity]
        cls.add_civic(national_sovereignty)

        national_unity = NationalUnity
        national_unity.add_requirement(CivicCondition(national_sovereignty))
        national_unity.tier = 4
        cls.add_civic(national_unity)

        return [
            patriotic_education,
            cultural_preservation,
            economic_nationalism,
            military_strength,
            national_sovereignty,
            national_unity,
        ]
