from gameplay.culture import Civic
from managers.i18n import _t


class NationalUnity(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.national_unity",
            name=_t("content.culture.civics.core.national_unity.name"),
            description=_t("content.culture.civics.core.national_unity.description"),
            *args,
            **kwargs,
        )
