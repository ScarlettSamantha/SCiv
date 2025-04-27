from typing import Any, List, Type

from gameplay.civic import Civic
from gameplay.civics.core.subs._base import BaseCoreSubtree
from gameplay.condition import CivicCondition
from managers.i18n import t_


class Anarchy(BaseCoreSubtree):
    key = "core.culture.subtrees.anarchy"
    name = t_("content.culture.subtrees.core.anarchy.name")
    description = t_("content.culture.subtrees.core.anarchy.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

    @classmethod
    def register_civics(cls) -> List[Type[Civic]]:
        from gameplay.civics.core.autonomy import Autonomy
        from gameplay.civics.core.decentralization import Decentralization
        from gameplay.civics.core.direct_action import DirectAction
        from gameplay.civics.core.mutual_aid import MutualAid
        from gameplay.civics.core.self_governance import SelfGovernance
        from gameplay.civics.core.voluntary_associations import VoluntaryAssociations

        self_governance = SelfGovernance
        self_governance.tier = 0
        self_governance.unlocks = [MutualAid]
        cls.add_civic(self_governance)

        mutual_aid = MutualAid
        mutual_aid.add_requirement(CivicCondition(self_governance))
        mutual_aid.unlocks = [DirectAction, Decentralization]
        mutual_aid.tier = 1
        cls.add_civic(mutual_aid)

        direct_action = DirectAction
        direct_action.add_requirement(CivicCondition(self_governance))
        direct_action.unlocks = [Decentralization]
        direct_action.tier = 1
        cls.add_civic(direct_action)

        decentralization = Decentralization
        decentralization.add_requirement(CivicCondition(mutual_aid))
        decentralization.add_requirement(CivicCondition(direct_action))
        decentralization.tier = 2
        decentralization.unlocks = [VoluntaryAssociations]
        cls.add_civic(decentralization)

        voluntary_associations = VoluntaryAssociations
        voluntary_associations.add_requirement(CivicCondition(decentralization))
        voluntary_associations.tier = 3
        voluntary_associations.unlocks = [Autonomy]
        cls.add_civic(voluntary_associations)

        autonomy = Autonomy
        autonomy.add_requirement(CivicCondition(decentralization))
        autonomy.tier = 4
        cls.add_civic(autonomy)

        return [self_governance, mutual_aid, direct_action, decentralization, voluntary_associations, autonomy]
