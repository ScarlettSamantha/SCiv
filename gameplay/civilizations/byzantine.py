from __future__ import annotations
from gameplay.civilization import Civilization
from managers.i18n import t_


class Byzantine(Civilization):
    name = t_("civilization.byzantine.name")
    description = t_("civilization.byzantine.description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.justinian import Justinian
        from gameplay.leaders.constantine import Constantine

        self.add_leader(Justinian())
        self.add_leader(Constantine())
