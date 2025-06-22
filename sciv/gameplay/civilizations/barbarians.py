from typing import Any

from gameplay.civilization import Civilization
from gameplay.leaders.alboin import Alboin
from gameplay.leaders.arminius import Arminius
from gameplay.leaders.boiorix import Boiorix
from gameplay.leaders.boudicca import Boudicca
from gameplay.leaders.gaiseric import Gaiseric
from gameplay.leaders.vidigoia import Vidigoia
from managers.i18n import t_


class Barbarians(Civilization):
    name = t_("civilization.barbarians.name")
    description = t_("civilization.barbarians.description")
    city_names = [
        t_("cities.barbarians.teutoburg"),
        t_("cities.barbarians.cherusca"),
        t_("cities.barbarians.vandalia"),
        t_("cities.barbarians.gothhaven"),
        t_("cities.barbarians.cimbriholm"),
        t_("cities.barbarians.ravenhold"),
        t_("cities.barbarians.wolfshollow"),
        t_("cities.barbarians.spearpoint"),
        t_("cities.barbarians.bloodrock"),
        t_("cities.barbarians.broken_spear"),
        t_("cities.barbarians.stormpeak"),
        t_("cities.barbarians.shadowfen"),
        t_("cities.barbarians.howling_vale"),
        t_("cities.barbarians.ashenfield"),
        t_("cities.barbarians.redmarsh"),
    ]
    introduction = t_("civilization.barbarians.introduction")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/barbarians.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        self.add_leader(Alboin())
        self.add_leader(Arminius())
        self.add_leader(Boiorix())
        self.add_leader(Boudicca())
        self.add_leader(Gaiseric())
        self.add_leader(Vidigoia())
