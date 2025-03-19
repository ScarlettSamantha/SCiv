from gameplay.civilization import Civilization
from managers.i18n import t_


class France(Civilization):
    name = t_("civilization.france.name")
    description = t_("civilization.france.description")
    city_names = [
        t_("cities.france.paris"),
        t_("cities.france.marseille"),
        t_("cities.france.lyon"),
        t_("cities.france.toulouse"),
        t_("cities.france.nice"),
        t_("cities.france.nantes"),
        t_("cities.france.strasbourg"),
        t_("cities.france.montpellier"),
        t_("cities.france.bordeaux"),
        t_("cities.france.lille"),
        t_("cities.france.rennes"),
        t_("cities.france.reims"),
        t_("cities.france.le_havre"),
        t_("cities.france.saint_etienne"),
        t_("cities.france.toulon"),
        t_("cities.france.grenoble"),
        t_("cities.france.dijon"),
        t_("cities.france.angers"),
        t_("cities.france.nimes"),
        t_("cities.france.villeurbanne"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.charlemagne import Charlemagne
        from gameplay.leaders.de_gaulle import DeGaulle
        from gameplay.leaders.louis import Louis
        from gameplay.leaders.napoleon import Napoleon

        self.add_leader(Napoleon())
        self.add_leader(Charlemagne())
        self.add_leader(DeGaulle())
        self.add_leader(Louis())
