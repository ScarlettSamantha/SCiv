from __future__ import annotations
from gameplay.civilization import Civilization

from managers.i18n import t_


class France(Civilization):
    name = t_("civilization.france.name")
    description = t_("civilization.france.description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.napoleon import Napoleon
        from gameplay.leaders.charlemagne import Charlemagne
        from gameplay.leaders.de_gaulle import DeGaulle
        from gameplay.leaders.louis import Louis

        self.add_leader(Napoleon())
        self.add_leader(Charlemagne())
        self.add_leader(DeGaulle())
        self.add_leader(Louis())
