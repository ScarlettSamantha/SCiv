from gameplay.culture import Civic
from managers.i18n import _t


class ReligiousLaw(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.religious_law",
            name=_t("content.culture.civics.core.religious_law.name"),
            description=_t("content.culture.civics.core.religious_law.description"),
            *args,
            **kwargs,
        )
