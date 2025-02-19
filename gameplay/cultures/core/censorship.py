from __future__ import annotations
from gameplay.culture import Civic
from managers.i18n import _t


class Censorship(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.censorship",
            name=_t("content.culture.civics.core.censorship.name"),
            description=_t("content.culture.civics.core.censorship.description"),
            *args,
            **kwargs,
        )
