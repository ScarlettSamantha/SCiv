from __future__ import annotations
from gameplay.civilization import Civilization

from managers.i18n import t_


class Ottoman(Civilization):
    name = t_("civilization.ottoman.name")
    description = t_("civilization.ottoman.description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.attaturk import Attaturk
        from gameplay.leaders.suleiman import Suleiman

        self.add_leader(Attaturk())
        self.add_leader(Suleiman())
