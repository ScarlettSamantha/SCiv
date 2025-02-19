from __future__ import annotations
from gameplay.culture import Civic
from managers.i18n import _t


class SharedSovereignty(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.shared_sovereignty",
            name=_t("content.culture.civics.core.shared_sovereignty.name"),
            description=_t("content.culture.civics.core.shared_sovereignty.description"),
            *args,
            **kwargs,
        )
