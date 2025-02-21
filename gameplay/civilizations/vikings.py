from __future__ import annotations
from gameplay.civilization import Civilization

from managers.i18n import t_


class Vikings(Civilization):
    name = t_("civilization.vikings.name")
    description = t_("civilization.vikings.description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.cnut import Cnut
        from gameplay.leaders.ragnar import Ragnar
        from gameplay.leaders.herald import Herald

        self.add_leader(Cnut())
        self.add_leader(Ragnar())
        self.add_leader(Herald())
