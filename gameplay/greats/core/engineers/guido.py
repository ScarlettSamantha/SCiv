from gameplay.greats.core.engineers._base import CoreBaseGreatEngineer
from managers.i18n import t_


class Guido(CoreBaseGreatEngineer):
    def __init__(self):
        super().__init__(
            key="core.engineers.guido",
            name=t_("content.greats.core.people.guido_van_rossem.name"),
            description=t_("content.greats.core.people.guido_van_rossem.description"),
            cost=100,
        )
