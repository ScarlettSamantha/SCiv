from typing import Any, List, Type

from gameplay.civic import Civic, CivicCondition
from gameplay.civics.core.subs._base import BaseCoreSubtree
from managers.i18n import t_


class Socialism(BaseCoreSubtree):
    key = "core.culture.subtrees.socialism"
    name = t_("content.culture.subtrees.core.socialism.name")
    description = t_("content.culture.subtrees.core.socialism.description")
    order = 8

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

    @classmethod
    def register_civics(cls) -> List[Type[Civic]]:
        from gameplay.civics.core.collective_ownership import CollectiveOwnership
        from gameplay.civics.core.free_education import FreeEducation
        from gameplay.civics.core.social_equality import SocialEquality
        from gameplay.civics.core.state_planning import StatePlanning
        from gameplay.civics.core.universal_healthcare import UniversalHealthcare
        from gameplay.civics.core.workers_rights import WorkersRights

        collective_ownership = CollectiveOwnership
        collective_ownership.tier = 0
        collective_ownership.unlocks = [WorkersRights]
        cls.add_civic(collective_ownership)

        workers_rights = WorkersRights
        workers_rights.set_requirements([CivicCondition(collective_ownership)])
        workers_rights.tier = 1
        workers_rights.unlocks = [FreeEducation]
        cls.add_civic(workers_rights)

        free_education = FreeEducation
        free_education.set_requirements([CivicCondition(collective_ownership)])
        free_education.tier = 1
        free_education.unlocks = [SocialEquality]
        cls.add_civic(free_education)

        universal_healthcare = UniversalHealthcare
        universal_healthcare.set_requirements([CivicCondition(workers_rights)])
        universal_healthcare.tier = 2
        universal_healthcare.unlocks = [SocialEquality]
        cls.add_civic(universal_healthcare)

        social_equality = SocialEquality
        social_equality.set_requirements([CivicCondition(universal_healthcare), CivicCondition(free_education)])
        social_equality.tier = 3
        social_equality.unlocks = [StatePlanning]
        cls.add_civic(social_equality)

        state_planning = StatePlanning
        state_planning.set_requirements([CivicCondition(social_equality)])
        state_planning.tier = 4
        cls.add_civic(state_planning)

        return [
            collective_ownership,
            workers_rights,
            universal_healthcare,
            free_education,
            social_equality,
            state_planning,
        ]
