from gameplay.civilization import Civilization
from managers.i18n import t_


class Ottoman(Civilization):
    name = t_("civilization.ottoman.name")
    description = t_("civilization.ottoman.description")
    city_names = [
        t_("cities.ottoman.constantinople"),
        t_("cities.ottoman.cairo"),
        t_("cities.ottoman.baghdad"),
        t_("cities.ottoman.damascus"),
        t_("cities.ottoman.aleppo"),
        t_("cities.ottoman.bursa"),
        t_("cities.ottoman.izmir"),
        t_("cities.ottoman.salonica"),
        t_("cities.ottoman.adrianople"),
        t_("cities.ottoman.tripoli"),
        t_("cities.ottoman.mecca"),
        t_("cities.ottoman.medina"),
        t_("cities.ottoman.jerusalem"),
        t_("cities.ottoman.mosul"),
        t_("cities.ottoman.belgrade"),
        t_("cities.ottoman.tunis"),
        t_("cities.ottoman.algiers"),
        t_("cities.ottoman.sarajevo"),
        t_("cities.ottoman.skopje"),
        t_("cities.ottoman.tabriz"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.attaturk import Attaturk
        from gameplay.leaders.suleiman import Suleiman

        self.add_leader(Attaturk())
        self.add_leader(Suleiman())
