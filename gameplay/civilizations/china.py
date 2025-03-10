from __future__ import annotations

from gameplay.civilization import Civilization
from managers.i18n import t_


class China(Civilization):
    name = t_("civilization.china.name")
    description = t_("civilization.china.description")
    city_names = [
        t_("cities.china.shanghai"),
        t_("cities.china.beijing"),
        t_("cities.china.chongqing"),
        t_("cities.china.tianjin"),
        t_("cities.china.guangzhou"),
        t_("cities.china.shenzhen"),
        t_("cities.china.chengdu"),
        t_("cities.china.nanjing"),
        t_("cities.china.wuhan"),
        t_("cities.china.xian"),
        t_("cities.china.hangzhou"),
        t_("cities.china.harbin"),
        t_("cities.china.suzhou"),
        t_("cities.china.shenyang"),
        t_("cities.china.qingdao"),
        t_("cities.china.dalian"),
        t_("cities.china.zhengzhou"),
        t_("cities.china.jinan"),
        t_("cities.china.changsha"),
        t_("cities.china.kunming"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.kublai import Kublai
        from gameplay.leaders.qin_shi_huang import QinShiHuang

        self.add_leader(QinShiHuang())
        self.add_leader(Kublai())
