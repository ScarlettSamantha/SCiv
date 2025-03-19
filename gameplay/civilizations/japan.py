from gameplay.civilization import Civilization
from managers.i18n import t_


class Japan(Civilization):
    name = t_("civilization.japan.name")
    description = t_("civilization.japan.description")
    city_names = [
        t_("cities.japan.tokyo"),
        t_("cities.japan.yokohama"),
        t_("cities.japan.osaka"),
        t_("cities.japan.nagoya"),
        t_("cities.japan.sapporo"),
        t_("cities.japan.fukuoka"),
        t_("cities.japan.kobe"),
        t_("cities.japan.kyoto"),
        t_("cities.japan.kawasaki"),
        t_("cities.japan.saitama"),
        t_("cities.japan.hiroshima"),
        t_("cities.japan.sendai"),
        t_("cities.japan.kitakyushu"),
        t_("cities.japan.chiba"),
        t_("cities.japan.sakai"),
        t_("cities.japan.niigata"),
        t_("cities.japan.hamamatsu"),
        t_("cities.japan.kumamoto"),
        t_("cities.japan.sagamihara"),
        t_("cities.japan.shizuoka"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.meiji import Meiji
        from gameplay.leaders.taisho import Taisho
        from gameplay.leaders.tokugawa import Tokugawa

        self.add_leader(Tokugawa())
        self.add_leader(Meiji())
        self.add_leader(Taisho())
