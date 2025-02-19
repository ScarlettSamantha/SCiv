from __future__ import annotations
from gameplay.civilization import Civilization

from managers.i18n import t_


class England(Civilization):
    def __init__(self):
        super().__init__(name=t_("civilization.england.name"), description=t_("civilization.england.description"))

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.victoria import Victoria
        from gameplay.leaders.elizabeth import Elizabeth

        self.add_leader(Victoria())
        self.add_leader(Elizabeth())
