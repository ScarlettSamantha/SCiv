from typing import List, Type

from gameplay.civic import Civic, CivicCondition
from gameplay.civics.core.subs._base import BaseCoreSubtree
from managers.i18n import t_


class Corporatocracy(BaseCoreSubtree):
    key = "core.culture.subtrees.corporatocracy"
    name = t_("content.culture.subtrees.core.corporatocracy.name")
    description = t_("content.culture.subtrees.core.corporatocracy.description")
    order = 12

    def __init__(
        self,
    ):
        super().__init__()

    @classmethod
    def register_civics(cls) -> List[Type[Civic]]:
        from gameplay.civics.core.business_privileges import BusinessPrivileges
        from gameplay.civics.core.corporate_governance import CorporateGovernance
        from gameplay.civics.core.corporate_influence import CorporateInfluence
        from gameplay.civics.core.economic_focus import EconomicFocus
        from gameplay.civics.core.lobbying_power import LobbyingPower
        from gameplay.civics.core.regulatory_capture import RegulatoryCapture

        corporate_influence = CorporateInfluence
        corporate_influence.tier = 0
        corporate_influence.unlocks = [LobbyingPower]
        cls.add_civic(corporate_influence)

        lobbying_power = LobbyingPower
        lobbying_power.set_requirements([CivicCondition(corporate_influence)])
        lobbying_power.unlocks = [EconomicFocus]
        lobbying_power.tier = 1
        cls.add_civic(lobbying_power)

        business_privileges = BusinessPrivileges
        business_privileges.set_requirements([CivicCondition(corporate_influence)])
        business_privileges.unlocks = [EconomicFocus]
        business_privileges.tier = 1
        cls.add_civic(business_privileges)

        economic_focus = EconomicFocus
        economic_focus.set_requirements([CivicCondition(business_privileges), CivicCondition(lobbying_power)])
        economic_focus.unlocks = [RegulatoryCapture]
        economic_focus.tier = 2
        cls.add_civic(economic_focus)

        regulatory_capture = RegulatoryCapture
        regulatory_capture.set_requirements([CivicCondition(economic_focus), CivicCondition(lobbying_power)])
        regulatory_capture.tier = 2
        regulatory_capture.unlocks = [CorporateGovernance]
        cls.add_civic(regulatory_capture)

        corporate_governance = CorporateGovernance
        corporate_governance.set_requirements([CivicCondition(economic_focus), CivicCondition(regulatory_capture)])
        corporate_governance.tier = 3
        cls.add_civic(corporate_governance)

        return [
            corporate_influence,
            lobbying_power,
            business_privileges,
            economic_focus,
            regulatory_capture,
            corporate_governance,
        ]
