from typing import Any, List, Type

from gameplay.civic import Civic, CivicCondition
from gameplay.civics.core.subs._base import BaseCoreSubtree
from managers.i18n import t_


class Capitalism(BaseCoreSubtree):
    key = "core.culture.subtrees.capitalism"
    name = t_("content.culture.subtrees.core.capitalism.name")
    description = t_("content.culture.subtrees.core.capitalism.description")
    order = 10

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

    @classmethod
    def register_civics(cls) -> List[Type[Civic]]:
        from gameplay.civics.core.capital_accumulation import CapitalAccumulation
        from gameplay.civics.core.entrepreneurship import Entrepreneurship
        from gameplay.civics.core.free_trade import FreeTrade
        from gameplay.civics.core.market_competition import MarketCompetition
        from gameplay.civics.core.minimal_regulation import MinimalRegulation
        from gameplay.civics.core.private_property import PrivateProperty

        private_property = PrivateProperty
        private_property.tier = 0
        private_property.unlocks = [Entrepreneurship]
        cls.add_civic(private_property)

        entrepreneurship = Entrepreneurship
        entrepreneurship.set_requirements([CivicCondition(private_property)])
        entrepreneurship.tier = 1
        entrepreneurship.unlocks = [FreeTrade, MinimalRegulation]
        cls.add_civic(entrepreneurship)

        free_trade = FreeTrade
        free_trade.set_requirements([CivicCondition(entrepreneurship)])
        free_trade.tier = 2
        free_trade.unlocks = [MinimalRegulation, CapitalAccumulation]
        cls.add_civic(free_trade)

        minimal_regulation = MinimalRegulation
        minimal_regulation.set_requirements([CivicCondition(entrepreneurship), CivicCondition(free_trade)])
        minimal_regulation.tier = 3
        cls.add_civic(minimal_regulation)

        capital_accumulation = CapitalAccumulation
        capital_accumulation.set_requirements([CivicCondition(free_trade)])
        capital_accumulation.tier = 3
        capital_accumulation.unlocks = [MarketCompetition]
        cls.add_civic(capital_accumulation)

        market_competition = MarketCompetition
        market_competition.set_requirements([CivicCondition(capital_accumulation)])
        market_competition.tier = 4
        cls.add_civic(market_competition)

        return [
            private_property,
            entrepreneurship,
            free_trade,
            minimal_regulation,
            capital_accumulation,
            market_competition,
        ]
