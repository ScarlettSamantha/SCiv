from __future__ import annotations

from gameplay.civilization import Civilization
from managers.i18n import t_


class Persia(Civilization):
    name = t_("civilization.persia.name")
    description = t_("civilization.persia.description")
    city_names = [
        t_("cities.persia.tehran"),
        t_("cities.persia.mashhad"),
        t_("cities.persia.isfahan"),
        t_("cities.persia.karaj"),
        t_("cities.persia.tabriz"),
        t_("cities.persia.shiraz"),
        t_("cities.persia.qom"),
        t_("cities.persia.ahvaz"),
        t_("cities.persia.kermanshah"),
        t_("cities.persia.urmia"),
        t_("cities.persia.zahedan"),
        t_("cities.persia.rasht"),
        t_("cities.persia.hamadan"),
        t_("cities.persia.arak"),
        t_("cities.persia.yazd"),
        t_("cities.persia.ardabil"),
        t_("cities.persia.bandar_abbas"),
        t_("cities.persia.zanjan"),
        t_("cities.persia.sanandaj"),
        t_("cities.persia.kerman"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.darius import Darius
        from gameplay.leaders.nebuchadnezzar import Nebuchadnezzar
        from gameplay.leaders.xerxes import Xerxes

        self.add_leader(Darius())
        self.add_leader(Xerxes())
        self.add_leader(Nebuchadnezzar())
