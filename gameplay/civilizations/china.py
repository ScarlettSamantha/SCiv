from __future__ import annotations

from gameplay.civilization import Civilization

from managers.i18n import t_


class China(Civilization):
    name = t_("civilization.china.name")
    description = t_("civilization.china.description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.qin_shi_huang import QinShiHuang
        from gameplay.leaders.kublai import Kublai

        self.add_leader(QinShiHuang())
        self.add_leader(Kublai())
