from __future__ import annotations
from gameplay.culture import Civic
from managers.i18n import _t


class SeparationOfPowers(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.separation_of_powers",
            name=_t("content.culture.civics.core.separation_of_powers.name"),
            description=_t("content.culture.civics.core.separation_of_powers.description"),
            *args,
            **kwargs,
        )
