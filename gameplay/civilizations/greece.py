from gameplay.civilization import Civilization
from managers.i18n import t_


class Greece(Civilization):
    name = t_("civilization.greece.name")
    description = t_("civilization.greece.description")
    city_names = [
        t_("cities.greece.athens"),
        t_("cities.greece.thessaloniki"),
        t_("cities.greece.patras"),
        t_("cities.greece.heraklion"),
        t_("cities.greece.larissa"),
        t_("cities.greece.volos"),
        t_("cities.greece.rhodes"),
        t_("cities.greece.ioannina"),
        t_("cities.greece.chania"),
        t_("cities.greece.agrinio"),
        t_("cities.greece.chalcis"),
        t_("cities.greece.katerini"),
        t_("cities.greece.trikala"),
        t_("cities.greece.serres"),
        t_("cities.greece.lamia"),
        t_("cities.greece.alexandroupoli"),
        t_("cities.greece.xanthi"),
        t_("cities.greece.kavala"),
        t_("cities.greece.kalamata"),
        t_("cities.greece.veria"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.alexander import Alexander
        from gameplay.leaders.leonidas import Leonidas

        self.add_leader(Leonidas())
        self.add_leader(Alexander())
