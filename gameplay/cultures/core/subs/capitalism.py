from gameplay.cultures.core.subs._base import BaseCoreSubtree
from managers.i18n import _t


class Capitalism(BaseCoreSubtree):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.subtrees.capitalism",
            name=_t("content.culture.subtrees.core.capitalism.name"),
            description=_t("content.culture.subtrees.core.capitalism.description"),
            *args,
            **kwargs,
        )

    def register_civics(self):
        from gameplay.cultures.core.capital_accumulation import CapitalAccumulation
        from gameplay.cultures.core.entrepreneurship import Entrepreneurship
        from gameplay.cultures.core.free_trade import FreeTrade
        from gameplay.cultures.core.market_competition import MarketCompetition
        from gameplay.cultures.core.minimal_regulation import MinimalRegulation
        from gameplay.cultures.core.private_property import PrivateProperty
        from system.requires import RequiresCivicComplete

        private_property = PrivateProperty()
        self.add_civic(private_property)

        entrepreneurship = Entrepreneurship()
        entrepreneurship.requires = [RequiresCivicComplete(private_property)]
        self.add_civic(entrepreneurship)

        free_trade = FreeTrade()
        free_trade.requires = [RequiresCivicComplete(private_property)]
        self.add_civic(free_trade)

        minimal_regulation = MinimalRegulation()
        minimal_regulation.requires = [RequiresCivicComplete(entrepreneurship), RequiresCivicComplete(free_trade)]
        self.add_civic(minimal_regulation)

        capital_accumulation = CapitalAccumulation()
        capital_accumulation.requires = [RequiresCivicComplete(minimal_regulation)]
        self.add_civic(capital_accumulation)

        market_competition = MarketCompetition()
        market_competition.requires = [RequiresCivicComplete(capital_accumulation)]
        self.add_civic(market_competition)
