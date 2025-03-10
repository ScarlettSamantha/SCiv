from gameplay.civilization import Civilization
from managers.i18n import t_


class LowCountries(Civilization):
    name = t_("civilization.low_countries.name")
    description = t_("civilization.low_countries.description")
    city_names = [
        t_("cities.low_countries.amsterdam"),
        t_("cities.low_countries.brussels"),
        t_("cities.low_countries.rotterdam"),
        t_("cities.low_countries.the_hague"),
        t_("cities.low_countries.antwerp"),
        t_("cities.low_countries.ghent"),
        t_("cities.low_countries.utrecht"),
        t_("cities.low_countries.eindhoven"),
        t_("cities.low_countries.tilburg"),
        t_("cities.low_countries.liege"),
        t_("cities.low_countries.groningen"),
        t_("cities.low_countries.charleroi"),
        t_("cities.low_countries.namur"),
        t_("cities.low_countries.breda"),
        t_("cities.low_countries.nijmegen"),
        t_("cities.low_countries.apeldoorn"),
        t_("cities.low_countries.haarlem"),
        t_("cities.low_countries.mons"),
        t_("cities.low_countries.luxembourg_city"),
        t_("cities.low_countries.enschede"),
    ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self) -> None:
        pass

    def register_leaders(self) -> None:
        from gameplay.leaders.ambiorix import Ambiorix
        from gameplay.leaders.willem import Willem

        self.add_leader(leader=Willem())
        self.add_leader(leader=Ambiorix())
