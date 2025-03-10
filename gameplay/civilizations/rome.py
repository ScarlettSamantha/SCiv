from __future__ import annotations

from gameplay.civilization import Civilization
from managers.i18n import t_


class Rome(Civilization):
    name = t_("civilization.rome.name")
    description = t_("civilization.rome.description")
    city_names = [
        t_("cities.rome.rome"),
        t_("cities.rome.alexandria"),
        t_("cities.rome.antioch"),
        t_("cities.rome.carthage"),
        t_("cities.rome.constantinople"),
        t_("cities.rome.ephesus"),
        t_("cities.rome.pergamum"),
        t_("cities.rome.smyrna"),
        t_("cities.rome.mediolanum"),
        t_("cities.rome.thessalonica"),
        t_("cities.rome.lugdunum"),
        t_("cities.rome.londinium"),
        t_("cities.rome.colonia_agrippina"),
        t_("cities.rome.gades"),
        t_("cities.rome.hispalis"),
        t_("cities.rome.tarraco"),
        t_("cities.rome.massilia"),
        t_("cities.rome.brundisium"),
        t_("cities.rome.arelate"),
        t_("cities.rome.emerita_augusta"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.augustus import Augustus
        from gameplay.leaders.ceasar import Ceasar

        self.add_leader(Ceasar())
        self.add_leader(Augustus())
