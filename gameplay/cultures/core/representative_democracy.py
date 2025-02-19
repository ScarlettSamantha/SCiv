from __future__ import annotations
from gameplay.culture import Civic
from managers.i18n import _t


class RepresentativeDemocracy(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.representative_democracy",
            name=_t("content.culture.civics.core.representative_democracy.name"),
            description=_t("content.culture.civics.core.representative_democracy.description"),
            *args,
            **kwargs,
        )
