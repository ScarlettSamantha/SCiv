from gameplay.culture import Civic
from managers.i18n import _t


class NationalSovereignty(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.national_sovereignty",
            name=_t("content.culture.civics.core.national_sovereignty.name"),
            description=_t("content.culture.civics.core.national_sovereignty.description"),
            *args,
            **kwargs,
        )
