from gameplay.culture import Civic
from managers.i18n import _t


class ReligiousUnity(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.religious_unity",
            name=_t("content.culture.civics.core.religious_unity.name"),
            description=_t("content.culture.civics.core.religious_unity.description"),
            *args,
            **kwargs,
        )
