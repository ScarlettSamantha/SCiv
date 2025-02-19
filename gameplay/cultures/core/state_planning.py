from __future__ import annotations
from gameplay.culture import Civic
from managers.i18n import _t


class StatePlanning(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.state_planning",
            name=_t("content.culture.civics.core.state_planning.name"),
            description=_t("content.culture.civics.core.state_planning.description"),
            *args,
            **kwargs,
        )
