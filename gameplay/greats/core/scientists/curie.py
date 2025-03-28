from gameplay.greats.core.scientists._base import CoreBaseGreatScientist
from managers.i18n import _t


class Curie(CoreBaseGreatScientist):
    def __init__(self):
        super().__init__(
            key="core.scientists.curie",
            name=_t("content.greats.core.people.curie.name"),
            description=_t("content.greats.core.people.curie.description"),
            cost=100,
        )
