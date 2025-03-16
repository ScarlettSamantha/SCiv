from gameplay.civilization import Civilization
from managers.i18n import t_


class Ussr(Civilization):
    name = t_("civilization.ussr.name")
    description = t_("civilization.ussr.description")
    city_names = [
        t_("cities.ussr.moscow"),
        t_("cities.ussr.leningrad"),
        t_("cities.ussr.tashkent"),
        t_("cities.ussr.baku"),
        t_("cities.ussr.minsk"),
        t_("cities.ussr.kharkov"),
        t_("cities.ussr.gorky"),
        t_("cities.ussr.novosibirsk"),
        t_("cities.ussr.sverdlovsk"),
        t_("cities.ussr.tbilisi"),
        t_("cities.ussr.kuibyshev"),
        t_("cities.ussr.omsk"),
        t_("cities.ussr.donetsk"),
        t_("cities.ussr.alma_ata"),
        t_("cities.ussr.chelyabinsk"),
        t_("cities.ussr.yerevan"),
        t_("cities.ussr.dnepropetrovsk"),
        t_("cities.ussr.kazan"),
        t_("cities.ussr.perm"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.gorbashov import Gorbashov
        from gameplay.leaders.lenin import Lenin
        from gameplay.leaders.peter import Peter

        self.add_leader(Lenin())
        self.add_leader(Gorbashov())
        self.add_leader(Peter())
