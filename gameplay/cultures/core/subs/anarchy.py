from __future__ import annotations
from gameplay.cultures.core.subs._base import BaseCoreSubtree
from managers.i18n import _t


class Anarchy(BaseCoreSubtree):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.subtrees.anarchy",
            name=_t("content.culture.subtrees.core.anarchy.name"),
            description=_t("content.culture.subtrees.core.anarchy.description"),
            *args,
            **kwargs,
        )

    def register_civics(self):
        from gameplay.cultures.core.self_governance import SelfGovernance
        from gameplay.cultures.core.mutual_aid import MutualAid
        from gameplay.cultures.core.direct_action import DirectAction
        from gameplay.cultures.core.decentralization import Decentralization
        from gameplay.cultures.core.voluntary_associations import VoluntaryAssociations
        from gameplay.cultures.core.autonomy import Autonomy
        from openciv.engine.requires import RequiresCivicComplete

        self_governance = SelfGovernance()
        self.add_civic(self_governance)

        mutual_aid = MutualAid()
        mutual_aid.requires = [RequiresCivicComplete(self_governance)]
        self.add_civic(mutual_aid)

        direct_action = DirectAction()
        direct_action.requires = [RequiresCivicComplete(self_governance)]
        self.add_civic(direct_action)

        decentralization = Decentralization()
        decentralization.requires = [RequiresCivicComplete(mutual_aid), RequiresCivicComplete(direct_action)]
        self.add_civic(decentralization)

        voluntary_associations = VoluntaryAssociations()
        voluntary_associations.requires = [RequiresCivicComplete(decentralization)]
        self.add_civic(voluntary_associations)

        autonomy = Autonomy()
        autonomy.requires = [RequiresCivicComplete(voluntary_associations)]
        self.add_civic(autonomy)
