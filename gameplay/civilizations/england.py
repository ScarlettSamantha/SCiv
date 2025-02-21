from __future__ import annotations
from gameplay.civilization import Civilization

from managers.i18n import t_


class England(Civilization):
    name = t_("civilization.england.name")
    description = t_("civilization.england.description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.victoria import Victoria
        from gameplay.leaders.elizabeth import Elizabeth

        self.add_leader(Victoria())
        self.add_leader(Elizabeth())
