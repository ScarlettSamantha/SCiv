from gameplay.culture import Civic
from managers.i18n import _t


class NationalPurity(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.national_purity",
            name=_t("content.culture.civics.core.national_purity.name"),
            description=_t("content.culture.civics.core.national_purity.description"),
            *args,
            **kwargs,
        )
