from __future__ import annotations
from gameplay.civilization import Civilization

from managers.i18n import t_


class Ussr(Civilization):
    name = t_("civilization.ussr.name")
    description = t_("civilization.ussr.description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.lenin import Lenin
        from gameplay.leaders.gorbashov import Gorbashov
        from gameplay.leaders.peter import Peter

        self.add_leader(Lenin())
        self.add_leader(Gorbashov())
        self.add_leader(Peter())
