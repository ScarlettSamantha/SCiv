from __future__ import annotations
from gameplay.civilization import Civilization

from managers.i18n import t_


class Rome(Civilization):
    def __init__(self):
        super().__init__(name=t_("civilization.rome.name"), description=t_("civilization.rome.description"))

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.ceasar import Ceasar
        from gameplay.leaders.augustus import Augustus

        self.add_leader(Ceasar())
        self.add_leader(Augustus())
