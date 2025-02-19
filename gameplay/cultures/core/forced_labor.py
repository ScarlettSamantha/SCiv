from __future__ import annotations
from gameplay.culture import Civic
from managers.i18n import _t


class ForcedLabor(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.forced_labor",
            name=_t("content.culture.civics.core.forced_labor.name"),
            description=_t("content.culture.civics.core.forced_labor.description"),
            *args,
            **kwargs,
        )
