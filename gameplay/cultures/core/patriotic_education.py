from __future__ import annotations
from gameplay.culture import Civic
from managers.i18n import _t


class PatrioticEducation(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.patriotic_education",
            name=_t("content.culture.civics.core.patriotic_education.name"),
            description=_t("content.culture.civics.core.patriotic_education.description"),
            *args,
            **kwargs,
        )
