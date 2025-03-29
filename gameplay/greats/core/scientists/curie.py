from gameplay.greats.core.scientists._base import CoreBaseGreatScientist
from managers.i18n import t_


class Curie(CoreBaseGreatScientist):
    def __init__(self):
        super().__init__(
            key="core.scientists.curie",
            name=t_("content.greats.core.people.curie.name"),
            description=t_("content.greats.core.people.curie.description"),
            cost=100,
        )
