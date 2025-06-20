from gameplay.greats.core.scientists._base import CoreBaseGreatScientist
from managers.i18n import t_


class Einstein(CoreBaseGreatScientist):
    def __init__(self):
        super().__init__(
            key="core.scientists.einstein",
            name=t_("content.greats.core.people.einstein.name"),
            description=t_("content.greats.core.people.einstein.description"),
            cost=100,
        )
