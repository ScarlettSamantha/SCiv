from __future__ import annotations

from gameplay.civilization import Civilization

from managers.i18n import t_


class Spain(Civilization):
    name = t_("civilization.spain.name")
    description = t_("civilization.spain.description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.isabella import Isabella
        from gameplay.leaders.charles_v import CharlesV
        from gameplay.leaders.charles_iii import CharlesIII
        from gameplay.leaders.james import James
        from gameplay.leaders.phillip import Phillip

        self.add_leader(Isabella())
        self.add_leader(CharlesV())
        self.add_leader(CharlesIII())
        self.add_leader(James())
        self.add_leader(Phillip())
