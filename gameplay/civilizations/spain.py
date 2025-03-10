from __future__ import annotations

from gameplay.civilization import Civilization
from managers.i18n import t_


class Spain(Civilization):
    name = t_("civilization.spain.name")
    description = t_("civilization.spain.description")
    city_names = [
        t_("cities.spain.madrid"),
        t_("cities.spain.barcelona"),
        t_("cities.spain.valencia"),
        t_("cities.spain.seville"),
        t_("cities.spain.zaragoza"),
        t_("cities.spain.malaga"),
        t_("cities.spain.murcia"),
        t_("cities.spain.palma"),
        t_("cities.spain.las_palmas"),
        t_("cities.spain.bilbao"),
        t_("cities.spain.alicante"),
        t_("cities.spain.cordoba"),
        t_("cities.spain.valladolid"),
        t_("cities.spain.vigo"),
        t_("cities.spain.gijon"),
        t_("cities.spain.lhospitalet_de_llobregat"),
        t_("cities.spain.acoruna"),
        t_("cities.spain.vitoria_gasteiz"),
        t_("cities.spain.granada"),
        t_("cities.spain.elche"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.charles_iii import CharlesIII
        from gameplay.leaders.charles_v import CharlesV
        from gameplay.leaders.isabella import Isabella
        from gameplay.leaders.james import James
        from gameplay.leaders.philip import Philip

        self.add_leader(Isabella())
        self.add_leader(CharlesV())
        self.add_leader(CharlesIII())
        self.add_leader(James())
        self.add_leader(Philip())
