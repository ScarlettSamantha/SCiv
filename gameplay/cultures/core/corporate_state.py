from __future__ import annotations
from gameplay.culture import Civic
from managers.i18n import _t


class CorporateState(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.corporate_state",
            name=_t("content.culture.civics.core.corporate_state.name"),
            description=_t("content.culture.civics.core.corporate_state.description"),
            *args,
            **kwargs,
        )
