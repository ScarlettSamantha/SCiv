from typing import Any, List, Type

from gameplay.civic import Civic, CivicCondition
from gameplay.civics.core.subs._base import BaseCoreSubtree
from managers.i18n import t_


class Communism(BaseCoreSubtree):
    key = "core.culture.subtrees.communism"
    name = t_("content.culture.subtrees.core.communism.name")
    description = t_("content.culture.subtrees.core.communism.description")
    order = 9

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

    @classmethod
    def register_civics(cls) -> List[Type[Civic]]:
        from gameplay.civics.core.centralized_economy import CentralizedEconomy
        from gameplay.civics.core.class_abolition import ClassAbolition
        from gameplay.civics.core.collectivized_agriculture import CollectivizedAgriculture
        from gameplay.civics.core.communal_living import CommunalLiving
        from gameplay.civics.core.international_solidarity import InternationalSolidarity
        from gameplay.civics.core.proletarian_dictatorship import ProletarianDictatorship

        class_abolition = ClassAbolition
        class_abolition.tier = 0
        class_abolition.unlocks = [CommunalLiving]
        cls.add_civic(class_abolition)

        communal_living = CommunalLiving
        communal_living.set_requirements([CivicCondition(class_abolition)])
        communal_living.unlocks = [CentralizedEconomy, CollectivizedAgriculture]
        communal_living.tier = 1
        cls.add_civic(communal_living)

        centralized_economy = CentralizedEconomy
        centralized_economy.set_requirements([CivicCondition(communal_living)])
        centralized_economy.unlocks = [ProletarianDictatorship]
        centralized_economy.tier = 2
        cls.add_civic(centralized_economy)

        proletarian_dictatorship = ProletarianDictatorship
        proletarian_dictatorship.set_requirements([CivicCondition(centralized_economy)])
        proletarian_dictatorship.unlocks = [CollectivizedAgriculture]
        proletarian_dictatorship.tier = 3
        cls.add_civic(proletarian_dictatorship)

        collectivized_agriculture = CollectivizedAgriculture
        collectivized_agriculture.set_requirements(
            [CivicCondition(proletarian_dictatorship), CivicCondition(communal_living)]
        )
        collectivized_agriculture.unlocks = [InternationalSolidarity]
        collectivized_agriculture.tier = 4
        cls.add_civic(collectivized_agriculture)

        international_solidarity = InternationalSolidarity
        international_solidarity.set_requirements([CivicCondition(collectivized_agriculture)])
        international_solidarity.tier = 5
        cls.add_civic(international_solidarity)

        return [
            class_abolition,
            communal_living,
            centralized_economy,
            proletarian_dictatorship,
            collectivized_agriculture,
            international_solidarity,
        ]
