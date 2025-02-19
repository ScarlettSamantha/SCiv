from __future__ import annotations
from gameplay.civilization import Civilization

from managers.i18n import t_


class Japan(Civilization):
    def __init__(self):
        super().__init__(name=t_("civilization.japan.name"), description=t_("civilization.japan.description"))

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.tokugawa import Tokugawa
        from gameplay.leaders.meiji import Meiji
        from gameplay.leaders.taisho import Taisho

        self.add_leader(Tokugawa())
        self.add_leader(Meiji())
        self.add_leader(Taisho())
