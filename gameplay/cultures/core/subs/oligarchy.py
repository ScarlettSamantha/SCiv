from gameplay.cultures.core.subs._base import BaseCoreSubtree
from managers.i18n import _t


class Oligarchy(BaseCoreSubtree):
    def __init__(self):
        super().__init__(
            key="core.culture.subtrees.oligarchy",
            name=_t("content.culture.subtrees.core.oligarchy.name"),
            description=_t("content.culture.subtrees.core.oligarchy.description"),
        )

    def register_civics(self):
        from gameplay.cultures.core.economic_control import EconomicControl
        from gameplay.cultures.core.elite_rule import EliteRule
        from gameplay.cultures.core.exclusive_networks import ExclusiveNetworks
        from gameplay.cultures.core.limited_participation import LimitedParticipation
        from gameplay.cultures.core.political_manipulation import PoliticalManipulation
        from gameplay.cultures.core.wealth_accumulation import WealthAccumulation
        from system.requires import RequiresCivicComplete

        elite_rule = EliteRule()
        self.add_civic(elite_rule)

        economic_control = EconomicControl()
        economic_control.requires = [RequiresCivicComplete(elite_rule)]
        self.add_civic(economic_control)

        limited_participation = LimitedParticipation()
        limited_participation.requires = [RequiresCivicComplete(elite_rule)]
        self.add_civic(limited_participation)

        wealth_accumulation = WealthAccumulation()
        wealth_accumulation.requires = [
            RequiresCivicComplete(economic_control),
            RequiresCivicComplete(limited_participation),
        ]
        self.add_civic(wealth_accumulation)

        exclusive_networks = ExclusiveNetworks()
        exclusive_networks.requires = [RequiresCivicComplete(wealth_accumulation)]
        self.add_civic(exclusive_networks)

        political_manipulation = PoliticalManipulation()
        political_manipulation.requires = [RequiresCivicComplete(exclusive_networks)]
        self.add_civic(political_manipulation)
