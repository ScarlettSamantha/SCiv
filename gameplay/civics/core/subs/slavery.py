from typing import List, Type

from gameplay.civic import Civic, CivicCondition
from gameplay.civics.core.subs._base import BaseCoreSubtree
from managers.i18n import t_


class Slavery(BaseCoreSubtree):
    key = "core.culture.subtrees.slavery"
    name = t_("content.culture.subtrees.core.slavery.name")
    description = t_("content.culture.subtrees.core.slavery.description")
    order = 4

    def __init__(self):
        super().__init__()

    @classmethod
    def register_civics(cls) -> List[Type[Civic]]:
        from gameplay.civics.core.economic_dependence import EconomicDependence
        from gameplay.civics.core.forced_labor import ForcedLabor
        from gameplay.civics.core.labor_exploitation import LaborExploitation
        from gameplay.civics.core.oppression import Oppression
        from gameplay.civics.core.ownership_rights import OwnershipRights
        from gameplay.civics.core.social_hierarchy import SocialHierarchy

        forced_labor = ForcedLabor
        forced_labor.tier = 0
        forced_labor.unlocks = [OwnershipRights]
        cls.add_civic(forced_labor)

        ownership_rights = OwnershipRights
        ownership_rights.add_requirement(CivicCondition(forced_labor))
        ownership_rights.tier = 1
        ownership_rights.unlocks = [SocialHierarchy]
        cls.add_civic(ownership_rights)

        labor_exploitation = LaborExploitation
        labor_exploitation.add_requirement(CivicCondition(forced_labor))
        labor_exploitation.tier = 1
        labor_exploitation.unlocks = [SocialHierarchy]
        cls.add_civic(labor_exploitation)

        social_hierarchy = SocialHierarchy
        social_hierarchy.add_requirement(CivicCondition(ownership_rights))
        social_hierarchy.add_requirement(CivicCondition(labor_exploitation))
        social_hierarchy.tier = 2
        social_hierarchy.unlocks = [Oppression]
        cls.add_civic(social_hierarchy)

        oppression = Oppression
        oppression.add_requirement(CivicCondition(social_hierarchy))
        oppression.tier = 3
        oppression.unlocks = [EconomicDependence]
        cls.add_civic(oppression)

        economic_dependence = EconomicDependence
        economic_dependence.add_requirement(CivicCondition(oppression))
        economic_dependence.tier = 4
        cls.add_civic(economic_dependence)

        return [
            forced_labor,
            ownership_rights,
            labor_exploitation,
            social_hierarchy,
            oppression,
            economic_dependence,
        ]
