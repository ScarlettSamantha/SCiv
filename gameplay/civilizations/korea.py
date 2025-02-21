from gameplay.civilization import Civilization

from managers.i18n import t_


class Korea(Civilization):
    name = t_("civilization.korea.name")
    description = t_("civilization.korea.description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadable = True
        self.icon = "icons/rome.png"

    def register_effects(self):
        pass

    def register_leaders(self):
        from gameplay.leaders.sejon import Sejon
        from gameplay.leaders.goi import Goi

        self.add_leader(Sejon())
        self.add_leader(Goi())
