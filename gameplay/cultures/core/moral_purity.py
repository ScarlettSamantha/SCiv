from __future__ import annotations
from gameplay.culture import Civic
from managers.i18n import _t


class MoralPurity(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.moral_purity",
            name=_t("content.culture.civics.core.moral_purity.name"),
            description=_t("content.culture.civics.core.moral_purity.description"),
            *args,
            **kwargs,
        )
