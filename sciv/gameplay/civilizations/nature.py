from typing import Any

from gameplay.civilization import Civilization
from gameplay.leaders.gaia import Gaia
from managers.i18n import t_


class Nature(Civilization):
    name = t_("civilization.nature.name")
    description = t_("civilization.nature.description")
    city_names = [
        t_("cities.nature.ge"),
    ]
    introduction = t_("civilization.nature.introduction")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/nature.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        self.add_leader(Gaia())
