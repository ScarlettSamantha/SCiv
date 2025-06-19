from typing import Any, List, Type

from gameplay.civic import Civic, CivicCondition
from gameplay.civics.core.subs._base import BaseCoreSubtree
from managers.i18n import t_


class Liberalism(BaseCoreSubtree):
    key = "core.culture.subtrees.liberalism"
    name = t_("content.culture.subtrees.core.liberalism.name")
    description = t_("content.culture.subtrees.core.liberalism.description")
    order = 8

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

    @classmethod
    def register_civics(cls) -> List[Type[Civic]]:
        from gameplay.civics.core.civil_liberties import CivilLiberties
        from gameplay.civics.core.free_market import FreeMarket
        from gameplay.civics.core.global_cooperation import GlobalCooperation
        from gameplay.civics.core.individual_rights import IndividualRights
        from gameplay.civics.core.representative_democracy import RepresentativeDemocracy
        from gameplay.civics.core.social_welfare import SocialWelfare

        individual_rights = IndividualRights
        individual_rights.tier = 0
        individual_rights.unlocks = [CivilLiberties]
        cls.add_civic(individual_rights)

        free_market = FreeMarket
        free_market.set_requirements([CivicCondition(individual_rights)])
        free_market.tier = 1
        free_market.unlocks = [CivilLiberties]
        cls.add_civic(free_market)

        civil_liberties = CivilLiberties
        civil_liberties.set_requirements([CivicCondition(individual_rights)])
        civil_liberties.tier = 1
        civil_liberties.unlocks = [SocialWelfare]
        cls.add_civic(civil_liberties)

        representative_democracy = RepresentativeDemocracy
        representative_democracy.set_requirements([CivicCondition(individual_rights)])
        representative_democracy.unlocks = [CivilLiberties]
        representative_democracy.tier = 1
        cls.add_civic(representative_democracy)

        social_welfare = SocialWelfare
        social_welfare.set_requirements([CivicCondition(free_market)])
        social_welfare.unlocks = [GlobalCooperation]
        social_welfare.tier = 2
        cls.add_civic(social_welfare)

        global_cooperation = GlobalCooperation
        global_cooperation.set_requirements([CivicCondition(representative_democracy)])
        global_cooperation.tier = 2
        cls.add_civic(global_cooperation)

        return [
            individual_rights,
            free_market,
            representative_democracy,
            social_welfare,
            civil_liberties,
            global_cooperation,
        ]
