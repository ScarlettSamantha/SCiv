from gameplay.civilization import Civilization
from managers.i18n import t_


class Korea(Civilization):
    name = t_("civilization.korea.name")
    description = t_("civilization.korea.description")
    city_names = [
        t_("cities.korea.seoul"),
        t_("cities.korea.busan"),
        t_("cities.korea.incheon"),
        t_("cities.korea.daegu"),
        t_("cities.korea.daejeon"),
        t_("cities.korea.gwangju"),
        t_("cities.korea.suwon"),
        t_("cities.korea.ulsan"),
        t_("cities.korea.changwon"),
        t_("cities.korea.goyang"),
        t_("cities.korea.yongin"),
        t_("cities.korea.cheongju"),
        t_("cities.korea.jeonju"),
        t_("cities.korea.ansan"),
        t_("cities.korea.cheonan"),
        t_("cities.korea.namyangju"),
        t_("cities.korea.hwaseong"),
        t_("cities.korea.bucheon"),
        t_("cities.korea.gyeongju"),
        t_("cities.korea.chuncheon"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.goi import Goi
        from gameplay.leaders.sejong import Sejong

        self.add_leader(Sejong())
        self.add_leader(Goi())
