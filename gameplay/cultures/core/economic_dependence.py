from __future__ import annotations
from gameplay.culture import Civic
from managers.i18n import _t


class EconomicDependence(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.economic_dependence",
            name=_t("content.culture.civics.core.economic_dependence.name"),
            description=_t("content.culture.civics.core.economic_dependence.description"),
            *args,
            **kwargs,
        )
