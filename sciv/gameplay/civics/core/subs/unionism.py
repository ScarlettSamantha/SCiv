from typing import List, Type

from gameplay.civic import Civic, CivicCondition
from gameplay.civics.core.subs._base import BaseCoreSubtree
from managers.i18n import t_


class Unionism(BaseCoreSubtree):
    key = "core.culture.subtrees.unionism"
    name = t_("content.culture.subtrees.core.unionism.name")
    description = t_("content.culture.subtrees.core.unionism.description")
    order = 6

    def __init__(self):
        super().__init__()

    @classmethod
    def register_civics(cls) -> List[Type[Civic]]:
        from gameplay.civics.core.collective_security import CollectiveSecurity
        from gameplay.civics.core.cooperative_governance import CooperativeGovernance
        from gameplay.civics.core.cultural_exchange import CulturalExchange
        from gameplay.civics.core.economic_integration import EconomicIntegration
        from gameplay.civics.core.shared_sovereignty import SharedSovereignty
        from gameplay.civics.core.unified_policy import UnifiedPolicy

        cooperative_governance = CooperativeGovernance
        cooperative_governance.tier = 0
        cooperative_governance.unlocks = [SharedSovereignty]
        cls.add_civic(cooperative_governance)

        shared_sovereignty = SharedSovereignty
        shared_sovereignty.set_requirements([CivicCondition(cooperative_governance)])
        shared_sovereignty.tier = 1
        shared_sovereignty.unlocks = [EconomicIntegration]
        cls.add_civic(shared_sovereignty)

        economic_integration = EconomicIntegration
        economic_integration.set_requirements([CivicCondition(shared_sovereignty)])
        economic_integration.tier = 1
        economic_integration.unlocks = [CulturalExchange]
        cls.add_civic(economic_integration)

        cultural_exchange = CulturalExchange
        cultural_exchange.set_requirements([CivicCondition(economic_integration)])
        cultural_exchange.tier = 2
        cultural_exchange.unlocks = [CollectiveSecurity]
        cls.add_civic(cultural_exchange)

        collective_security = CollectiveSecurity
        collective_security.set_requirements([CivicCondition(cultural_exchange)])
        collective_security.tier = 3
        collective_security.unlocks = [UnifiedPolicy]
        cls.add_civic(collective_security)

        unified_policy = UnifiedPolicy
        unified_policy.set_requirements([CivicCondition(collective_security)])
        unified_policy.tier = 4
        cls.add_civic(unified_policy)

        return [
            cooperative_governance,
            shared_sovereignty,
            economic_integration,
            cultural_exchange,
            collective_security,
            unified_policy,
        ]
