from __future__ import annotations
from gameplay.greats.core.scientists._base import CoreBaseGreatScientist
from managers.i18n import _t


class Einstein(CoreBaseGreatScientist):
    def __init__(self):
        super().__init__(
            key="core.scientists.einstein",
            name=_t("content.greats.core.people.einstein.name"),
            description=_t("content.greats.core.people.einstein.description"),
            cost=100,
        )
