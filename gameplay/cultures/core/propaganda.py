from __future__ import annotations
from gameplay.culture import Civic
from managers.i18n import _t


class Propaganda(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.propaganda",
            name=_t("content.culture.civics.core.propaganda.name"),
            description=_t("content.culture.civics.core.propaganda.description"),
            *args,
            **kwargs,
        )
