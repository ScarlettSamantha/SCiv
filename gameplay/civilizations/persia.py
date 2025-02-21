from __future__ import annotations
from gameplay.civilization import Civilization

from managers.i18n import t_


class Persia(Civilization):
    name = t_("civilization.persia.name")
    description = t_("civilization.persia.description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.darius import Darius
        from gameplay.leaders.xerxes import Xerxes
        from gameplay.leaders.nebuchadnezzar import Nebuchadnezzar

        self.add_leader(Darius())
        self.add_leader(Xerxes())
        self.add_leader(Nebuchadnezzar())
