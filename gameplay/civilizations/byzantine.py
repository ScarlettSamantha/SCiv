from gameplay.civilization import Civilization
from managers.i18n import t_


class Byzantine(Civilization):
    name = t_("civilization.byzantine.name")
    description = t_("civilization.byzantine.description")
    city_names = [
        t_("cities.byzantine.constantinople"),
        t_("cities.byzantine.antioch"),
        t_("cities.byzantine.alexandria"),
        t_("cities.byzantine.thessalonica"),
        t_("cities.byzantine.nicaea"),
        t_("cities.byzantine.trebizond"),
        t_("cities.byzantine.ephesus"),
        t_("cities.byzantine.nicomedia"),
        t_("cities.byzantine.athens"),
        t_("cities.byzantine.smyrna"),
        t_("cities.byzantine.philippopolis"),
        t_("cities.byzantine.adrianople"),
        t_("cities.byzantine.caesarea"),
        t_("cities.byzantine.laodicea"),
        t_("cities.byzantine.sinope"),
        t_("cities.byzantine.chersonesus"),
        t_("cities.byzantine.mistra"),
        t_("cities.byzantine.sardis"),
        t_("cities.byzantine.seleucia"),
        t_("cities.byzantine.hierapolis"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.constantine import Constantine
        from gameplay.leaders.justinian import Justinian

        self.add_leader(Justinian())
        self.add_leader(Constantine())
