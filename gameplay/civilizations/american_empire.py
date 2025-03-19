from gameplay.civilization import Civilization
from managers.i18n import t_


class AmericanEmpire(Civilization):
    name = t_("civilization.american_empire.name")
    description = t_("civilization.american_empire.description")
    city_names = [
        t_("cities.american_empire.new_york"),
        t_("cities.american_empire.los_angeles"),
        t_("cities.american_empire.chicago"),
        t_("cities.american_empire.houston"),
        t_("cities.american_empire.phoenix"),
        t_("cities.american_empire.philadelphia"),
        t_("cities.american_empire.san_antonio"),
        t_("cities.american_empire.san_diego"),
        t_("cities.american_empire.dallas"),
        t_("cities.american_empire.san_jose"),
        t_("cities.american_empire.austin"),
        t_("cities.american_empire.jacksonville"),
        t_("cities.american_empire.fort_worth"),
        t_("cities.american_empire.columbus"),
        t_("cities.american_empire.charlotte"),
        t_("cities.american_empire.san_francisco"),
        t_("cities.american_empire.indianapolis"),
        t_("cities.american_empire.seattle"),
        t_("cities.american_empire.denver"),
        t_("cities.american_empire.washington"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
