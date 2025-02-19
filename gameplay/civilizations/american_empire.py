from __future__ import annotations
from gameplay.civilization import Civilization

from managers.i18n import t_


class AmericanEmpire(Civilization):
    def __init__(self):
        super().__init__(
            name=t_("civilization.american_empire.name"), description=t_("civilization.american_empire.description")
        )

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.abraham_lincoln import AbrahamLincoln
        from gameplay.leaders.fdr import FDR
        from gameplay.leaders.kamehameha import Kamehameha
        from gameplay.leaders.sitting_bull import SittingBull

        self.add_leader(AbrahamLincoln())
        self.add_leader(FDR())
        self.add_leader(Kamehameha())
        self.add_leader(SittingBull())
