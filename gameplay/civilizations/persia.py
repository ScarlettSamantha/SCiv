from __future__ import annotations
from gameplay.civilization import Civilization

from managers.i18n import t_


class Persia(Civilization):
    def __init__(self):
        super().__init__(name=t_("civilization.persia.name"), description=t_("civilization.persia.description"))

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
