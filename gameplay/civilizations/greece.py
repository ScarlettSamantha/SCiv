from __future__ import annotations
from gameplay.civilization import Civilization

from managers.i18n import t_


class Greece(Civilization):
    def __init__(self):
        super().__init__(name=t_("civilization.greece.name"), description=t_("civilization.greece.description"))

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.leonidas import Leonidas
        from gameplay.leaders.alexander import Alexander

        self.add_leader(Leonidas())
        self.add_leader(Alexander())
