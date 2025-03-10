from __future__ import annotations

from gameplay.civilization import Civilization
from managers.i18n import t_


class Germany(Civilization):
    name = t_("civilization.germany.name")
    description = t_("civilization.germany.description")
    city_names = [
        t_("cities.germany.berlin"),
        t_("cities.germany.hamburg"),
        t_("cities.germany.munich"),
        t_("cities.germany.cologne"),
        t_("cities.germany.frankfurt"),
        t_("cities.germany.stuttgart"),
        t_("cities.germany.dusseldorf"),
        t_("cities.germany.leipzig"),
        t_("cities.germany.dortmund"),
        t_("cities.germany.essen"),
        t_("cities.germany.bremen"),
        t_("cities.germany.dresden"),
        t_("cities.germany.hanover"),
        t_("cities.germany.nuremberg"),
        t_("cities.germany.duisburg"),
        t_("cities.germany.bochum"),
        t_("cities.germany.wuppertal"),
        t_("cities.germany.bielefeld"),
        t_("cities.germany.bonn"),
        t_("cities.germany.munster"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.otto import Otto
        from gameplay.leaders.wilhelm import Wilhelm

        self.add_leader(Otto())
        self.add_leader(Wilhelm())
