from gameplay.civilization import Civilization
from managers.i18n import t_


class Vikings(Civilization):
    name = t_("civilization.vikings.name")
    description = t_("civilization.vikings.description")
    city_names = [
        t_("cities.vikings.hedeby"),
        t_("cities.vikings.kaupang"),
        t_("cities.vikings.birka"),
        t_("cities.vikings.ribe"),
        t_("cities.vikings.dublin"),
        t_("cities.vikings.jelling"),
        t_("cities.vikings.york"),
        t_("cities.vikings.roskilde"),
        t_("cities.vikings.lejre"),
        t_("cities.vikings.trelleborg"),
        t_("cities.vikings.uppsala"),
        t_("cities.vikings.trondheim"),
        t_("cities.vikings.oslo"),
        t_("cities.vikings.sigtuna"),
        t_("cities.vikings.aarhus"),
        t_("cities.vikings.lund"),
        t_("cities.vikings.vasteras"),
        t_("cities.vikings.viborg"),
        t_("cities.vikings.stavanger"),
        t_("cities.vikings.reykjavik"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.cnut import Cnut
        from gameplay.leaders.herald import Herald
        from gameplay.leaders.ragnar import Ragnar

        self.add_leader(Cnut())
        self.add_leader(Ragnar())
        self.add_leader(Herald())
