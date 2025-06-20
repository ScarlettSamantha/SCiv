from gameplay.greats.core.scientists._base import CoreBaseGreatScientist
from managers.i18n import t_


class Tesla(CoreBaseGreatScientist):
    def __init__(self):
        super().__init__(
            key="core.scientists.tesla",
            name=t_("content.greats.core.people.tesla.name"),
            description=t_("content.greats.core.people.tesla.description"),
            cost=100,
        )
