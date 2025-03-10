from __future__ import annotations

from gameplay.civilization import Civilization
from managers.i18n import t_


class Egypt(Civilization):
    name = t_("civilization.egypt.name")
    description = t_("civilization.egypt.description")
    city_names = [
        t_("cities.egypt.cairo"),
        t_("cities.egypt.alexandria"),
        t_("cities.egypt.giza"),
        t_("cities.egypt.shubra_el_kheima"),
        t_("cities.egypt.port_said"),
        t_("cities.egypt.suez"),
        t_("cities.egypt.mansoura"),
        t_("cities.egypt.tanta"),
        t_("cities.egypt.asyut"),
        t_("cities.egypt.fayoum"),
        t_("cities.egypt.zagazig"),
        t_("cities.egypt.ismailia"),
        t_("cities.egypt.kafr_el_sheikh"),
        t_("cities.egypt.damietta"),
        t_("cities.egypt.luxor"),
        t_("cities.egypt.qena"),
        t_("cities.egypt.sohag"),
        t_("cities.egypt.beni_suef"),
        t_("cities.egypt.minya"),
        t_("cities.egypt.aswan"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.cleopatra import Cleopatra
        from gameplay.leaders.ramesses import Ramesses

        self.add_leader(Ramesses())
        self.add_leader(Cleopatra())
