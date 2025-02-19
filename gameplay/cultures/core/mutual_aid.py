from __future__ import annotations
from gameplay.culture import Civic
from managers.i18n import _t


class MutualAid(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.mutual_aid",
            name=_t("content.culture.civics.core.mutual_aid.name"),
            description=_t("content.culture.civics.core.mutual_aid.description"),
            *args,
            **kwargs,
        )
