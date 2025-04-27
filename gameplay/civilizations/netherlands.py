from typing import Any

from gameplay.civilization import Civilization
from managers.i18n import t_


class Netherlands(Civilization):
    name = t_("civilization.netherlands.name")
    description = t_("civilization.netherlands.description")
    city_names = [
        t_("cities.netherlands.amsterdam"),
        t_("cities.netherlands.brussels"),
        t_("cities.netherlands.rotterdam"),
        t_("cities.netherlands.the_hague"),
        t_("cities.netherlands.antwerp"),
        t_("cities.netherlands.ghent"),
        t_("cities.netherlands.utrecht"),
        t_("cities.netherlands.eindhoven"),
        t_("cities.netherlands.tilburg"),
        t_("cities.netherlands.liege"),
        t_("cities.netherlands.groningen"),
        t_("cities.netherlands.charleroi"),
        t_("cities.netherlands.namur"),
        t_("cities.netherlands.breda"),
        t_("cities.netherlands.nijmegen"),
        t_("cities.netherlands.apeldoorn"),
        t_("cities.netherlands.haarlem"),
        t_("cities.netherlands.mons"),
        t_("cities.netherlands.luxembourg_city"),
        t_("cities.netherlands.enschede"),
    ]
    introduction = t_("civilization.netherlands.introduction")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "assets/placeholders/icon_small.png"

    def register_effects(self) -> None:
        pass

    def register_leaders(self) -> None:
        from gameplay.leaders.ambiorix import Ambiorix
        from gameplay.leaders.willem import William

        self.add_leader(leader=William())
        self.add_leader(leader=Ambiorix())
