from __future__ import annotations
from gameplay.cultures.core.subs._base import BaseCoreSubtree
from managers.i18n import _t


class Fascism(BaseCoreSubtree):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.subtrees.facism",
            name=_t("content.culture.subtrees.core.facism.name"),
            description=_t("content.culture.subtrees.core.facism.description"),
            *args,
            **kwargs,
        )

    def register_civics(self):
        from gameplay.cultures.core.totalitarian_control import TotalitarianControl
        from gameplay.cultures.core.state_propaganda import StatePropaganda
        from gameplay.cultures.core.militarization import Militarization
        from gameplay.cultures.core.corporate_state import CorporateState
        from gameplay.cultures.core.national_purity import NationalPurity
        from gameplay.cultures.core.leader_worship import LeaderWorship
        from openciv.engine.requires import RequiresCivicComplete

        totalitarian_control = TotalitarianControl()
        self.add_civic(totalitarian_control)

        state_propaganda = StatePropaganda()
        state_propaganda.requires = [RequiresCivicComplete(totalitarian_control)]
        self.add_civic(state_propaganda)

        militarization = Militarization()
        militarization.requires = [RequiresCivicComplete(state_propaganda)]
        self.add_civic(militarization)

        corporate_state = CorporateState()
        corporate_state.requires = [RequiresCivicComplete(militarization)]
        self.add_civic(corporate_state)

        national_purity = NationalPurity()
        national_purity.requires = [RequiresCivicComplete(corporate_state)]
        self.add_civic(national_purity)

        leader_worship = LeaderWorship()
        leader_worship.requires = [RequiresCivicComplete(national_purity)]
        self.add_civic(leader_worship)
