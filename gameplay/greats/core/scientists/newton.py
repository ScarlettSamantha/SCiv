from gameplay.greats.core.scientists._base import CoreBaseGreatScientist
from managers.i18n import t_


class Newton(CoreBaseGreatScientist):
    def __init__(self):
        super().__init__(
            key="core.scientists.newton",
            name=t_("content.greats.core.people.newton.name"),
            description=t_("content.greats.core.people.newton.description"),
            cost=100,
        )
