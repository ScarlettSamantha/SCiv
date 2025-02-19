from __future__ import annotations
from gameplay.culture import Civic
from managers.i18n import _t


class CulturalPreservation(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.cultural_preservation",
            name=_t("content.culture.civics.core.cultural_preservation.name"),
            description=_t("content.culture.civics.core.cultural_preservation.description"),
            *args,
            **kwargs,
        )
