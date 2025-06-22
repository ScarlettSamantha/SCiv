from typing import Any, List, Type

from gameplay.civic import Civic, CivicCondition
from gameplay.civics.core.subs._base import BaseCoreSubtree
from managers.i18n import t_


class Fascism(BaseCoreSubtree):
    key = "core.culture.subtrees.facism"
    name = t_("content.culture.subtrees.core.facism.name")
    description = t_("content.culture.subtrees.core.facism.description")
    order = 5

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

    @classmethod
    def register_civics(cls) -> List[Type[Civic]]:
        from gameplay.civics.core.corporate_state import CorporateState
        from gameplay.civics.core.leader_worship import LeaderWorship
        from gameplay.civics.core.militarization import Militarization
        from gameplay.civics.core.national_purity import NationalPurity
        from gameplay.civics.core.state_propaganda import StatePropaganda
        from gameplay.civics.core.totalitarian_control import TotalitarianControl

        totalitarian_control = TotalitarianControl
        totalitarian_control.tier = 0
        totalitarian_control.unlocks = [StatePropaganda]
        cls.add_civic(totalitarian_control)

        state_propaganda = StatePropaganda
        state_propaganda.set_requirements([CivicCondition(totalitarian_control)])
        state_propaganda.tier = 1
        state_propaganda.unlocks = [Militarization, CorporateState]
        cls.add_civic(state_propaganda)

        militarization = Militarization
        militarization.set_requirements([CivicCondition(state_propaganda)])
        militarization.tier = 2
        militarization.unlocks = [LeaderWorship]
        cls.add_civic(militarization)

        corporate_state = CorporateState
        corporate_state.set_requirements([CivicCondition(state_propaganda)])
        corporate_state.tier = 2
        corporate_state.unlocks = [NationalPurity]
        cls.add_civic(corporate_state)

        national_purity = NationalPurity
        national_purity.set_requirements([CivicCondition(corporate_state)])
        national_purity.tier = 3
        national_purity.unlocks = [LeaderWorship]
        cls.add_civic(national_purity)

        leader_worship = LeaderWorship
        leader_worship.set_requirements([CivicCondition(militarization)])
        leader_worship.tier = 3
        cls.add_civic(leader_worship)

        return [
            totalitarian_control,
            state_propaganda,
            militarization,
            corporate_state,
            national_purity,
            leader_worship,
        ]
