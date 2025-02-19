from __future__ import annotations
from gameplay.greats.core.scientists._base import CoreBaseGreatScientist
from managers.i18n import _t


class Tesla(CoreBaseGreatScientist):
    def __init__(self):
        super().__init__(
            key="core.scientists.tesla",
            name=_t("content.greats.core.people.tesla.name"),
            description=_t("content.greats.core.people.tesla.description"),
            cost=100,
        )
