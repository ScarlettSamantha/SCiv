from gameplay.civilization import Civilization
from managers.i18n import t_


class England(Civilization):
    name = t_("civilization.england.name")
    description = t_("civilization.england.description")
    city_names = [
        t_("cities.england.london"),
        t_("cities.england.birmingham"),
        t_("cities.england.manchester"),
        t_("cities.england.leeds"),
        t_("cities.england.sheffield"),
        t_("cities.england.liverpool"),
        t_("cities.england.bristol"),
        t_("cities.england.newcastle"),
        t_("cities.england.sunderland"),
        t_("cities.england.wolverhampton"),
        t_("cities.england.nottingham"),
        t_("cities.england.leicester"),
        t_("cities.england.coventry"),
        t_("cities.england.kingston_upon_hull"),
        t_("cities.england.stoke_on_trent"),
        t_("cities.england.bradford"),
        t_("cities.england.plymouth"),
        t_("cities.england.southampton"),
        t_("cities.england.reading"),
        t_("cities.england.derby"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.elizabeth import Elizabeth
        from gameplay.leaders.victoria import Victoria

        self.add_leader(Victoria())
        self.add_leader(Elizabeth())
