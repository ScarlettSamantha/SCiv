from gameplay.civilization import Civilization
from managers.i18n import t_


class Akkadian(Civilization):
    name = t_("civilization.akkadian.name")
    description = t_("civilization.akkadian.description")
    city_names = [
        t_("cities.akkadian.agade"),
        t_("cities.akkadian.ur"),
        t_("cities.akkadian.uruk"),
        t_("cities.akkadian.nippur"),
        t_("cities.akkadian.kish"),
        t_("cities.akkadian.lagash"),
        t_("cities.akkadian.eridu"),
        t_("cities.akkadian.sippar"),
        t_("cities.akkadian.shuruppak"),
        t_("cities.akkadian.isin"),
        t_("cities.akkadian.larsa"),
        t_("cities.akkadian.adab"),
        t_("cities.akkadian.eshnunna"),
        t_("cities.akkadian.mari"),
        t_("cities.akkadian.der"),
        t_("cities.akkadian.bad_tibira"),
        t_("cities.akkadian.umma"),
        t_("cities.akkadian.zabala"),
        t_("cities.akkadian.akkad"),
        t_("cities.akkadian.akshak"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.naram_sin import NaramSin
        from gameplay.leaders.sargon import Sargon

        self.add_leader(Sargon())
        self.add_leader(NaramSin())
