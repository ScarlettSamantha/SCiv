from gameplay.civilization import Civilization
from managers.i18n import t_


class LowCountries(Civilization):
    name = t_("civilization.low_countries.name")
    description = t_("civilization.low_countries.description")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self) -> None:
        pass

    def register_leaders(self) -> None:
        from gameplay.leaders.willem import Willem
        from gameplay.leaders.ambiorix import Ambiorix

        self.add_leader(leader=Willem())
        self.add_leader(leader=Ambiorix())
