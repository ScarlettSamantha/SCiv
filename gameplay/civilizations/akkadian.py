from __future__ import annotations
from gameplay.civilization import Civilization

from managers.i18n import t_


class Akkadian(Civilization):
    def __init__(self):
        super().__init__(name=t_("civilization.akkadian.name"), description=t_("civilization.akkadian.description"))

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.sargon import Sargon
        from gameplay.leaders.naram_sin import NaramSin

        self.add_leader(Sargon())
        self.add_leader(NaramSin())
