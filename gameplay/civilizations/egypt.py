from __future__ import annotations
from gameplay.civilization import Civilization

from managers.i18n import t_


class Egypt(Civilization):
    name = t_("civilization.egypt.name")
    description = t_("civilization.egypt.description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.ramesses import Ramesses
        from gameplay.leaders.cleopatra import Cleopatra

        self.add_leader(Ramesses())
        self.add_leader(Cleopatra())
